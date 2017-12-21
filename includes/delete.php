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

	} else {
		// Mark for deletion so facade-worker.py removes files and data

		$query = "UPDATE repos SET status='Delete'
			WHERE id=" . $repo_id;

		query_db($db,$query,"Marking repo for deletion with ID ". $repo_id);

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

	// Mark the project for deletion.
	$query = "UPDATE projects SET name='(Queued for removal)'
		WHERE id=" . $project_id;

	query_db($db,$query,"Preparing to delete project with ID " . $project_id);

}

?>
