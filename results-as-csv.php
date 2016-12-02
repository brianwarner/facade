<?php

/*
* Copyright 2016 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

include_once "includes/db.php";
$db = setup_db();

$project = array();
$tags = array();
$affiliations = array();

// Handle custom dates
if ($_GET["start"] == 'custom') {
	$start_date = sanitize_input($db,$_GET["start_date"],10);
	$date_clause = $date_clause . " AND m.start_date >= '" . $start_date . "'";
}

if ($_GET["end"] == 'custom') {
	$end_date = sanitize_input($db,$_GET["end_date"],10);
	$date_clause = $date_clause . " AND m.start_date <= '" . $end_date . "'";
}

// If dates are actually out of order, reset the clause and return everything
if ($_GET["start"] == 'custom' &&
$_GET["end"] == 'custom' &&
$start_date > $end_date) {
	$date_clause = "";
}

// Normalize a request for specific repos, or fall back to all repos
if (isset($_GET["projects"])) {
	foreach ($_GET["projects"] as $project) {
		$projects[] = sanitize_input($db,$project,11);
	}
} else {
	$query = "SELECT id FROM projects";
	$result = query_db($db,$query,'Fetching all projects');
	while ($project = $result->fetch_assoc()) {
		$projects[] = $project['id'];
	}
}

// Figure out which tags we need to attach
if (isset($_GET["tags"])) {
	foreach ($_GET["tags"] as $tag) {
		$tags[] = sanitize_input($db,$tag,64);
	}
}

// If it's all data plus tags, get the tags
if (isset($_GET["with-tags"])) {
	$query = "SELECT DISTINCT tag FROM special_tags";
	$result = query_db($db,$query,'Get all of the tags');
	while ($tag = $result->fetch_assoc()) {
		$tags[] = $tag["tag"];
	}
}

// Figure out which affiliations we need to attach
if (isset($_GET["affiliations"])) {

	foreach ($_GET["affiliations"] as $affiliation) {
		$affiliations[] = sanitize_input($db,$affiliation,64);
	}

	$affiliations_clause = " AND (Affiliation='" .
		join("' OR Affiliation='",$affiliations) . "')";
}

// Get ready for export
$header=TRUE;
header('Content-Type: application/csv');
header('Content-Disposition: attachment; filename="facade_results.csv";');

$f = fopen('php://output', 'w');

// Walk through the project IDs
foreach ($projects as $project) {
	$query = "SELECT p.name AS 'Project name',
		r.path AS 'Repo Path',
		r.name AS 'Repo Name',
		m.start_date AS 'Start Date',
		d.name AS 'Developer Name',
		d.email AS 'Email',
		d.affiliation AS 'Affiliation',
		d.added AS 'LoC Added',
		d.removed AS 'LoC Removed',
		d.changesets AS 'Patches'
		FROM projects p
		RIGHT JOIN repos r ON p.id = r.projects_id
		RIGHT JOIN gitdm_master m ON r.id = m.repos_id
		RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
		LEFT JOIN exclude e ON (d.email = e.email
			AND (r.projects_id = e.projects_id
			OR e.projects_id = 0))
		OR (d.email LIKE CONCAT('%',e.domain)
			AND (r.projects_id = e.projects_id
			OR e.projects_id = 0))
		WHERE r.projects_id = $project
		AND e.email IS NULL
		AND e.domain IS NULL" .
		$date_clause .
		$affiliations_clause;
print $query;
	$result = query_db($db,$query,'Fetching project data');

	// Write the project-specific data
	while ($row = $result->fetch_assoc()) {

		// Find any tags that match this row and apply them.
		if (isset($_GET["tags"]) ||
		isset($_GET["with-tags"])) {
			foreach ($tags as $tag) {

				// Find tags that with a start_date before this row
				$query = "SELECT id,end_date FROM special_tags
					WHERE email = '" . str_replace("'","\'",$row["Email"]) . "'
					AND start_date <= '" . $row["Start Date"] . "'
					AND tag='" . $tag . "'";

				$tags_result = query_db($db, $query, 'Getting tags');

				// Add any tags with an end_date after this row, or no end_date.
				$add_tag = FALSE;
				while ($tags_row = $tags_result->fetch_assoc()) {
					if ($tags_row["end_date"] >= $row["Start Date"] ||
					$tags_row["end_date"] == NULL) {
						$add_tag = TRUE;
					}
				}

				// Add matched tag to output, or a blank to preserve ordering.
				// Escape single quotes in tags.
				if ($add_tag) {
					$row['Tag: ' . str_replace("\'","'",$tag)] = str_replace("\'","'",$tag);
				} else {
					$row['Tag: ' . str_replace("\'","'",$tag)] = '';
				}

			}
		}

		// Write the headers and tag columns if they haven't already been done.
		if ($header) {
			fputcsv($f, array_keys($row), ',');
			$header=FALSE;
		}

		fputcsv($f, $row, ',');
	}
}

close_db($db);
?>
