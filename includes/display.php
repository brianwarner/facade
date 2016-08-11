<?php

/*
* Copyright 2016 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

function gitdm_results_as_summary_table ($db,$scope,$id,$type,$number_results) {

	if ($scope == 'project') {
		$scope_clause = "r.projects_id=" . $id . " AND ";
	} elseif ($scope == 'repo') {
		$scope_clause = "r.id=" . $id . " AND ";
	} else {
		$scope_clause = "";
	}

	if ($number_results != 'All') {
		$results_clause = " LIMIT " . $number_results;
	}

	// Fetch the data
	$query = "SELECT d." . $type . " AS " . $type . ", sum(d.added) AS added, YEAR(m.start_date) AS year
			FROM repos r
			RIGHT JOIN gitdm_master m ON r.id = m.repos_id
			RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
			LEFT JOIN exclude e ON (d.email = e.email AND (r.projects_id = e.projects_id OR e.projects_id = 0))
			OR (d.email LIKE CONCAT('%',e.domain) AND (r.projects_id = e.projects_id OR e.projects_id = 0))
			WHERE " . $scope_clause . "
			e.email IS NULL
			AND e.domain IS NULL
			GROUP BY d." . $type . ", YEAR(m.start_date)";

	$result = query_db($db,$query,"Fetching result data");


	// Stash the data in a way that makes it easy to access later, if we know the entity and year
	while ($data = $result->fetch_assoc()) {
		$summary[$data[$type]][$data["year"]] = $data["added"];
		$summary[$data[$type]]["Total"] += $data["added"];
		$summary["Total"][$data["year"]] += $data["added"];
		$summary["Grand total"] += $data["added"];
	}

	if ($summary) {
		// If there's data for the table, proceed

		echo '<h3>Lines of code added by ';

		if (($number_results != 'All') && ($number_results <= $result->num_rows)) {
			echo 'the top ';
			if ($number_results > 1) {
				echo $number_results . ' ';
			}
		} else {
			echo 'all ';
		}

		echo 'contributor';
		if ($number_results != 1) {
			echo 's';
		}
		echo ', by ' . $type . '</h3>';

		// Get the range of years
		$query = "SELECT YEAR(m.start_date) AS year
				FROM repos r
				RIGHT JOIN gitdm_master m ON r.id = m.repos_id
				RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
				LEFT JOIN exclude e ON (d.email = e.email AND (r.projects_id = e.projects_id OR e.projects_id = 0))
				OR (d.email LIKE CONCAT('%',e.domain) AND (r.projects_id = e.projects_id OR e.projects_id = 0))
				WHERE " . $scope_clause . "
				e.email IS NULL
				AND e.domain IS NULL
				GROUP BY YEAR(m.start_date)
				ORDER BY YEAR(m.start_date) ASC";

		$result_years = query_db($db,$query,"Finding out how many years are in the dataset.");

		// Get the entity names, ordered in descending order of LoC added. This will define the order of the data when building the results table.
		$query = "SELECT d." . $type . " AS " . $type . "
				FROM repos r
				RIGHT JOIN gitdm_master m ON r.id = m.repos_id
				RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
				LEFT JOIN exclude e ON (d.email = e.email AND (r.projects_id = e.projects_id OR e.projects_id = 0))
				OR (d.email LIKE CONCAT('%',e.domain) AND (r.projects_id = e.projects_id OR e.projects_id = 0))
				WHERE " . $scope_clause . "
				e.email IS NULL
				AND e.domain IS NULL
				GROUP BY d." . $type . "
				ORDER BY sum(d.added) DESC" . $results_clause;

		$result_entity = query_db($db,$query,"Finding out which entities are in the dataset.");

		// Create the summary table
		echo '<table><tr><th class="results-entity"></th>';

		while ($year = $result_years->fetch_assoc()) {
			echo '<th class="results-year">' . $year["year"] . '</th>';
		}

		echo '<th class="results-total">Total</th></tr>';

		$result_years->data_seek(0);

		while ($entity = $result_entity->fetch_assoc()) {
			echo '<tr><td class="results-entity">' . $entity[$type] . '</td>';
			while ($year = $result_years->fetch_assoc()) {
				echo '<td class="added">' . number_format($summary[$entity[$type]][$year["year"]]) . '</td>';
			}
			echo '<td class="total">' . number_format($summary[$entity[$type]]["Total"])  .'</td></tr>';
			$result_years->data_seek(0);
		}

		echo '<tr><td class="total">Total from all contributors</td>';

		$result_years->data_seek(0);

		while ($year = $result_years->fetch_assoc()) {
			echo '<td class="total">' . number_format($summary["Total"][$year["year"]]) . '</td>';
		}

		echo '<td class="grand-total">' . number_format($summary["Grand total"]) . '</td></tr></table>';

		if (($number_results != 'All') && ($number_results < $result->num_rows)) {
			if ($scope == 'project') {
				echo '<p><a href="projects?id=' . $id . '&detail=' . $type . '">View all</a></p>';
			} elseif ($scope == 'repo') {
				echo '<p><a href="repositories?repo=' . $id . '&detail=' . $type . '">View all</a></p>';
			}
		}

	} else {
		echo '<p><strong>No data found.</strong></p>';
	}
}

function gitdm_results_as_daily_graph ($db,$project,$repo,$start_date,$end_date,$affiliation,$aggregate = TRUE) {


	$query = "SELECT d.affiliation, sum(d.added), m.start_date FROM gitdm_master m LEFT JOIN gitdm_data d ON m.id = d.gitdm_master_id LEFT JOIN repos r ON m.repos_id = r.id WHERE m.start_date < '2015-03-02' AND r.projects_id = 2 AND r.id = 3 GROUP BY d.affiliation, m.start_date";


}

function unknown_results_as_table ($db,$project_id = NULL) {

	// Displays unknown domains and email, sorted by lines of code added.

	if (isset($project_id)) {
		$project_clause = ' WHERE projects_id=' . $project_id;
	}

	echo '<div class="sub-block">
	<h3>Domains with <i>(Unknown)</i> affiliation</h3>

	<table>
	<tr><th class="quarter">Domain</th><th>Lines of code added</th></tr>';

	$query = "SELECT domain,sum(added) FROM unknown_cache" . $project_clause . " GROUP BY domain ORDER BY sum(added) DESC LIMIT 20";
	$result = query_db($db,$query,"Getting unknown entries");

	while ($row = $result->fetch_assoc()) {
		echo '<tr><td>' . $row["domain"] . '</td><td>' . number_format($row["sum(added)"]) . '</td></tr>';
	}

	echo '</table>

	</div> <!-- .sub-block -->

	<div class="sub-block">
	<h3>Emails with <i>(Unknown)</i> affiliation</h3>

	<table>
	<tr><th class="quarter">Email</th><th>Lines of code added</th></tr>';

	$query = "SELECT email,added FROM unknown_cache" . $project_clause . " ORDER BY added DESC LIMIT 20";
	$result = query_db($db,$query,"Getting unknown entries");

	while ($row = $result->fetch_assoc()) {
		echo '<tr><td>' . $row["email"] . '</td><td>' . number_format($row["added"]) . '</td></tr>';
	}

	echo '</table>
	</div> <!-- .sub-block -->';
}

function list_repos ($db,$project_id) {

	$query = "SELECT * FROM repos WHERE projects_id=" . $project_id;
	$result_repo = query_db($db,$query,"Select repos for project " . $project_id);

	if ($result_repo->num_rows > 0) {
		echo '<table><tr><th class="half">Git repo</th><th class="quarter">Repo Status</th><th class="quarter">gitdm Status</th></tr>';

		while ($row_repo = $result_repo->fetch_assoc()) {

			echo '<tr';

			echo '><td><a href="repositories?repo=' . $row_repo["id"] . '" class="linked">' . $row_repo["git"] . '</a></td><td>';

			$query = "SELECT status FROM repos_fetch_log WHERE repos_id=" . $row_repo["id"] . " ORDER BY id DESC LIMIT 1";
			$result_repo_log = query_db($db,$query,"Select last repo status for " . $row_repo["git"]);

			$row_repo_log = $result_repo_log->fetch_assoc();

			echo '<strong>';

			if ($row_repo_log["status"]) {
				echo $row_repo_log["status"];
			} else {
				echo '<span style="color:green">New</span>';
			}
			echo '</strong>';

			// Determine the last time the git repo was successfully pulled

			$query = "SELECT status,date_attempted FROM repos_fetch_log WHERE repos_id=" . $row_repo["id"] . " AND status='Up-to-date' ORDER BY date_attempted DESC LIMIT 1";
			$result_repo_log = query_db($db,$query,"Select last successful repo status for " . $row_repo["git"]);

			$row_repo_log = $result_repo_log->fetch_assoc();

			if ($row_repo_log["date_attempted"]) {
				$date_attempted = strtotime($row_repo_log["date_attempted"]);
				echo '<br>Last successful pull at<br>' . date("H:i", $date_attempted) . ' on ' . date("M j, Y", $date_attempted);
			}

			// Determine if the repo is marked to be removed during the next facade-worker.py run

			if ($row_repo['status'] == "Delete") {
				echo '<br><span style="color:red">Marked for removal</span>';
			}


			echo '</td><td><span class="button"><form action="manage" id="delrepo" method="post"><input type="submit" name="confirmdelete_repo" value="delete"><input type="hidden" name="project_id" value="' . $project_id . '"><input type="hidden" name="repo_id" value="' . $row_repo["id"]. '"></form></span>';

			// Find any incomplete repos

			$query = "SELECT status FROM gitdm_master WHERE repos_id=" . $row_repo["id"] . " AND status!='Complete' ORDER BY date_attempted ASC";
			$result_gitdm_master = query_db($db,$query,"Get any incomplete gitdm status");
			$row_gitdm_master = $result_gitdm_master->fetch_assoc();

			if ($row_gitdm_master) {
				echo '<span style="color:red"><strong>INCOMPLETE</strong></span>';
			} else {
				// Determine if the repo has complete status
				$query = "SELECT status FROM gitdm_master WHERE repos_id=" . $row_repo["id"] . " AND status='Complete' ORDER BY date_attempted DESC";
				$result_gitdm_master = query_db($db,$query,"Get any incomplete gitdm status");
				$row_gitdm_master = $result_gitdm_master->fetch_assoc();

				if ($row_gitdm_master) {
					echo "<strong>Complete</strong>";
				} else {
					// If the return is empty, there must be no status
					echo '<strong><span style="color:green">New</span></strong>';
				}

			}

			$query = "SELECT start_date FROM gitdm_master WHERE repos_id=" . $row_repo["id"] . " AND status='Complete' ORDER BY start_date DESC LIMIT 1";
			$result_gitdm_master = query_db($db,$query,"Get last complete gitdm status");
			$row_gitdm_master = $result_gitdm_master->fetch_assoc();

			if ($row_gitdm_master['start_date']) {
				$date_attempted = strtotime($row_gitdm_master["start_date"]);
				echo '<br> Current through<br>' . date("F j, Y", $date_attempted);
			}

			echo '</td></tr>';

		}

		echo '</table>';

	} else {
		echo '<p>No repos associated with this project.</p>';
	}
}

function list_excludes($db,$project_id = NULL) {

	/* List all excluded domains and emails given the project_id.
	Project ID of 0 returns global excludes. No project ID returns
	all exclusion rules. */

	// If scope is for a specific project, get that project's name - can I eliminate this?
	if ($project_id > 0) {
		$query = "SELECT name FROM projects WHERE id=" . $project_id;
		$result = query_db($db,$query,"Retrieving name");
		$row = $result->fetch_assoc();
		$project_name = $row["name"];

		$project_clause = ' AND r.projects_id = ' . $project_id;

		// Show all rules that apply on a project detail page
		$project_id_clause = " AND (projects_id=" . $project_id . " OR projects_id=0)";
	} elseif ($project_id === 0) {
		$project_name = "all projects";
		$project_id_clause = " AND projects_id=0";
	}

	echo '<div class="sub-block">';

	$query = "SELECT id,domain,projects_id FROM exclude WHERE domain IS NOT NULL" . $project_id_clause;
	$result = query_db($db,$query,'Getting all excluded domains');

	if ($result->num_rows > 0) {

		echo '<table>
		<tr><th class="quarter">Domains</th><th class="quarter">Lines of code excluded</th><th class="half">Applies to</th></tr>';

		// Get the number of lines of code affected by each exclude
		while ($row = $result->fetch_assoc()) {

			$query = "SELECT sum(d.added) AS added
				FROM gitdm_master m
				RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
				LEFT JOIN repos r ON m.repos_id = r.id
				WHERE d.email LIKE '%" . $row['domain'] . "%'" . $project_clause;

			$result_lines = query_db($db,$query,'Getting excluded lines for project ' . $project_name . ', domain ' . $row['domain']);

			$lines = $result_lines->fetch_assoc();

			echo '<tr><td>' . $row['domain'] . '</td><td>' . number_format($lines['added']) . '</td><td>';

			// If current page is in the scope of the exclusion rule, allow the user to delete it
			if (isset($project_id) && $row['projects_id'] == $project_id) {
				echo '<span class="button"><form action="manage" id="delexcludedomain" method="post"><input type="submit" name="delete_excludedomain" value="delete"><input type="hidden" name="exclude_id" value="' . $row['id'] . '"><input type="hidden" name="project_id" value="' . $project_id . '"></form></span>';
			} 

			// Identify the scope of the exclusion rule
			if ($row['projects_id'] == 0) {
				echo 'All projects</td>';
			} else {
				$query = "SELECT name FROM projects WHERE id=" . $row['projects_id'];
				$result_excluded_from = query_db($db,$query,'Getting project name');
				$excluded_from = $result_excluded_from->fetch_assoc();
				echo $excluded_from['name'] . '</td>';
			}


			echo '</tr>';
		}

		echo '</table>';

	} else {
		echo '<p><strong>No domains excluded.</strong></p>';
	}

	if (isset($project_id)) {
		echo '<p><form action="manage" id="newexcludedomain" method="post"><input type="submit" name="confirmnew_excludedomain" value="Exclude a domain from ' . $project_name . '"><input type="hidden" name="project_name" value="' . $project_name . '"><input type="hidden" name="project_id" value="' . $project_id .'"></form></p>';
	}

	echo '</div> <!-- .sub-block -->

	<div class="sub-block">';

	$query = "SELECT id,email,projects_id FROM exclude WHERE email IS NOT NULL" . $project_id_clause . " ORDER BY projects_id ASC, email ASC";
	$result = query_db($db,$query,'Getting all excluded emails');

	if ($result->num_rows > 0) {

		echo '<table>
		<tr><th class="quarter">Emails</th><th class="quarter">Lines of code excluded</th><th class="half">Applies to</th></tr>';

		// Get the number of lines of code affected by each exclude
		while ($row = $result->fetch_assoc()) {

			$query = "SELECT sum(d.added) AS added
				FROM gitdm_master m
				RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
				LEFT JOIN repos r ON m.repos_id = r.id
				WHERE d.email='" . $row['email'] . "'" . $project_clause;

			$result_lines = query_db($db,$query,'Getting excluded lines for project ' . $project_name . ', email ' . $row['email']);

			$lines = $result_lines->fetch_assoc();

			echo '<tr><td>' . $row['email'] . '</td><td>' . number_format($lines['added']) . '</td><td>';

			// If current page is in the scope of the exclusion rule, allow the user to delete it
			if (isset($project_id) && $row['projects_id'] == $project_id) {
				echo '<span class="button"><form action="manage" id="delexcludeemail" method="post"><input type="submit" name="delete_excludeemail" value="delete"><input type="hidden" name="exclude_id" value="' . $row['id'] . '"><input type="hidden" name="project_id" value="' . $projects_id . '"></form></span>';
			}


			// Identify the scope of the exclusion rule
			if ($row['projects_id'] == 0) {
				echo 'All projects</td>';
			} else {
				$query = "SELECT name FROM projects WHERE id=" . $row['projects_id'];
				$result_excluded_from = query_db($db,$query,'Getting project name');
				$excluded_from = $result_excluded_from->fetch_assoc();
				echo $excluded_from['name'] . '</td>';
			}

			echo '</tr>';
		}

		echo '</table>';

	} else {
		echo '<p><strong>No emails excluded.</strong></p>';
	}

	if (isset($project_id)) {
		echo '<form action="manage" id="newexcludeemail" method="post"><input type="submit" name="confirmnew_excludeemail" value="Exclude an email from ' . $project_name . '"><input type="hidden" name="project_name" value="' . $project_name . '"><input type="hidden" name="project_id" value="' . $project_id .'"></form>';
	}

	echo '</div> <!-- .sub-block -->';
}

?>
