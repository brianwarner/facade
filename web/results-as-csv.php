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

include_once "includes/db.php";

list($db,$db_people) = setup_db();

$project = array();
$tags = array();
$affiliations = array();

$report_attribution = get_setting($db,'report_attribution');
$report_date = get_setting($db,'report_date');

if ($report_attribution == 'author') {
	$tag_author = 'Author Email';
} else {
	$tag_author = 'Committer Email';
}

if ($report_date == 'author') {
	$tag_date = 'Author Date';
} else {
	$tag_date = 'Committer Date';
}

// Handle custom dates
if ($_GET["start"] == 'custom') {
	$start_date = sanitize_input($db,$_GET["start_date"],10);
	$date_clause = $date_clause . " AND committer_date >= '" . $start_date . "'";
} else {
	$date_clause = '';
}

// If dates are actually out of order, reset the clause and return everything
if ($start_date > date("Y-m-d",time())) {
	$date_clause = '';
}

// Normalize a request for specific repos, or fall back to all repos
if (isset($_GET["projects"])) {
	foreach ($_GET["projects"] as $project) {
		$projects[] = sanitize_input($db,$project,11);
	}
} else {
	$query = "SELECT id FROM projects WHERE name != '(Queued for removal)'";
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

	$affiliations_clause = " AND (" . $report_attribution . "_affiliation='" .
		join("' OR " . $report_attribution . "_affiliation='",$affiliations) . "') ";
} else {
	$affiliations_clause = '';
}

// Get ready for export
$header=TRUE;
header('Content-Type: text/csv; charset=UTF-8');
header('Content-Disposition: attachment; filename="facade_results.csv";');

$f = fopen('php://output', 'w');

fputs($f, $bom =( chr(0xEF) . chr(0xBB) . chr(0xBF) ));

// Walk through the project IDs
foreach ($projects as $project) {

	// PHP can run out of memory on huge projects, so export the data in chunks

	$min_record = 0;
	$num_records = 50000;
	$more_data = TRUE;

	while ($more_data) {

		$get_results = "SELECT p.name AS 'Project name',
			r.path AS 'Repo Path',
			r.name AS 'Repo Name',
			a.author_date AS 'Author Date',
			a.author_name AS 'Author Name',
			a.author_raw_email AS 'Author Raw Email',
			a.author_email AS 'Author Email',
			a.author_affiliation AS 'Author Affiliation',
			a.committer_date AS 'Committer Date',
			a.committer_name AS 'Committer Name',
			a.committer_raw_email AS 'Committer Raw Email',
			a.committer_email AS 'Committer Email',
			a.committer_affiliation AS 'Committer Affiliation',
			a.added AS 'LoC Added',
			a.removed AS 'LoC Removed',
			a.whitespace AS 'Whitespace changes',
			a.commit AS 'Commit',
			a.filename AS 'Filename'
			FROM projects p
			RIGHT JOIN repos r ON p.id = r.projects_id
			RIGHT JOIN analysis_data a ON r.id = a.repos_id
			LEFT JOIN exclude e ON (a.author_email = e.email
				AND (r.projects_id = e.projects_id
				OR e.projects_id = 0))
			OR (a.author_email LIKE CONCAT('%',e.domain)
				AND (r.projects_id = e.projects_id
				OR e.projects_id = 0))
			WHERE p.name != '(Queued for removal)' AND
			r.projects_id = $project
			AND e.email IS NULL
			AND e.domain IS NULL" .
			$date_clause .
			$affiliations_clause . "
			ORDER BY a.committer_date ASC
			LIMIT " . $min_record . "," . $num_records;

		$result = query_db($db,$get_results,'Fetching project data');

		// Write the project-specific data
		while ($row = $result->fetch_assoc()) {

			// Find any tags that match this row and apply them.
			if (isset($_GET["tags"]) ||
			isset($_GET["with-tags"])) {
				foreach ($tags as $tag) {

					// Find tags that match this row
					$query = "SELECT id,end_date FROM special_tags
						WHERE email = '" . str_replace("'","\'",$row[$tag_author]) . "'
						AND start_date <= '" . $row[$tag_date] . "'
						AND end_date >= '" . $row[$tag_date] . "'
						AND tag='" . $tag . "'";

					$tags_result = query_db($db, $query, 'Getting tags');

					// Add matched tag to output, or a blank to preserve ordering.
					// Escape single quotes in tags.
					if ($tags_result->num_rows) {
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

		$min_record += $num_records;

		if ($result->num_rows < $num_records) {
			$more_data = FALSE;
		}
	}
}

$db->close();
$db_people->close();

?>
