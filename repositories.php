<?php

/*
Copyright 2016 Brian Warner

This file is part of Facade, and is made available under the terms of the GNU General Public License version 2.
*/

include_once "includes/delete.php";
include_once "includes/display.php";
include_once "includes/db.php";
$db = setup_db();


if ($_GET["repo"]) {

	$repo_id = sanitize_input($db,$_GET["repo"],11);

	$query = "SELECT git FROM repos WHERE id=" . $repo_id;
	$result = query_db($db,$query,"Get url of repo");

	$name = $result->fetch_assoc();
	$repo_url = $name["git"];

	$title = 'Repo: ' . $repo_url;

	include_once "includes/header.php";

	// First, verify that there's data to show. If not, suppress the report displays.

	$query = "SELECT NULL FROM repos r RIGHT JOIN gitdm_master m ON r.id = m.repos_id WHERE m.status = 'Complete' AND r.id=" . $repo_id;
	$result = query_db($db,$query,"Figure out if there's anything to display.");

	if ($result->num_rows > 0) {

		// If a detailed listing was requested, show all the results. Otherwise limit for readibility.
		if ($_GET["detail"]) {

			$detail = sanitize_input($db,$_GET["detail"],16);

			echo '<div class="content-block">
			<h2>All contributions</h2>';

			gitdm_results_as_summary_table ($db,'repo',$repo_id,$detail,'All');

		} else {

			echo '<div class="content-block">
			<h2>Contributor summary</h2>

			<div class="sub-block">';

			gitdm_results_as_summary_table ($db,'repo',$repo_id,'affiliation',5);

			echo '</div> <!-- .sub-block -->

			<div class="sub-block">';

			gitdm_results_as_summary_table ($db,'repo',$repo_id,'email',10);

			echo '</div> <!-- .sub-block -->

			</div> <!-- .content-block -->';
		}
	}

} else {

	$title = "Tracked Repositories";
	include_once "includes/header.php";

	echo '<div class="content-block"><h2>All repositories</h2>';

	$query = "SELECT name,id FROM projects";
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

close_db($db);

?>
