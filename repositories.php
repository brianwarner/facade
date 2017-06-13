<?php

/*
* Copyright 2016-2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

include_once "includes/delete.php";
include_once "includes/display.php";
include_once "includes/db.php";

list($db,$db_people) = setup_db();

if ($_GET["repo"]) {

	$repo_id = sanitize_input($db,$_GET["repo"],11);

	$query = "SELECT git FROM repos WHERE id=" . $repo_id;
	$result = query_db($db,$query,"Get url of repo");

	$name = $result->fetch_assoc();
	$repo_url = $name["git"];

	$title = 'Repo: ' . $repo_url;

	include_once "includes/header.php";
	include_once "includes/warnings.php";

	// Determine if a year was requested.
	$year = 'All';
	$period = 'annual';
	if ($_GET["year"]) {
		$year = sanitize_input($db,$_GET["year"],4);
		$period = 'monthly';
		$period_clause = ' AND year=' . $year;
	}

	// Determine if a specific affiliation was requested.
	$affiliation = 'All';
	if ($_GET["affiliation"]) {
		$affiliation = sanitize_input($db,rawurldecode($_GET["affiliation"]),64);
		$affiliation_clause = " AND affiliation = '" . $affiliation . "'";
	}

	// Determine if a specific email was requested.
	$email = 'All';
	if ($_GET["email"]) {
		$email = sanitize_input($db,rawurldecode($_GET["email"]),64);
		$email_clause = " AND email = '" . $email . "'";
	}

	// Determine if a specific stat was requested.
	$stat = 'added';
	if ($_GET["stat"]) {
		$stat = sanitize_input($db,$_GET["stat"],12);
	}

	// First, verify that there's data to show. If not, suppress the report displays.
	$query = "SELECT NULL FROM repo_" . $period . "_cache " .
		"WHERE repos_id=" . $repo_id .
		$year_clause . $affiliation_clause . $email_clause;

	$result = query_db($db,$query,"Check whether to display.");

	if ($result->num_rows > 0) {

		write_stat_selector_submenu($_SERVER['REQUEST_URI'],$stat);

		// Show all results if details requested. Otherwise limit for readability
		if ($_GET["detail"]) {

			$detail = sanitize_input($db,$_GET["detail"],16);

			echo '<div class="content-block">
			<h2>All contributions</h2>';

			cached_results_as_summary_table($db,'repo',$repo_id,$detail,'All',$year,$affiliation,$email,$stat);

		} else {

			echo '<div class="content-block">
			<h2>Contributor summary</h2>';

			if (($affiliation == 'All') || (($affiliation == 'All') && ($email != 'All'))) {
				echo '<div class="sub-block">';

				cached_results_as_summary_table($db,'repo',$repo_id,'affiliation',5,$year,$affiliation,$email,$stat);

				echo '</div> <!-- .sub-block -->';
			}

			if (($email == 'All') || ($affiliation != 'All')) {

				echo '<div class="sub-block">';

				cached_results_as_summary_table($db,'repo',$repo_id,'email',10,$year,$affiliation,$email,$stat);

				echo '</div> <!-- .sub-block -->';
            }
			echo '</div> <!-- .sub-block -->';

		}

	} else {

		// There is no analysis data cached

		echo '<div class="content-block">
			<h2>No contributor data</h2>
			<p>Facade has not calculated any contribution data for this repo.
			This could be because all commits are outside of the analysis range,
			or because the analysis has not yet completed.</p>
			<p>When data is available, it will appear here.</p>';
	}

} else {

	$title = "Tracked Repositories";
	include_once "includes/header.php";
	include_once "includes/warnings.php";

	echo '<div class="content-block"><h2>All repositories</h2>';

	$query = "SELECT name,id FROM projects ORDER BY name ASC";
	$result = query_db($db,$query,"Select project names.");

	if ($result->num_rows > 0) {

		while ($row = $result->fetch_assoc()) {
			echo '<h3>' . $row["name"] . '</h3>';

			list_repos($db,$row["id"]);

		}
	} else {
		echo '<p>No projects found.</p>';
	}

	echo '</div> <!-- .content-block -->';
}

include_once "includes/footer.php";

$db->close();
$db_people->close();

?>
