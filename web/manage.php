<?php

/*
* Copyright 2016-2017 Brian Warner
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*
* SPDX-License-Identifier:	Apache-2.0
*/

include_once "includes/delete.php";
include_once "includes/db.php";

list($db,$db_people) = setup_db();

session_start();

// Protect against unauthorized access
if (!ISSET($_SESSION['access_granted'])) {
	echo '<meta http-equiv="refresh" content="0;user">';
	die;
}


if (ISSET($_POST["confirmnew_repo"])) {

	$title = "Add a git repo";
	include_once "includes/header.php";

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	echo '<div class="content-block"><div class="sub-block"><p>Add a single git
		repository by URL. Authentication is not supported, so use anonymous
		git repo links.</p>
		</div> <!-- .sub-block -->
		<div class="sub-block">
		<form action="manage" id="newrepo" method="post">
		<table>
		<tr class="quarter">
		<td><label for="git">Git repository</label></td>
		<td><span class="text"><input type="text" name="git"></span></td>
		</tr>
		</table>
		<p><input type="hidden" name="project_id" value="' . $project_id .
		'"><input type="submit" name="new_repo" value="Add repo">
		</form>
		</div> <!-- .sub-block -->';

	include_once "includes/footer.php";

} elseif (ISSET($_POST["new_repo"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	// add a new repo and return to the project details pages.
	$git = sanitize_input($db,$_POST["git"],256);

	// Trim any trailing slashes
	$git = rtrim($git,'/');

	// Only do something if valid input was submitted
	if ($git) {
		$query = "INSERT INTO repos (projects_id,git,status) VALUES ('" .
			$project_id . "','" . $git . "','New')";
		query_db($db,$query,"Add new git repo");
	}

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["confirmdelete_repo"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	$title = "Deleting git repo";
	include_once "includes/header.php";

	$repo_id = sanitize_input($db,$_POST["repo_id"],11);

	$query = "SELECT git FROM repos WHERE id=" . $repo_id;
	$result = query_db($db,$query,"Getting git repo URL.");

	$row = $result->fetch_assoc();
	$git = $row["git"];

	echo '<p>You are about to delete all data for "' . $git . '" (including all
		contribution statistics).</p><p><strong>Are you sure?</strong></p>
		<p><form action="manage" id="delete" method="post">
		<input type="submit" name="delete_repo" value="Delete it">
		<input type="hidden" name="project_id" value="' . $project_id . '">
		<input type="hidden" name="repo_id" value="' . $repo_id . '">
		</form></p>';

	include_once "includes/footer.php";

} elseif (ISSET($_POST["delete_repo"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	delete_repository($db,sanitize_input($db,$_POST["repo_id"],11));

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["confirmnew_project"])) {

	$title = "Add a new project";
	include_once "includes/header.php";

	echo '<form action="manage" id="newproject" method="post">
		<p><label>Project name:</label><br>
		<span class="text"><input type="text" name="project_name"></span></p>
		<p><label>Project website:</label><br>
		<span class="text"><input type="text" name="project_website"></span></p>
		<p><label>Project description:</label><br>
		<textarea name="project_description" form="newproject" cols=64 rows=4
		maxlength=256 ></textarea></p>

		<p><input type="submit" name="new_project" value="Add project">
		</form>';

	include_once "includes/footer.php";

} elseif (ISSET($_POST["new_project"])) {

	$project_name = sanitize_input($db,$_POST["project_name"],64);
	$project_website = sanitize_input($db,$_POST["project_website"],64);
	$project_description = sanitize_input($db,$_POST["project_description"],256);

	if ($project_name) {

		$query = "INSERT INTO projects (name,website,description)
		VALUES ('" . $project_name . "','" . $project_website . "',
		'" . $project_description . "')";

		query_db($db,$query,"Insert new project");
	}

	header("Location: projects");

} elseif (ISSET($_POST["confirmedit_project"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	$query = "SELECT name,description,website FROM projects
		WHERE name != '(Queued for removal)'
		AND id=" . $project_id;
	$result = query_db($db,$query,"Getting name, description, and website");

	$project = $result->fetch_assoc();

	$title = "Edit " . $project["name"];
	include_once "includes/header.php";

	echo '<div class="content-block"><h2>Name</h2>
		<form id="editname" action="manage" method="post">
		<p><span class="text"><input type="text" name="project_name" value="' .
		$project["name"] . '"></span></p>
		<input type="hidden" name="id" value="' . $project_id . '">
		<p><input type="submit" name="edit_name" value="edit name"></p>
		</form>
		</div> <!-- .content-block -->

		<div class="content-block"><h2>Description</h2>
		<form id="editdescription" action="manage" method="post">
		<p><textarea name="project_description" form="editdescription" cols=64
		rows=4 maxlength=256>' . $project["description"] . '</textarea></p>
		<input type="hidden" name="id" value="' . $project_id . '">
		<p><input type="submit" name="edit_description"
		value="edit description"></p>
		</form>
		</div> <!-- .content-block> -->

		<div class="content-block"><h2>Website</h2>
		<form id="editwebsite" action="manage" method="post">
		<p><span class="text"><input type="text" name="project_website"
		value="'. $project["website"] . '"></span></p>
		<input type="hidden" name="id" value="' . $project_id . '">
		<p><input type="submit" name="edit_website" value="edit website"></p>
		</form>
		</div> <!-- .content-block -->';

	include_once "includes/footer.php";

} elseif (ISSET($_POST["updateprojectrepos"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	$set_repos_update = "UPDATE repos SET status='Update'
		WHERE projects_id = " . $project_id;
	query_db($db,$set_repos_update,"Forcing repo update");

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["recacheproject"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	$recache_project = "UPDATE projects SET recache = TRUE WHERE id = " . $project_id;
	query_db($db,$recache_project,"Recaching project");

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["edit_name"])) {

	$project_id = sanitize_input($db,$_POST["id"],11);

	// Don't allow an empty name
	if (trim($_POST["project_name"])) {

		$query = "UPDATE projects
			SET name='" . sanitize_input($db,$_POST["project_name"],64) . "'
				WHERE id=" . $project_id;

		query_db($db,$query,"updating name");

	}

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["edit_description"])) {

	$project_id = sanitize_input($db,$_POST["id"],11);

	// An empty description is fine
	$query = "UPDATE projects
		SET description='" . sanitize_input($db,$_POST["project_description"],256) ."'
		WHERE id=" . $project_id;

	query_db($db,$query,"updating description");

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["edit_website"])) {

	$project_id = sanitize_input($db,$_POST["id"],11);

	// An empty website is fine
	$query = "UPDATE projects
		SET website='" . sanitize_input($db,$_POST["project_website"],64) . "'
		WHERE id=" . $project_id;

	query_db($db,$query,"updating website");

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["confirmdelete_project"])) {

	$title = "Deleting project";
	include_once "includes/header.php";

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	$query = "SELECT name FROM projects WHERE name != '(Queued for removal)' AND id=" . $project_id;
	$result = query_db($db,$query,"Getting project name.");

	$row = $result->fetch_assoc();
	$name = $row["name"];

	echo '<p>You are about to delete all data for "' . $name . '" (including
		repositories and all contribution statistics).</p><p><strong>Are you
		sure?</strong></p>
		<p><form action="manage" id="delete" method="post">
		<input type="submit" name="delete_project" value="Delete it">
		<input type="hidden" value="' . $project_id . '" name="project_id">
		</form></p>';


} elseif (ISSET($_POST["delete_project"])) {

	delete_project ($db,sanitize_input($db,$_POST["project_id"],11));

	header("Location: projects");

} elseif (ISSET($_POST["confirmnew_excludedomain"])) {

	$title = "Exclude a domain from analysis and results";
	include_once "includes/header.php";

	$project_id = sanitize_input($db,$_POST["project_id"],11);
	$project_name = sanitize_input($db,$_POST["project_name"],64);

	echo '<form action="manage" id="new_excludedomain" method="post">

		<p><label>Domain<br><span class="text">
		<input type="text" name="domain"></span></label></p>
		<p><input type="hidden" name="project_id" value="' . $project_id . '">
		<input type="submit" name="new_excludedomain"
		value="Exclude this domain from ' . $project_name . '">
		</form>';

	include_once "includes/footer.php";

} elseif (ISSET($_POST["new_excludedomain"])) {

	// add a new domain to the exclude list and return to the project details pages.

	$project_id = sanitize_input($db,$_POST["project_id"],11);
	$domain = sanitize_input($db,$_POST["domain"],64);

	// Only do something if valid input was submitted
	if ($domain) {

		$query = "INSERT INTO exclude (projects_id,domain)
			VALUES ('" . $project_id . "','" . $domain . "')";

		query_db($db,$query,"Add new exclusion domain");

	}

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["delete_excludedomain"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);
	$exclude_id = sanitize_input($db,$_POST["exclude_id"],11);

	$query = "DELETE FROM exclude WHERE id=" . $exclude_id;
	query_db($db,$query,"Remove domain from exclude list");

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["confirmnew_excludeemail"])) {

	$title = "Exclude an email from analysis and results";
	include_once "includes/header.php";

	$project_id = sanitize_input($db,$_POST["project_id"],11);
	$project_name = sanitize_input($db,$_POST["project_name"],64);

	echo '<form action="manage" id="new_excludeemail" method="post">
		<p><label>Email<br><span class="text">
		<input type="text" name="email"></span></label></p>
		<p><input type="hidden" name="project_id" value="' . $project_id . '">
		<input type="submit" name="new_excludeemail"
		value="Exclude this email from ' . $project_name . '">
		</form>';

	include_once "includes/footer.php";

} elseif (ISSET($_POST["new_excludeemail"])) {

	// add a new email to the exclude list and return to the project details pages.

	$project_id = sanitize_input($db,$_POST["project_id"],11);
	$email = sanitize_input($db,$_POST["email"],64);

	// Only do something if valid input was submitted
	if ($email) {

		$query = "INSERT INTO exclude (projects_id,email)
			VALUES ('" . $project_id . "','" . $email . "')";

		query_db($db,$query,"Add new exclusion email");

	}

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["delete_excludeemail"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);
	$exclude_id = sanitize_input($db,$_POST["exclude_id"],11);

	$query = "DELETE FROM exclude WHERE id=" . $exclude_id;
	query_db($db,$query,"Remove email from exclude list");

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["add_tag"])) {

	$tag = sanitize_input($db,$_POST["select_tag"],64);
	$start_date = sanitize_input($db,$_POST["start_date"],10);
	$email = sanitize_input($db,$_POST["email"],64);

	if ($tag == 'custom') {
		$tag = sanitize_input($db,$_POST["new_tag"],64);
	}

	if (sanitize_input($db,$_POST["end_date"],10) == 'custom') {
		$end_date = sanitize_input($db,$_POST["custom_end"],10);
	}

	if ($tag &&
	$start_date &&
	$end_date &&
	$email &&
	$start_date <= $end_date) {

		// Tag that ends on a specific date
		$query = "INSERT INTO special_tags (tag,start_date,end_date,email)
			VALUES ('" . $tag . "','" . $start_date . "','" . $end_date . "',
			'" . $email . "')";

		query_db($db,$query,"inserting custom tag");

	} elseif ($tag &&
	$start_date &&
	$email &&
	!$end_date) {

		// Tag that doesn't end on a specific date
		$query = "INSERT INTO special_tags (tag,start_date,email)
			VALUES ('" . $tag . "','" . $start_date . "','" . $email . "')";

		query_db($db,$query,"inserting custom tag without end date");

	} else {
		echo 'incomplete';
	}

	header("Location: tags");

} elseif (ISSET($_POST["delete_tag"])) {

	$tag_id = sanitize_input($db,$_POST["id"],11);

	if ($tag_id) {
		$query = "DELETE FROM special_tags WHERE id=" . $tag_id;
		query_db($db,$query,"Deleting custom tag.");
	}

	header("Location: tags");

} elseif (ISSET($_POST["confirmimport_cgit"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	$title = 'Import repos from cgit';
	include_once 'includes/header.php';

	echo '<div class="content-block"><div class="sub-block"><p>cgit is a common
		web interface for servers hosting a large number of git repos.  It can
		be more efficient to import them directly from the cgit index page,
		which has the full listing of projects.</p><p>It may take a long time to
		discover all of the repos on a cgit server.  Be patient.</p>
		</div><!-- .sub-block -->
		<div class="sub-block">
		<form action="import" id="import" method="post">
		<input type="hidden" name="project_id" value="' . $project_id . '">
		<input type="hidden" name="input_type" value="cgit">
		<table>
		<tr>
		<td class="quarter"><label>cgit index page: </label></td>
		<td><span class="text">
		<input type="text" name="url"></span></td>
		</tr>
		</table>
		<p><input type="submit" name="submit_cgit" value="Discover repos from cgit"></p>
		</form></div><!-- .sub-block --></div><!-- .content-block -->';

	include_once 'includes/footer.php';

} elseif (ISSET($_POST["confirmimport_gerrit"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	$title = 'Import repos from Gerrit';
	include_once 'includes/header.php';

	echo '<div class="content-block"><div class="sub-block"><p>Gerrit is a
		commonly used tool to manage repositories.  It can take a while to
		navigate large instances manually, since every repo address is on a
		different page.  Facade can attempt to discover all of the repos in a
		Gerrit instance.</p>
		<p>At minimum, you will need the base URL for the Gerrit instance. This
		is everything that appears to the left of the &quot;#&quot; symbol
		when you visit a project page:</p>
		<blockquote>
		<pre><strong>https://gerrit.project.org/...</strong>/#/...</pre>
		</blockquote>

		<p>If the Gerrit instance uses a different base URL for	anonymous
		cloning, you can set that as well.  This can be checked on any
		project page, under the General tab.  You should copy
		everything to the left of the Project name:
		<blockquote>
		<h3>Project project/name</h3>
		<pre><strong>https://anongit.project.org/.../</strong>project/name</pre>
		</blockquote>
		<p>If the anonymous git URL is not set, repos will be cloned with
		the same base URL as the Gerrit instance. This should work fine in
		most cases.  If your repos can\'t be cloned though, you probably
		needed to set this and should just import them again.</p>
		</div><!-- .sub-block -->
		<div class="sub-block">
		<form action="import" id="import" method="post">
		<input type="hidden" name="project_id" value="' . $project_id . '">
		<input type="hidden" name="input_type" value="gerrit">
		<table>
		<tr>
		<td class="quarter">
		<label>Gerrit URL:</td>
		<td><span class="text">
		<input type="text" name="url"></span></td>
		</tr>

		<tr>
		<td><label>Anonymous git repo base URL: (optional) </label></td>
		<td><span class="text">
		<input type="text" name="anongit"></span></td>
		</tr>
		</table>

		<p><input type="submit" name="submit_gerrit"
		value="Discover repos from Gerrit"></p>
		</form></div><!-- .sub-block --></div><!-- .content-block -->';

	include_once 'includes/footer.php';

} elseif (ISSET($_POST["confirmimport_github"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	$title = 'Import repos from github';
	include_once 'includes/header.php';

	echo '<div class="content-block"><div class="sub-block">
		<p>Repos on GitHub are organized by user, and sometimes by organization.
		You can import repos directly from GitHub if you know either of
		these.</p>
		<p>To find the user or organization, navigate to one of the repos you
		want to import and copy the bold text:
		<blockquote>
		<pre>https://github.com/<strong>use_this</strong>/reponame</pre>
		</blockquote></p>
		</div><!-- .sub-block -->
		<div class="sub-block">
		<form action="import" id="import" method="post">
		<input type="hidden" name="project_id" value="' . $project_id . '">
		<input type="hidden" name="input_type" value="github">
		<table>
		<tr>
		<td class="quarter">
		<label><input type="radio" name="github" value="organization"
		class="select" checked="checked">Github organization: </label></td>
		<td><span class="text">
		<input type="text" name="github_org"></span></td>
		</tr>

		<tr>
		<td><label><input type="radio" name="github" value="user"
		class="select">Github user: </label></td>
		<td><span class="text"><input type="text" name="github_user"></span></td>
		</tr>
		</table>

		<p><input type="submit" name="submit_import"
		value="Discover repos from GitHub"></p>
		</form></div><!-- .sub-block --></div><!-- .content-block -->';

	include_once 'includes/footer.php';

} elseif (ISSET($_POST["import_repos"])) {

	$project_id = sanitize_input($db,$_POST["project_id"],11);

	// The names of the repos just help us cycle through the POST variable
	foreach ($_POST["repos"] as $repo) {

		$git = sanitize_input($db,$_POST["radio_" . str_replace('.','_',$repo)],256);

		// Only do something if valid input was submitted
		if ($git) {

			$query = "INSERT INTO repos (projects_id,git,status)
				VALUES ('" . $project_id . "','" . $git . "','New')";

			query_db($db,$query,"Add new git repo");

		}
	}

	header("Location: projects?id=" . $project_id);

} elseif (ISSET($_POST["confirmnew_alias"])) {

	$title = "Add an alias";
	include_once "includes/header.php";

	$project_id = sanitize_input($db,$_POST["project_id"],11);
	$email = sanitize_input($db,$_POST["domain"],128);

	echo '<div class="content-block"><div class="sub-block"><p>Alias mapping
		help ensure that developers with multiple email addresses get full
		credit for their work.</p>
		</div> <!-- .sub-block -->
		<div class="sub-block">
		<form action="manage" id="newalias" method="post">
		<table>
		<tr>
		<td class="quarter"><label for="alias">This email: </label></td>
		<td class="quarter"><span class="text"><input type="text" name="alias"
		value="' . $email . '"></span></td>
		<td class="half">&nbsp;</td>
		</tr>
		<tr>
		<td class="quarter"><label for="canonical">Is an alias for: </label></td>
		<td class="quarter"><span class="text"><input type="text" name="canonical"></span></td>
		<td class="half">&nbsp;</td>
		</tr>
		</table>
		<input type="submit" name="new_alias" value="Add alias">
		</form>
		</div> <!-- .sub-block -->';

	include_once "includes/footer.php";

} elseif (ISSET($_POST["new_alias"])) {

	$alias = sanitize_input($db,$_POST['alias'],64);
	$canonical = sanitize_input($db,$_POST['canonical'],64);

	if ($alias && $canonical) {

		// Add an alias

		$add_alias = "INSERT INTO aliases (alias,canonical)
			VALUES ('" . $alias . "','" . $canonical . "')
			ON DUPLICATE KEY UPDATE active = TRUE";

		query_db($db_people,$add_alias,'Adding alias');

	}

	header("Location: people");

} elseif (ISSET($_POST["delete_alias"])) {

	$id = sanitize_input($db,$_POST['id'],11);

	if ($id) {

		// Set alias to inactive so it will be fixed next time facade-worker.py runs

		$set_inactive = "UPDATE aliases SET active = FALSE WHERE id=" . $id;

		query_db($db_people,$set_inactive,'Disabling alias');

	}

	header("Location: people");

} elseif (ISSET($_POST["confirmnew_affiliation"])) {

	$title = "Add an affiliation";
	include_once "includes/header.php";

	$project_id = sanitize_input($db,$_POST["project_id"],11);
	$domain = sanitize_input($db,$_POST["domain"],128);

	echo '<div class="content-block"><div class="sub-block"><p>Affiliation
		mappings help trace work back to specific companies, based upon the
		domain name their employees use or by specific email addresses.</p>
		<p>The start date field allows you to indicate that after a certain
		date, the affiliation should be changed. This should be used when a
		developer uses a personal email and then changes companies, or when a
		company is acquired and the domain is now associated with a new
		parent.</p>

		</div> <!-- .sub-block -->
		<div class="sub-block">
		<form action="manage" id="newaffiliation" method="post">
		<table>
		<tr>
		<td class="quarter"><label for="domain">This email or domain: </label></td>
		<td class="quarter"><span class="text"><input type="text" name="domain"
		value="'. $domain . '"></span></td>
		<td class="half">&nbsp;</td>
		</tr>
		<tr>
		<td class="quarter"><label for="affiliation">Is associated with this
		organization: </label></td>
		<td class="quarter"><span class="text"><input type="text"
		name="affiliation"></span></td>
		<td class="half">&nbsp;</td>
		</tr>
		<tr>
		<td class="quarter">But only after this date (optional):</td>
		<td class="quarter"><span class="text"><input type="text"
		name="start_date"></span></td>
		<td>&nbsp;</td>
		</tr>
		</table>
		</div> <!-- .sub-block -->
		<div class="sub-block">
		<input type="submit" name="new_affiliation" value="Add affiliation">
		</form>
		</div> <!-- .sub-block -->';

	include_once "includes/footer.php";

} elseif (ISSET($_POST["new_affiliation"])) {

	$domain = sanitize_input($db,$_POST['domain'],64);
	$affiliation = sanitize_input($db,$_POST['affiliation'],64);
	$start_date = sanitize_input($db,$_POST['start_date'],10);

	if ($domain && $affiliation) {

		// Add an affiliation

		if ($start_date) {
			$add_affiliation = "INSERT INTO affiliations
				(domain,affiliation,start_date) VALUES ('"
				. $domain . "','" . $affiliation . "','" . $start_date . "')
				ON DUPLICATE KEY UPDATE active = TRUE";

		} else {
			$add_affiliation = "INSERT INTO affiliations
				(domain,affiliation) VALUES ('"
				. $domain . "','" . $affiliation . "')
				ON DUPLICATE KEY UPDATE active = TRUE";
		}

		query_db($db_people,$add_affiliation,'Adding affiliation');

	}

	header("Location: people");

} elseif (ISSET($_POST["delete_affiliation"])) {

	$id = sanitize_input($db,$_POST['id'],11);

	if ($id) {

		// Set affiliation to inactive so it will be fixed next time facade-worker.py runs

		$set_inactive = "UPDATE affiliations SET active = FALSE WHERE id=" . $id;

		query_db($db_people,$set_inactive,'Disabling affiliation');
	}

	header("Location: people");

} elseif (ISSET($_POST["export_projects_csv"])) {

	$fetch_projects = "SELECT id,name,description,website FROM projects WHERE
		name != '(Queued for removal)'";

	$projects = query_db($db,$fetch_projects,'fetching projects');

	header('Content-Type: text/csv; charset=UTF-8');
	header('Content-Disposition: attachment; filename="facade_projects.csv";');

	$f = fopen('php://output', 'w');

	fprintf($f, chr(0xEF) . chr(0xBB) . chr(0xBF));

	fputcsv($f, ['Project ID','Name','Description','Website'],',');

	while ($project = $projects->fetch_assoc()) {
		fputcsv($f,$project,',');
	}

} elseif (ISSET($_POST["import_projects_csv"])) {

	if ($_FILES['import_file']['error'] == 0) {

		$safe = False;

		$import = array_map('str_getcsv',file($_FILES['import_file']['tmp_name']));

		foreach ($import as $line) {

			if (!$safe) {

				// Need to use strpos in case file has utf-8 BOM (optional)

				if (strpos($line[0],'Project ID') &&
					$line[1] == 'Name' &&
					$line[2] == 'Description' &&
					$line[3] == 'Website') {

					$safe = True;

					// Clear projects data when we know it's safe to import
					$drop_projects = "DELETE FROM projects";

					query_db($db,$drop_projects,'Dropping project data');

				}
			} else {

				$insert = "INSERT IGNORE INTO projects
					(id,name,description,website) VALUES ('" .
					$line[0] . "','" . $line[1] . "','" . $line['2'] . "','" .
					$line['3'] . "')";

				query_db($db,$insert,'Importing project');

			}
		}
	}

	header("Location: projects");

} elseif (ISSET($_POST["export_repos_csv"])) {

	$fetch_repos = "SELECT id,projects_id,git,path,name,status FROM repos";

	$repos = query_db($db,$fetch_repos,'fetching repos');

	header('Content-Type: text/csv; charset=UTF-8');
	header('Content-Disposition: attachment; filename="facade_repos.csv";');

	$f = fopen('php://output', 'w');

	fprintf($f, chr(0xEF) . chr(0xBB) . chr(0xBF));

	fputcsv($f, ['Repo ID','Projects ID','Git','Path','Name','Status'],',');

	while ($repo = $repos->fetch_assoc()) {
		fputcsv($f,$repo,',');
	}

} elseif (ISSET($_POST["import_repos_csv"]) ||
	ISSET($_POST["import_clone_repos_csv"])) {

	if ($_FILES['import_file']['error'] == 0) {

		$safe = False;

		$import = array_map('str_getcsv',file($_FILES['import_file']['tmp_name']));

		foreach ($import as $line) {

			if (!$safe) {

				// Need to use strpos in case file has utf-8 BOM (optional)

				if (strpos($line[0],'Repo ID') &&
					$line[1] == 'Projects ID' &&
					$line[2] == 'Git' &&
					$line[3] == 'Path' &&
					$line[4] == 'Name' &&
					$line[5] == 'Status') {

					$safe = True;

					// Clear repos data when we know it's safe to import
					$drop_repos = "DELETE FROM repos";

					query_db($db,$drop_repos,'Dropping repo data');

				}
			} else {

				if ($_POST["import_clone_repos_csv"]) {

					$clear = "DELETE FROM repos_fetch_log";

					query_db($db,$clear,'Clearing repos fetch log');

					$insert = "INSERT IGNORE INTO repos
						(id,projects_id,git,path,name,status)
						VALUES ('" . $line[0] . "','" . $line[1] . "','" .
						$line[2] . "','" . $line[3] . "','" . $line[4] . "','New')";

				} else {

					$insert = "INSERT IGNORE INTO repos
						(id,projects_id,git,path,name,status)
						VALUES ('" . $line[0] . "','" . $line[1] . "','" .
						$line[2] . "','" . $line[3] . "','" . $line[4] . "','" .
						$line[5] . "')";

				}

				query_db($db,$insert,'Importing project');

			}
		}
	}

	header("Location: repositories");

} elseif (ISSET($_POST["export_aliases_csv"])) {

	// Only export active aliases. When imported, they'll be active by default.

	$fetch_aliases = "SELECT canonical,alias FROM aliases WHERE active = TRUE";

	$aliases = query_db($db_people,$fetch_aliases,'fetching aliases');

	header('Content-Type: text/csv; charset=UTF-8');
	header('Content-Disposition: attachment; filename="facade_aliases.csv";');

	$f = fopen('php://output', 'w');

	fprintf($f, chr(0xEF) . chr(0xBB) . chr(0xBF));

	fputcsv($f, ['Canonical email','Alias'],',');

	while ($alias = $aliases->fetch_assoc()) {
		fputcsv($f,$alias,',');
	}

} elseif (ISSET($_POST["import_aliases_csv"])) {

	if ($_FILES['import_file']['error'] == 0) {

		$safe = False;

		$import = array_map('str_getcsv',file($_FILES['import_file']['tmp_name']));

		foreach ($import as $line) {

			if (!$safe) {

				// Need to use strpos in case file has utf-8 BOM (optional)

				if (strpos($line[0],'Canonical email') &&
					$line[1] == 'Alias') {

					$safe = True;
				}
			} else {

				$insert = "INSERT INTO aliases
					(canonical,alias) VALUES ('" .
					$line[0] . "','" . $line[1] . "')
					ON DUPLICATE KEY UPDATE active = TRUE";

				query_db($db_people,$insert,'Importing alias');

			}
		}
	}

	header("Location: people");

} elseif (ISSET($_POST["export_affiliations_csv"])) {

	// Only export active affiliations. When imported, they'll be active by default.

	$fetch_affiliations = "SELECT domain,affiliation,start_date FROM
		affiliations WHERE active = TRUE";

	$affiliations = query_db($db_people,$fetch_affiliations,'fetching affiliations');

	header('Content-Type: text/csv; charset=UTF-8');
	header('Content-Disposition: attachment; filename="facade_affiliations.csv";');

	$f = fopen('php://output', 'w');

	fprintf($f, chr(0xEF) . chr(0xBB) . chr(0xBF));

	fputcsv($f, ['Domain','Affiliation','Beginning on'],',');

	while ($affiliation = $affiliations->fetch_assoc()) {
		fputcsv($f,$affiliation,',');
	}

} elseif (ISSET($_POST["import_affiliations_csv"])) {

	if ($_FILES['import_file']['error'] == 0) {

		$safe = False;

		$import = array_map('str_getcsv',file($_FILES['import_file']['tmp_name']));

		foreach ($import as $line) {

			if (!$safe) {

				// Need to use strpos in case file has utf-8 BOM (optional)

				if (strpos($line[0],'Domain') &&
					$line[1] == 'Affiliation' &&
					$line[2] == 'Beginning on') {

					$safe = True;
				}
			} else {

				if ($line[2]) {

				$insert = "INSERT INTO affiliations
					(domain,affiliation,start_date) VALUES ('" .
					$line[0] . "','" . $line[1] . "','" . $line[2] . "')
					ON DUPLICATE KEY UPDATE active = TRUE";

				} else {

				$insert = "INSERT INTO affiliations
					(domain,affiliation) VALUES ('" .
					$line[0] . "','" . $line[1] . "')
					ON DUPLICATE KEY UPDATE active = TRUE";

				}

				query_db($db_people,$insert,'Importing affiliation');

			}
		}
	}

	header("Location: people");

} elseif (ISSET($_POST["export_tags_csv"])) {

	$fetch_tags = "SELECT email,start_date,end_date,tag FROM special_tags";

	$tags = query_db($db,$fetch_tags,'fetching tags');

	header('Content-Type: text/csv; charset=UTF-8');
	header('Content-Disposition: attachment; filename="facade_tags.csv";');

	$f = fopen('php://output', 'w');

	fprintf($f, chr(0xEF) . chr(0xBB) . chr(0xBF));

	fputcsv($f, ['Email','Beginning on','Ending on','Tag'],',');

	while ($tag = $tags->fetch_assoc()) {
		fputcsv($f,$tag,',');
	}

} elseif (ISSET($_POST["import_tags_csv"])) {

	if ($_FILES['import_file']['error'] == 0) {

		$safe = False;

		$import = array_map('str_getcsv',file($_FILES['import_file']['tmp_name']));

		foreach ($import as $line) {

			if (!$safe) {
				if (strpos($line[0],'Email') &&
					$line[1] == 'Beginning on' &&
					$line[2] == 'Ending on' &&
					$line[3] == 'Tag') {

					$safe = True;
				}
			} else {

				// Handle tags without an end date

				if (!$line[2]) {
					$insert = "INSERT IGNORE INTO special_tags
						(email,start_date,tag) VALUES ('" .
						$line[0] . "','" . $line[1]  . "','" . $line[3] . "')";
				} else {
					$insert = "INSERT IGNORE INTO special_tags
						(email,start_date,end_date,tag) VALUES ('" .
						$line[0] . "','" . $line[1]  . "','" . $line[2] . "','" .
						$line[3] . "')";
				}

				query_db($db,$insert,'Importing tag');

			}
		}
	}

	header("Location: tags");

} elseif (ISSET($_POST["export_settings_csv"])) {

	$fetch_settings = "SELECT setting,value FROM settings ORDER BY id ASC";

	$settings = query_db($db,$fetch_settings,'fetching settings');

	header('Content-Type: text/csv; charset=UTF-8');
	header('Content-Disposition: attachment; filename="facade_settings.csv";');

	$f = fopen('php://output', 'w');

	fprintf($f, chr(0xEF) . chr(0xBB) . chr(0xBF));

	fputcsv($f, ['Setting','Value'],',');

	while ($setting = $settings->fetch_assoc()) {
		fputcsv($f,$setting,',');
	}

} elseif (ISSET($_POST["import_settings_csv"])) {

	if ($_FILES['import_file']['error'] == 0) {

		$safe = False;

		$import = array_map('str_getcsv',file($_FILES['import_file']['tmp_name']));

		foreach ($import as $line) {

			if (!$safe) {

				// Need to use strpos in case file has utf-8 BOM (optional)

				if (strpos($line[0],'Setting') &&
					$line[1] == 'Value') {

					$safe = True;

					// Clear repos data when we know it's safe to import
					$drop_settings = "DELETE FROM settings";

					query_db($db,$drop_settings,'Dropping settings data');

				}
			} else {

				$insert = "INSERT INTO settings
					(setting,value) VALUES ('" .
					$line[0] . "','" . $line[1] . "')";

				query_db($db,$insert,'Importing settings');

				// Add a 10 ms delay to ensure sequential settings have distinguishable
				// timestamps.

				usleep(10000);
			}
		}
	}

	header("Location: configure");

} else {
	echo "Oops, what did you want to do?\n";
}

$db->close();
$db_people->close();

?>
