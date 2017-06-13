<?php

/*
* Copyright 2016-2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

function delete_repository ($db,$repo_id) {

	// Get the url of the git repo to let the user know what was deleted
	$query = "SELECT git FROM repos
		WHERE id=" . $repo_id;

	$result = query_db($db,$query,"Getting repo");

	$row = $result->fetch_assoc();
	$name = $row["git"];

	// If the repo was initialized, files must be deleted
	$query = "SELECT status FROM repos
		WHERE id=" . $repo_id;

	$result = query_db($db,$query,"Checking repo status");

	$row = $result->fetch_assoc();
	$status = $row["status"];

	if ($status == "New") {
		// Only need to delete the repo
		$query = "DELETE FROM repos
			WHERE id=" . $repo_id;

		query_db($db,$query,"Removing uninitialized repo");

		echo '<div class="info">Repo "' . $name . '" removed.</div>';

	} else {
		// Clear analysis data, mark for deletion so facade-worker.py removes files

		$clean = "DELETE FROM analysis_data WHERE repos_id = $repo_id";

		query_db($db,$clean,'Deleting analysis data for ' . $repo_id);


		$query = "UPDATE repos SET status='Delete'
			WHERE id=" . $repo_id;

		query_db($db,$query,"Marking repo for deletion with ID ". $repo_id);

		echo '<div class="info">Repo "' . $name . '" marked for deletion.</div>';
	}
}

function delete_project ($db,$project_id) {

	$query = "SELECT name FROM projects
		WHERE id=" . $project_id;

	$result = query_db($db,$query,"Getting project name");

	$row = $result->fetch_assoc();
	$name = $row["name"];

	// First remove the repos
	$query = "SELECT id FROM repos
		WHERE projects_id=" . $project_id;

	$result = query_db($db,$query,"Getting repos for project with ID " . $project_id);

	while ($row = $result->fetch_assoc()) {
		delete_repository($db,$row["id"]);
	}

	// Then remove the excludes
	$remove_excludes = "DELETE FROM exclude WHERE projects_id = " . $project_id;

	query_db($db,$remove_excludes,'Removing excludes for project with ID ' .
		$project_id);

	// Remove the project. If delete fails (e.g., php times out), can try again.
	$query = "DELETE FROM projects
		WHERE id=" . $project_id;

	query_db($db,$query,"Deleting project with ID " . $project_id);

	echo '<div class="info">Project "' . $name . '" deleted.</div>';

}


?>
