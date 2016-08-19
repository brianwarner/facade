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
$db = setup_db();


if ($_GET["id"]) {

	// Display a specific project's details.
	$project_id = sanitize_input($db,$_GET["id"],11);

	$query = "SELECT name FROM projects WHERE id=" . $project_id;
	$result = query_db($db,$query,"Get real name of project");

	$name = $result->fetch_assoc();
	$project_name = $name["name"];

	$title = $project_name;

	include_once "includes/header.php";

	$query = "SELECT description,website FROM projects WHERE id=" . $project_id;
	$result = query_db($db,$query,"Getting project description");

	while ($row = $result->fetch_assoc()){

		// If there's a non-empty description, show it
		if (trim($row["description"])) {
			echo '<p>' . $row["description"] . '</p>';
		}

		// If there's a non-empty website, show it
		if (trim($row["website"])) {
			echo '<p><a href="' . $row["website"] . '">' . $row["website"] . '</a></p>';
		}
	}

	// Verify that there's data to show. If not, suppress the report displays.

	$query = "SELECT NULL FROM repos r RIGHT JOIN gitdm_master m ON r.id = m.repos_id WHERE m.status = 'Complete' AND r.projects_id=" . $project_id;
	$result = query_db($db,$query,"Figure out if there's anything to display.");

	if ($result->num_rows > 0) {

		// If a detailed listing was requested, show all the results. Otherwise limit for readibility.
		if ($_GET["detail"]) {

			$detail = sanitize_input($db,$_GET["detail"],16);

			echo '<div class="content-block">
			<h2>All contributions</h2>';

			gitdm_results_as_summary_table ($db,'project',$project_id,$detail,'All');

		} else {

			echo '<div class="content-block">
			<h2>Contributor summary</h2>

			<div class="sub-block">';

			gitdm_results_as_summary_table ($db,'project',$project_id,'affiliation',5);

			echo '</div> <!-- .sub-block -->

			<div class="sub-block">';

			gitdm_results_as_summary_table ($db,'project',$project_id,'email',10);

			echo '</div> <!-- .sub-block -->

			</div> <!-- .content-block -->';
		}

		// Only show unknown contributors if some are unknown

		$query = "SELECT NULL FROM unknown_cache WHERE projects_id=" . $project_id;
		$unknown_result = query_db($db,$query,"Finding if there are any unknown contributors");

		if ($unknown_result->num_rows > 0 ) {

			echo '<div class="content-block">

			<h2>Top unknown contributors</h2>';

			unknown_results_as_table($db,$project_id);

			echo '</div> <!-- .content-block -->';
		}
	}

	echo '<div class="content-block">
	<h2>Current repositories</h2>';

	list_repos($db,$project_id);

	echo '<form action="manage" id="newrepo" method="post">
	<p><input type="hidden" name="project_id" value="' . $project_id . '"><input type="submit" name="confirmnew_repo" value="Add a repo">
	</form>
	<!--<form action="manage" id="cgit" method="post">
	<p><input type="hidden" name="project_id" value="' . $project_id . '"><input type="submit" name="confirmimport_cgit" value="Import from cgit">
	</form></p>-->

	</div> <!-- .content-block -->';

} else {

	// List all of the projects

	$project_id = 0;
	$project_name = "all projects";

	$title = "Tracked Projects";
	include_once "includes/header.php";

	$query = "SELECT * FROM projects";

	$result = query_db($db,$query,"Get projects");

	if ($result->num_rows > 0) {
		echo '<div class="content-block">
		<table>';

		while($row = $result->fetch_assoc()) {
			echo '<tr><td class="linked quarter"><a href="projects?id=' . $row["id"] . '">' . stripslashes($row["name"]) . '</a></td><td>';

			if (stripslashes($row["description"])) {
				echo stripslashes($row["description"]) . "<br><br>";
			}
			if (stripslashes($row["website"])) {
				echo '<a href="' . stripslashes($row["website"]) . '">' . stripslashes($row["website"]) . '</a>';
			}
			echo '</td></tr>';
		}

	echo '</table>';

	} else {
		echo '<div class="content-block"><p>No projects found.</p>';
	}

	echo '<form action="manage" id="newproject" method="post">
<p><input type="submit" name="confirmnew_project" value="Add a new project">
</form></p>
</div> <!-- .content-block -->';

}

echo '<div class="content-block">
<h2>Domains and emails excluded from ' . $project_name .'</h2>';

list_excludes($db,$project_id);

if ($project_id == 0) {
	echo '<h2>All domain and email exclusions</h2>';
	list_excludes($db);
}

echo '</div> <!-- .content-block -->';

if ($_GET["id"]) {
	echo '<div class="content-block">
	<h2>Manage</h2>
	<p><form action="manage" id="editdelproject" method="post"><input type="submit" name="confirmedit_project" value="edit this project\'s name and description"><input type="hidden" name="project_id" value="' . $project_id . '"></p>
	<p><form action="manage" id="editdelproject" method="post"><input type="submit" name="confirmdelete_project" value="delete this project and all its data"><input type="hidden" name="project_id" value="' . $project_id . '"></form></p>

	</div> <!-- .content-block -->';
}

include_once "includes/footer.php";

close_db($db);
?>
