<?php

/*
* Copyright 2016 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

include_once "includes/delete.php";
include_once "includes/db.php";
include_once "includes/display.php";
include_once "includes/scrape.php";
$db = setup_db();

include_once "includes/db.php";
$db = setup_db();

$project_id = sanitize_input($db,$_POST["project_id"],11);
$url = sanitize_input($db,$_POST["cgit"],256);
$github = sanitize_input($db,$_POST["github"],12);
$github_org = sanitize_input($db,$_POST["github_org"],128);
$github_user = sanitize_input($db,$_POST["github_user"],128);

// If a URL is passed, we're importing from cgit. If a github project is passed, we're importing from github.
if (($project_id) && ($url)) {
	$title = "Import from a cgit index";
	include_once "includes/header.php";

	// Trim a trailing slash, if it exists
	if (substr($url,strlen($url)-1,1) == '/') {
		$url = substr($url,0,strlen($url)-1);
	}

	$page = fetch_page($url);

	// Make sure we actually got something back in the scrape
	if ($page) {

		$page_doc = new DOMDocument();
		libxml_use_internal_errors(TRUE);

		$page_doc->loadHTML($page);
		libxml_clear_errors();

		// Verify there is a div called 'cgit', no need to proceed if not.
		if ($page_doc->getElementById('cgit')) {

			$page_xpath = new DOMXPath($page_doc);
			$category = NULL;

			// Get all the table cells with a class (we don't care about the contents of the rest)
			$page_cgit_cells = $page_xpath->query("//div[contains(@id, 'cgit')]//table[contains(@class, 'list')]//td[@class]");

			if ($page_cgit_cells) {
				write_import_table_header();

				foreach ($page_cgit_cells as $page_cgit_cell) {

					// Figure out whether we're in a section header or a repo link cell
					if ($page_cgit_cell->getAttribute('class') == 'reposection') {
						write_import_table_subheader($page_cgit_cell->nodeValue);
					} elseif (strpos($page_cgit_cell->getAttribute('class'),'-repo') > 0) {
						$page_repo_link = $page_cgit_cell->getElementsByTagName('a');
						$repo_name = $page_repo_link[0]->getAttribute('title');
						$repo_link = $page_repo_link[0]->getAttribute('href');

						// If repo URL is relative to server root, trim the path from the page URL and construct link to git detail
						if (substr($repo_link,0,1) == '/') {
							if (strpos($url,'/',strpos($url,'//')+2)) {
							        $repo_url =  substr($url,0,strpos($url,'/',strpos($url,'//')+2)) . $repo_link;
							} else {
								$repo_url = $url . $repo_link;
							}
						} else {
							$repo_url = $url . '/' . $repo_link;
						}

						// Now get the repo's page to figure out the git URLs
						$repo_page = fetch_page($repo_url);

						if ($repo_page) {
							$repo_page_doc = new DOMDocument();
							$repo_page_doc->loadHTML($repo_page);
							libxml_clear_errors();

							// Make sure we're still on a cgit page, complain if not
							if ($repo_page_doc->getElementById('cgit')) {

								$repo_page_xpath = new DOMXPath($repo_page_doc);
								$repo_page_git_links = $repo_page_xpath->query("//a[contains(@rel, 'vcs-git')]");

								// Collect the listed repo URLs
								if ($repo_page_git_links->length > 0) {

									$git_links = array();
									$is_already_used = '';

									foreach ($repo_page_git_links as $repo_page_git_link) {
										$git_link = $repo_page_git_link->getAttribute('href');
										$git_links[] = $git_link;

										// Check to see if repo is already known
										$query = "SELECT NULL FROM repos WHERE projects_id=" . $project_id . " AND git='" . $git_link . "'";
										$result = query_db($db,$query,'Looking for a match with existing repos');

										if ($result->num_rows > 0) {
											$is_already_used = $git_link;
										}
									}

									write_import_table_row($repo_name,$git_links,$is_already_used);
								} else {
									echo "<p>Couldn't find any valid git repo links.</p>";
								}
							}
						} else {
							echo "<p>Something went wrong, could not fetch git repo detail page.</p>";
						}
					}
				}

				write_import_table_footer($project_id);
			} else {
				echo "<p>This cgit appears to be empty.</p>";
			}
		} else {
			echo "<p>This does not appear to be a cgit index page.  You should be using the page that lists all the projects.</p>";
		}
	} else {
		echo "<p>Page not found. Please check your URL.</p>";
	}

	include_once 'includes/footer.php';

} elseif (($project_id) && ((($github == 'organization') && ($github_org)) || (($github == 'user') && ($github_user)))) {

	$title = 'Import from GitHub';
	include_once 'includes/header.php';

	if ($github == 'organization') {
		$github_category = 'orgs';
		$github_entity = $github_org;
	} else {
		$github_category = 'users';
		$github_entity = $github_user;
	}

	$url = 'https://api.github.com/' . $github_category . '/' . $github_entity . '/repos?type=all';

	$github_contents = json_decode(fetch_page($url));

	// Make sure we got something valid
	if ($github_contents) {

		write_import_table_header();

		foreach ($github_contents as $github_content) {
			$is_already_used = '';
			$repos = array($github_content->html_url,$github_content->git_url);

			// Check to see if one of the URLs is already in use in the project
			foreach ($repos as $repo) {
				$query = "SELECT NULL FROM repos WHERE projects_id=" . $project_id . " AND git='" . $repo . "'";
				$result = query_db($db,$query,'Checking for existing repos');

				if ($result->num_rows > 0) {
					$is_already_used = $repo;
				}
			}

			write_import_table_row($github_content->name,$repos,$is_already_used);
		}
		write_import_table_footer($project_id);

	} else {
		echo '<p>' . $github_entity . ' appears to be an invalid GitHub ' . $github . '.</p>';
	}
	include_once 'includes/footer.php';

} else {
	header("Location: projects?id=" . $project_id);
}

?>
