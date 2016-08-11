<?php

/*
* Copyright 2016 Brian Warner
* 
* This file is part of Facade, and is made available under the terms of the GNU General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

function delete_gitdm_data ($db,$repo_id,$name) {

	// Get the ID associated with the gitdm master and data tables
	$query = "SELECT id FROM gitdm_master WHERE repos_id=" . $repo_id;
	$result = query_db($db,$query,"Getting gitdm ID");

	while ($row = $result->fetch_assoc()) {
		$gitdm_master_id = $row["id"];

		// Clear the gitdm data
		$query = "DELETE FROM gitdm_data WHERE gitdm_master_id=" . $gitdm_master_id;
		query_db($db,$query,"Deleting gitdm data for repo " . $name);

		// Remove the master entry
		$query = "DELETE FROM gitdm_master WHERE id=" . $gitdm_master_id;
		query_db($db,$query,"Deleting the master entry for " . $name);
	}

	echo '<div class="info">gitdm data deleted for repo ' . $name . '</div>';

}

function delete_repository ($db,$repo_id) {

	// Get the url of the git repo to let the user know what was deleted
	$query = "SELECT git FROM repos WHERE id=" . $repo_id;
	$result = query_db($db,$query,"Getting repo");

	$row = $result->fetch_assoc();
	$name = $row["git"];

	// Check to see if the repo was initialized, which means files must be deleted
	$query = "SELECT status FROM repos WHERE id=" . $repo_id;
	$result = query_db($db,$query,"Checking repo status");

	$row = $result->fetch_assoc();
	$status = $row["status"];

	if ($status == "New") {
		// Only need to delete the repo
		$query = "DELETE FROM repos WHERE id=" . $repo_id;
		query_db($db,$query,"Removing uninitialized repo");

		echo '<div class="info">Repo "' . $name . '" removed.</div>';

	} else {
		// Need to mark the repo for deletion so the next repo_maintenance.py run removes files, and clear gitdm data
		$query = "UPDATE repos SET status='Delete' WHERE id=" . $repo_id;
		query_db($db,$query,"Marking repo for deletion with ID ". $repo_id);

		echo '<div class="info">Repo "' . $name . '" marked for deletion.</div>';

		delete_gitdm_data($db,$repo_id,$name);
	}
}

function delete_project ($db,$project_id) {

	$query = "SELECT name FROM projects WHERE id=" . $project_id;
	$result = query_db($db,$query,"Getting project name");

	$row = $result->fetch_assoc();
	$name = $row["name"];

	$query = "DELETE FROM projects WHERE id=" . $project_id;
	query_db($db,$query,"Deleting project with ID " . $project_id);

	echo '<div class="info">Project "' . $name . '" deleted.</div>';

	$query = "SELECT id FROM repos WHERE projects_id=" . $project_id;
	$result = query_db($db,$query,"Getting repos for project with ID " . $project_id);

	while ($row = $result->fetch_assoc()) {
		delete_repository($db,$row["id"]);
	}

}


?>
