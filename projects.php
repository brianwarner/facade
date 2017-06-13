<?php

/*
* Copyright 2016-2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

include_once "includes/delete.php";
include_once "includes/db.php";
include_once "includes/display.php";

list($db,$db_people) = setup_db();

$attribution = get_setting($db,'report_attribution');

if ($_GET["id"]) {

	// Display a specific project's details.
	$project_id = sanitize_input($db,$_GET["id"],11);

	$query = "SELECT name FROM projects WHERE id=" . $project_id;
	$result = query_db($db,$query,"Get real name of project");

	$name = $result->fetch_assoc();
	$project_name = $name["name"];

	$title = $project_name;

	include_once "includes/header.php";
	include_once "includes/warnings.php";

	$query = "SELECT description,website FROM projects
		WHERE id=" . $project_id;
	$result = query_db($db,$query,"Getting project description");

	while ($row = $result->fetch_assoc()){

		// If there's a non-empty description, show it
		if (trim($row["description"])) {
			echo '<p>' . $row["description"] . '</p>';
		}

		// If there's a non-empty website, show it
		if (trim($row["website"])) {
			echo '<p><a href="' . $row["website"] . '">' . $row["website"] .
				'</a></p>';
		}
	}

	// Determine if a year was requested.
	$year = 'All';
	$period = 'annual';
	if ($_GET["year"]) {
		$year = sanitize_input($db,$_GET["year"],4);
		$period = 'monthly';
		$period_clause = ' AND year = ' . $year;
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

	// Verify that there's data to show. If not, suppress the report displays.

	$query = "SELECT NULL FROM project_" . $period . "_cache " .
		"WHERE projects_id=" . $project_id .
		$year_clause . $affiliation_clause . $email_clause;

	$result = query_db($db,$query,"Figure out if there's anything to display.");

	if ($result->num_rows > 0) {

		write_stat_selector_submenu($_SERVER['REQUEST_URI'],$stat);

		// Show all if requested, otherwise limit for readability
		if ($_GET["detail"]) {

			$detail = sanitize_input($db,$_GET["detail"],16);

			echo '<div class="content-block">
			<h2>All contributions</h2>';

			cached_results_as_summary_table($db,'project',$project_id,$detail,'All',$year,$affiliation,$email,$stat);

		} else {

			echo '<div class="content-block">
			<h2>Contributor summary</h2>';

			if (($affiliation == 'All') || (($affiliation == 'All') && ($email != 'All'))) {
				echo '<div class="sub-block">';

				cached_results_as_summary_table($db,'project',$project_id,'affiliation',5,$year,$affiliation,$email,$stat);

				echo '</div> <!-- .sub-block -->';
			}

			if (($email == 'All') || ($affiliation != 'All')) {

				echo '<div class="sub-block">';

				cached_results_as_summary_table($db,'project',$project_id,'email',10,$year,$affiliation,$email,$stat);

				echo '</div> <!-- .sub-block -->';
			}
			echo '</div> <!-- .content-block -->';
		}

		// Only show unknown contributors if some are unknown

		$query = "SELECT NULL FROM unknown_cache
			WHERE projects_id=" . $project_id;
		$unknown_result = query_db($db,$query,"Find unknown contributors");

		if ($unknown_result->num_rows > 0 ) {

			echo '<div class="content-block">
				<h2>Top unknown ' . $attribution . 's</h2>';

			unknown_results_as_table($db,$project_id);

			echo '</div> <!-- .content-block -->';
		}
	} else {
		echo '<div class="content-block">
			<h2>No contributor data</h2>
			<p>Facade has not calculated any contribution data for this project.
			This could be because all commits are outside of the analysis range,
			or because the analysis has not yet completed.</p>
			<p>When data is available, it will appear here.</p>';

	}

	if ($year == 'All' && $affiliation == 'All') {

		echo '<div class="content-block">
			<h2>Current repositories</h2>';

		list_repos($db,$project_id);

		if ($_SESSION['access_granted']) {
			echo '<form action="manage" id="newrepo" method="post">
				<p><input type="hidden" name="project_id" value="' . $project_id . '">
				<input type="submit" name="confirmnew_repo" value="Add a single repo">
				</form>
				<form action="manage" id="cgit" method="post">
				<p><input type="hidden" name="project_id" value="' . $project_id . '">
				<input type="submit" name="confirmimport_cgit" value="Import from cgit">
				</form></p>
				<form action="manage" id="gerrit" method="post">
				<p><input type="hidden" name="project_id" value="' . $project_id . '">
				<input type="submit" name="confirmimport_gerrit" value="Import from gerrit">
				</form></p>
				<!--<form action="manage" id="github" method="post">
				<p><input type="hidden" name="project_id" value="' . $project_id . '">
				<input type="submit" name="confirmimport_github" value="Import from GitHub">
				</form></p>-->';

		}
		echo '</div> <!-- .content-block -->';
	}
} else {

	// List all of the projects

	$project_id = 0;
	$project_name = "all projects";

	$title = "Tracked Projects";
	include_once "includes/header.php";

	include_once "includes/warnings.php";

	$query = "SELECT * FROM projects ORDER BY name ASC";

	$result = query_db($db,$query,"Get projects");

	if ($result->num_rows > 0) {
		echo '<div class="content-block">
		<table>';

		while($row = $result->fetch_assoc()) {
			echo '<tr>
				<td class="linked quarter">
				<a href="projects?id=' . $row["id"] . '">' .
				stripslashes($row["name"]) . '</a></td>
				<td>';

			if (stripslashes($row["description"])) {
				echo stripslashes($row["description"]) . "<br><br>";
			}
			if (stripslashes($row["website"])) {
				echo '<a href="' . stripslashes($row["website"]) . '">' .
					stripslashes($row["website"]) . '</a>';
			}
			echo '</td></tr>';
		}

	echo '</table>';

	} else {
		echo '<div class="content-block"><p>No projects found.</p>';
	}

	if ($_SESSION['access_granted']) {
		echo '<form action="manage" id="newproject" method="post">
			<p><input type="submit" name="confirmnew_project"
		value="Add a new project"></form></p>';
	}

	echo '</div> <!-- .content-block -->';

}

echo '<div class="content-block">
<h2>Domains and emails excluded from ' . $project_name .'</h2>';

list_excludes($db,$project_id,$project_name,'domain');
list_excludes($db,$project_id,$project_name,'email');

echo '</div> <!-- .content-block -->';

if ($_GET["id"] && $_SESSION['access_granted']) {
	echo '<div class="content-block">
	<h2>Manage</h2>
	<p><form action="manage" id="editdelproject" method="post">
	<input type="submit" name="confirmedit_project"
	value="edit this project\'s name and description">
	<input type="hidden" name="project_id" value="' . $project_id . '"></p>
	<p><form action="manage" id="editdelproject" method="post">
	<input type="submit" name="confirmdelete_project"
	value="delete this project and all its data">
	<input type="hidden" name="project_id" value="' . $project_id . '"></form></p>

	</div> <!-- .content-block -->';
}

include_once "includes/footer.php";

$db->close();
$db_people->close();

?>
