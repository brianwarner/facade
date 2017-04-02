<?php

/*
* Copyright 2016 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

function cached_results_as_summary_table($db,$scope,$id,$type,$max_results,$year,$affiliation,$email,$stat) {

	if ($max_results != 'All') {
		$results_clause = " LIMIT " . $max_results;
	}

	if ($year == 'All') {
		$cache_table = $scope . '_annual_cache';
		$year_clause = '';
		$period = 'year';

		// Get the range of years to name the summary array

		$summary_keys = array();

		$query = "SELECT year FROM " . $cache_table .
			" GROUP BY year ORDER BY year ASC";
		$result = query_db($db,$query,"Getting range of years");

		while ($year_key = $result->fetch_assoc()) {
			array_push($summary_keys,$year_key['year']);
		}

	} else {
		$cache_table = $scope . '_monthly_cache';
		$year_clause = "year = " . $year . " AND ";
		$period = 'month';
		$summary_keys = array(1,2,3,4,5,6,7,8,9,10,11,12);
	}

	if ($affiliation != 'All') {
		$affiliation_clause = "affiliation = '" . $affiliation . "' AND ";
	}

	if ($email != 'All') {
		$email_clause = "email = '" . $email . "' AND ";
	}

	if ($stat == 'contributors') {
		$stat_clause = "COUNT(DISTINCT(email))";
	} elseif ($stat == 'patches') {
		$stat_clause = "SUM(patches)";
	} elseif ($stat == 'removed') {
		$stat_clause = "SUM(removed)";
	} else {
		$stat_clause = "sum(added)";
	}

	// Put some logic in to change this.

	$sort_field = "sum(added)";
	$sort_order = "DESC";

	// Figure out how many results we have, total

	$query = "SELECT " . $type . "
		FROM " . $cache_table .
		" WHERE " . $year_clause . "id=" . $id .
		" GROUP BY " . $type .
		" ORDER BY " . $sort_field . " " . $sort_order;

	$result = query_db($db,$query,"Get initial list of results");

	$total_entities = $result->num_rows;

	// Get the sorted list of results.

	$query = "SELECT " . $type . "
		FROM " . $cache_table .
		" WHERE " . $year_clause . $affiliation_clause . $email_clause . "id=" .
		$id . " GROUP BY " . $type .
		" ORDER BY " . $sort_field . " " . $sort_order .
		$results_clause;

	$result = query_db($db,$query,"Get initial list of results");

	// Make sure we have results

	if ($total_entities) {

        if ($stat == 'contributors') {
            echo '<h3>Unique contributor emails';
        } else {
            if ($stat == 'removed') {
                echo '<h3>Lines of code removed by ';
            } elseif ($stat == 'patches') {
                echo '<h3>Patched landed by ';
            } else {
                echo '<h3>Lines of code added by ';
            }

            if ($email != 'All') {
                echo $email;

            } else {

                if ($max_results != 'All' &&
                $max_results <= $total_entities) {

                    echo 'the top ';
                    if ($max_results > 1) {
                        echo $max_results . ' ';
                    }
                } else {
                    echo 'all ';
                }

                echo 'contributor';
                if ($max_results != 1) {
                    echo 's';
                }
            }
        }

        if ($affiliation != 'All') {
            echo ' from ' . $affiliation;
        }

        if ($year != 'All') {
            echo ' in ' . $year;
        }

        if (($affiliation == 'All') && ($email == 'All')) {
            echo ', by ' . $type . "</h3>\n";
        }

		// Print the table header

		echo "<table><tr>\n";
		echo '<th>&nbsp;</th>';
		foreach ($summary_keys as $key) {
			echo '<th class="results-period">';
			if ($year == 'All') {
				echo '<a href="' . $_SERVER['REQUEST_URI'] . '&year='.
				$key . '">' . $key . '</a>';

			} else {
				$month = DateTime::createFromFormat('!m',$key);
				echo $month->format('M');
			}
			echo "</th>\n";
		}
		echo '<th class="results-total">Total</th>' . "\n</tr>\n";

		$grand_total = 0;

		while ($list = $result->fetch_assoc()) {

			// Get data for each row of the table

			$query = "SELECT " . $stat_clause . " AS stat," .
				$period . " AS period
				FROM " . $cache_table . "
				WHERE " . $year_clause . "id=" . $id . "
				AND " . $type . "='" . $list[$type] . "'
				GROUP BY period ORDER BY period ASC";

			$result_data = query_db($db,$query,"Get data");

			// Use a named array to identify dates with no data

			$summary = array_fill_keys($summary_keys,0);
			$total = 0;

			while ($data = $result_data->fetch_assoc()) {
				$summary[$data['period']] = $data['stat'];
				$total += $data['stat'];
				$grand_total += $data['stat'];
			}

			echo '<tr><td class="results-entity">';

			if (($email == 'All') || ($affiliation == 'All')) {
				echo '<a href="' . $_SERVER['REQUEST_URI'] .
					'&' . $type . '=' . rawurlencode($list[$type]) . '">'
					. $list[$type] . '</a>';
			} else {
				echo $list[$type];
			}
			echo "</td>\n";
			foreach ($summary as $summary_data) {
				echo '<td class="' . $stat . '">' . number_format($summary_data)
					. "</td>\n";
			}

			if ($stat == 'contributors') {

				// If doing contribs, overwrite $total with meaningful number

				$query = "SELECT " . $stat_clause . " AS stat
					FROM " . $cache_table . "
					WHERE " . $year_clause . "id=" . $id . "
					AND " . $type . "='" . $list[$type] . "'";

				$result_contribs = query_db($db,$query,"Get data");

				$total_contribs = $result_contribs->fetch_assoc();

				$total = $total_contribs['stat'];
			}

			echo '<td class="total">' . number_format($total) . "</td></tr>\n";
		}

		if (($max_results == 'All' || $max_results >= $total_entities)
			&& ($affiliation =='All' && $email == 'All')) {

			// Write the totals row

			$summary = array_fill_keys($summary_keys,0);

			echo '<tr><td class="total">Total from all contributors</td>';

			$query = "SELECT " . $stat_clause . " as stat," .
				$period . " AS period
				FROM " . $cache_table . "
				WHERE " . $year_clause . "id=" . $id . "
				GROUP BY period ORDER BY period ASC";

			$result_total = query_db($db,$query,"Get totals");

			while ($period_total = $result_total->fetch_assoc()) {
				$summary[$period_total['period']] = $period_total['stat'];
			}

			foreach ($summary as $summary_data) {
				echo '<td class="total">' . number_format($summary_data)
					. "</td>\n";
			}

			if ($stat == 'contributors') {

				// If doing contribs, overwrite $grand_total with meaningful number

				$query = "SELECT " . $stat_clause . " AS stat
					FROM " . $cache_table . "
					WHERE " . $year_clause . "id=" . $id;

				$result_contribs = query_db($db,$query,"Get data");

				$total_contribs = $result_contribs->fetch_assoc();

				$grand_total = $total_contribs['stat'];
			}

			echo '<td class="grand-total">' . number_format($grand_total) .
				"</td></tr>\n";
		}

		echo '</table>';

		// If there are more results to show, add "View all" link
		if ($max_results != 'All' &&
		$max_results < $total_entities ) {

			echo '</p><a href="' . $_SERVER['REQUEST_URI'] . '&detail=' .
			$type . '">View all</a></p>';
		}
	} else {
		echo '<p><strong>No data found.</strong></p>';
	}
}

function gitdm_results_as_summary_table($db,$scope,$id,$type,$max_results,$year,$affiliation,$email,$stat) {

	// This function is deprecated and will be removed.

	if ($scope == 'project') {
		$scope_clause = "r.projects_id=" . $id . " AND ";
	} elseif ($scope == 'repo') {
		$scope_clause = "r.id=" . $id . " AND ";
	} else {
		$scope_clause = "";
	}

	if ($max_results != 'All') {
		$results_clause = " LIMIT " . $max_results;
	}

	if ($year == 'All') {
		$period = 'YEAR(m.start_date)';
		$year_clause = '';
	} else {
		$period = 'MONTH(m.start_date)';
		$year_clause = "YEAR(m.start_date) = " . $year . " AND ";
	}

	if ($affiliation != 'All') {
		$affiliation_clause = "d.affiliation = '" . $affiliation . "' AND ";
	}

	if ($email != 'All') {
		$email_clause = "d.email = '" . $email . "' AND ";
	}

	if ($stat == 'contributors') {
		$stat_clause = "COUNT(DISTINCT(d.email))";
	} elseif ($stat == 'patches') {
		$stat_clause = "SUM(d.changesets)";
	} elseif ($stat == 'removed') {
		$stat_clause = "SUM(d.removed)";
	} else {
		$stat_clause = "sum(d.added)";
	}

	// Fetch the data
	$query = "SELECT d." . $type . " AS " . $type . ",
			" . $stat_clause . " AS added,
			" . $period . " AS period
			FROM repos r
			RIGHT JOIN gitdm_master m ON r.id = m.repos_id
			RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
			LEFT JOIN exclude e
			ON (d.email = e.email
				AND (r.projects_id = e.projects_id
					OR e.projects_id = 0))
			OR (d.email LIKE CONCAT('%',e.domain)
				AND (r.projects_id = e.projects_id
					OR e.projects_id = 0))
			WHERE " . $scope_clause . $year_clause .
			$affiliation_clause . $email_clause . "
			e.email IS NULL
			AND e.domain IS NULL
			GROUP BY d." . $type . ", " . $period;

	$result = query_db($db,$query,"Fetching result data");

	// Stash data by entity and year so it's easier to access later
	while ($data = $result->fetch_assoc()) {
		$summary[$data[$type]][$data["period"]] = $data["added"];
		$summary["Total"][$data["period"]] += $data["added"];

		// Cumulative contributor stats by company don't make sense
		if ($stat != 'contributors') {
			$summary[$data[$type]]["Total"] += $data["added"];
			$summary["Grand total"] += $data["added"];
		}
	}

	// Figure out if there are more entities that could be shown
	$query = "SELECT NULL
		FROM repos r
		RIGHT JOIN gitdm_master m ON r.id = m.repos_id
		RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
		LEFT JOIN exclude e ON (d.email = e.email
			AND (r.projects_id = e.projects_id
				OR e.projects_id = 0))
				OR (d.email LIKE CONCAT('%',e.domain)
			AND (r.projects_id = e.projects_id
				OR e.projects_id = 0))
		WHERE " . $year_clause . $scope_clause .
		$affiliation_clause . $email_clause . "
		e.email IS NULL
		AND e.domain IS NULL
		GROUP BY d." . $type;

	$result_total = query_db($db,$query,"Finding out how many entities are in the dataset.");
	$total_entities = $result_total->num_rows;

	if ($summary) {
		// If there's data for the table, proceed

		if ($stat == 'contributors') {
			echo '<h3>Unique contributor emails';
		} else {
			if ($stat == 'removed') {
				echo '<h3>Lines of code removed by ';
			} elseif ($stat == 'patches') {
				echo '<h3>Patched landed by ';
			} else {
				echo '<h3>Lines of code added by ';
			}

			if ($email != 'All') {
				echo $email;

			} else {

				if ($max_results != 'All' &&
				$max_results <= $total_entities) {

					echo 'the top ';
					if ($max_results > 1) {
						echo $max_results . ' ';
					}
				} else {
					echo 'all ';
				}

				echo 'contributor';
				if ($max_results != 1) {
					echo 's';
				}
			}
		}

		if ($affiliation != 'All') {
			echo ' from ' . $affiliation;
		}

		if ($year != 'All') {
			echo ' in ' . $year;
		}

		if (($affiliation == 'All') && ($email == 'All')) {
			echo ', by ' . $type . '</h3>';
		}

// this also needs the constraints, and the go from year to period
		// Get the range of years
		$query = "SELECT " . $period . " AS period
				FROM repos r
				RIGHT JOIN gitdm_master m ON r.id = m.repos_id
				RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
				LEFT JOIN exclude e ON (d.email = e.email
					AND (r.projects_id = e.projects_id
						OR e.projects_id = 0))
				OR (d.email LIKE CONCAT('%',e.domain)
					AND (r.projects_id = e.projects_id
						OR e.projects_id = 0))
				WHERE " . $scope_clause . $year_clause .
				$affiliation_clause . $email_clause . "
				e.email IS NULL
				AND e.domain IS NULL
				GROUP BY " . $period . "
				ORDER BY " . $period . " ASC";

		$result_period = query_db($db,$query,"Finding out how many years are in the dataset.");

		// Entity names in descending order of LoC added to build results table.

		$query = "SELECT d." . $type . " AS " . $type . "
				FROM repos r
				RIGHT JOIN gitdm_master m ON r.id = m.repos_id
				RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
				LEFT JOIN exclude e ON (d.email = e.email
					AND (r.projects_id = e.projects_id
						OR e.projects_id = 0))
				OR (d.email LIKE CONCAT('%',e.domain)
					AND (r.projects_id = e.projects_id
						OR e.projects_id = 0))
				WHERE " . $scope_clause . $year_clause .
				$affiliation_clause . $email_clause . "
				e.email IS NULL
				AND e.domain IS NULL
				GROUP BY d." . $type . "
				ORDER BY " . $stat_clause . " DESC" . $results_clause;

		$result_entity = query_db($db,$query,"Finding out which entities are in the dataset.");
		$number_entities = $result_entity->num_rows;

		// Create the summary table
		echo '<table>
			<tr>
			<th class="results-entity"></th>';

		while ($period = $result_period->fetch_assoc()) {
			echo '<th class="results-period">';
			if ($year == 'All') {
				echo '<a href="' . $_SERVER['REQUEST_URI'] . '&year='.
				$period["period"] . '">' . $period["period"] . '</a>';

			} else {
				$month = DateTime::createFromFormat('!m',$period["period"]);
				echo $month->format('M');
			}
			echo '</th>';
		}

		echo '<th class="results-total">Total</th>
			</tr>';

		$result_period->data_seek(0);

		while ($entity = $result_entity->fetch_assoc()) {

			// Collect cumulative contributor stats by company that do make sense
			if ($stat == 'contributors') {
				$query = "SELECT d." . $type . " AS " . $type . ",
					" . $stat_clause . " AS added
					FROM repos r
					RIGHT JOIN gitdm_master m ON r.id = m.repos_id
					RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
					LEFT JOIN exclude e
					ON (d.email = e.email
						AND (r.projects_id = e.projects_id
							OR e.projects_id = 0))
					OR (d.email LIKE CONCAT('%',e.domain)
						AND (r.projects_id = e.projects_id
							OR e.projects_id = 0))
					WHERE " . $scope_clause . $year_clause .
					$affiliation_clause . $email_clause . "
					e.email IS NULL
					AND e.domain IS NULL
					AND d." . $type . " = '" . $entity[$type] . "'
					GROUP BY d." . $type;

				$result_contrib_total = query_db($db,$query,"Fetching result data");

				$contrib_total = $result_contrib_total->fetch_assoc();
				$summary[$entity[$type]]["Total"] = $contrib_total["added"];
				$summary["Grand total"] += $contrib_total["added"];
			}

			echo '<tr>
				<td class="results-entity">';
				if (($email == 'All') || ($affiliation == 'All')) {
					echo '<a href="' . $_SERVER['REQUEST_URI'] .
						'&' . $type . '=' . rawurlencode($entity[$type]) . '">'
						. $entity[$type] . '</a>';
				} else {
					echo $entity[$type];
				}
			echo '</td>';
			while ($period = $result_period->fetch_assoc()) {
				echo '<td class="added">' .
					number_format($summary[$entity[$type]][$period["period"]]) .
					'</td>';
			}
			echo '<td class="total">' .
			number_format($summary[$entity[$type]]["Total"]) .
			'</td></tr>';
			$result_period->data_seek(0);
		}

		if ((($email == 'All') && ($affiliation == 'All')) || ($number_entities > 1)) {

			echo '<tr>
				<td class="total">Total from all contributors</td>';

			$result_period->data_seek(0);

			while ($period = $result_period->fetch_assoc()) {
				echo '<td class="total">' .
					number_format($summary["Total"][$period["period"]]) . '</td>';
			}

			echo '<td class="grand-total">' . number_format($summary["Grand total"])
				. '</td>
				</tr>';
		}
		echo '</table>';

		// If there are more results to show, add "View all" link
		if ($max_results != 'All' &&
		$max_results < $total_entities ) {

			echo '</p><a href="' . $_SERVER['REQUEST_URI'] . '&detail=' .
			$type . '">View all</a></p>';
		}

	} else {
		echo '<p><strong>No data found.</strong></p>';
	}
}

function unknown_results_as_table ($db,$project_id = NULL) {

	// Displays unknown domains and email, sorted by lines of code added.

	if (isset($project_id)) {
		$project_clause = ' WHERE projects_id=' . $project_id;
	}

	echo '<div class="sub-block">
		<h3>Domains with <i>(Unknown)</i> affiliation</h3>

		<table>
		<tr>
		<th class="quarter">Domain</th>
		<th>Lines of code added</th>
		</tr>';

	$query = "SELECT domain,sum(added) FROM unknown_cache"
		. $project_clause .
		" GROUP BY domain
		ORDER BY sum(added) DESC LIMIT 20";

	$result = query_db($db,$query,"Getting unknown entries");

	while ($row = $result->fetch_assoc()) {
		echo '<tr>
			<td>' . $row["domain"] . '</td>
			<td>' . number_format($row["sum(added)"]) . '</td>
			</tr>';
	}

	echo '</table>

		</div> <!-- .sub-block -->

		<div class="sub-block">
		<h3>Emails with <i>(Unknown)</i> affiliation</h3>

		<table>
		<tr>
		<th class="quarter">Email</th>
		<th>Lines of code added</th>
		</tr>';

	$query = "SELECT email,added FROM unknown_cache"
		. $project_clause . "
		ORDER BY added DESC LIMIT 20";

	$result = query_db($db,$query,"Getting unknown entries");

	while ($row = $result->fetch_assoc()) {
		echo '<tr>
			<td>' . $row["email"] . '</td>
			<td>' . number_format($row["added"]) . '</td>
			</tr>';
	}

	echo '</table>
	</div> <!-- .sub-block -->';
}

function list_repos ($db,$project_id) {

	$query = "SELECT * FROM repos WHERE projects_id=" . $project_id;
	$result_repo = query_db($db,$query,"Select repos for project " . $project_id);

	if ($result_repo->num_rows > 0) {
		echo '<table>
			<tr>
			<th class="half">Git repo</th>
			<th class="quarter">Repo Status</th>
			<th class="quarter">gitdm Status</th>
			</tr>';

		while ($row_repo = $result_repo->fetch_assoc()) {

			echo '<tr';

			echo '>
				<td><a href="repositories?repo=' . $row_repo["id"] .
				'" class="linked">' . $row_repo["git"] . '</a></td>
				<td>';

			$query = "SELECT status FROM repos_fetch_log
				WHERE repos_id=" . $row_repo["id"] . "
				ORDER BY id DESC LIMIT 1";

			$result_repo_log = query_db($db,$query,"Select last repo status for " . $row_repo["git"]);

			$row_repo_log = $result_repo_log->fetch_assoc();

			echo '<div class="detail"><strong>';

			if ($row_repo_log["status"]) {
				echo $row_repo_log["status"];
			} else {
				echo '<span style="color:green">New</span>';
			}
			echo '</strong>';

			// Determine the last time the git repo was successfully pulled

			$query = "SELECT status,date_attempted FROM repos_fetch_log
				WHERE repos_id=" . $row_repo["id"] . "
				AND status='Up-to-date'
				ORDER BY date_attempted DESC LIMIT 1";

			$result_repo_log = query_db($db,$query,"Select last successful repo status for " . $row_repo["git"]);

			$row_repo_log = $result_repo_log->fetch_assoc();

			if ($row_repo_log["date_attempted"]) {
				$date_attempted = strtotime($row_repo_log["date_attempted"]);
				echo '<span class="detail-text">Last successful pull at<br>' . date("H:i", $date_attempted) . ' on ' . date("M j, Y", $date_attempted). '</span>';
			}

			// Determine if repo is marked to be removed during the next facade-worker.py run

			if ($row_repo['status'] == "Delete") {
				echo '<br><span style="color:red">Marked for removal</span>';
			}


			echo '</div><!-- .detail -->
				</td>
				<td>';
			if ($_SESSION['access_granted']) {
				echo '<span class="button"><form action="manage" id="delrepo"
					method="post">
					<input type="submit" name="confirmdelete_repo" value="delete">
					<input type="hidden" name="project_id" value="' . $project_id . '">
					<input type="hidden" name="repo_id" value="' . $row_repo["id"]. '">
					</form></span>';
			}
			echo '<div class="detail">';

			// Find any incomplete repos

			$query = "SELECT status FROM gitdm_master
				WHERE repos_id=" . $row_repo["id"] . "
				AND status!='Complete'
				ORDER BY date_attempted ASC";

			$result_gitdm_master = query_db($db,$query,"Get any incomplete gitdm status");
			$row_gitdm_master = $result_gitdm_master->fetch_assoc();

			if ($row_gitdm_master) {
				echo '<span style="color:red"><strong>INCOMPLETE</strong></span>';
			} else {
				// Determine if the repo has complete status
				$query = "SELECT status FROM gitdm_master
					WHERE repos_id=" . $row_repo["id"] . "
					AND status='Complete'
					ORDER BY date_attempted DESC";

				$result_gitdm_master = query_db($db,$query,"Get any incomplete gitdm status");
				$row_gitdm_master = $result_gitdm_master->fetch_assoc();

				if ($row_gitdm_master) {
					echo "<strong>Complete</strong>";
				} else {
					// If the return is empty, there must be no status
					echo '<strong><span style="color:green">New</span></strong>';
				}

			}

			$query = "SELECT start_date FROM gitdm_master
				WHERE repos_id=" . $row_repo["id"] . "
				AND status='Complete'
				ORDER BY start_date DESC LIMIT 1";

			$result_gitdm_master = query_db($db,$query,"Get last complete gitdm status");
			$row_gitdm_master = $result_gitdm_master->fetch_assoc();

			if ($row_gitdm_master['start_date']) {
				$date_attempted = strtotime($row_gitdm_master["start_date"]);
				echo '<span class="detail-text">Current through<br>' . date("F j, Y", $date_attempted) . '</span>';
			}

			echo '</div><!-- .detail -->
				</td>
				</tr>';

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

	$stat_clause = "sum(d.added)";

	// If scope is for a specific project, get that project's name - can I eliminate this?
	if ($project_id > 0) {
		$query = "SELECT name FROM projects
			WHERE id=" . $project_id;

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

	$query = "SELECT id,domain,projects_id FROM exclude
		WHERE domain IS NOT NULL" .
		$project_id_clause;

	$result = query_db($db,$query,'Getting all excluded domains');

	if ($result->num_rows > 0) {

		echo '<table>
			<tr>
			<th class="quarter">Domains</th>
			<th class="quarter">Lines of code excluded</th>
			<th class="half">Applies to</th>
			</tr>';

		// Get the number of lines of code affected by each exclude
		while ($row = $result->fetch_assoc()) {

			$query = "SELECT " . $stat_clause . " AS added
				FROM gitdm_master m
				RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
				LEFT JOIN repos r ON m.repos_id = r.id
				WHERE d.email LIKE '%" . $row['domain'] . "%'" . $project_clause;

			$result_lines = query_db($db,$query,
				'Getting excluded lines for project ' . $project_name . ',
				domain ' . $row['domain']);

			$lines = $result_lines->fetch_assoc();

			echo '<tr>
				<td>' . $row['domain'] . '</td>
				<td>' . number_format($lines['added']) . '</td>
				<td>';

			// If current page is in the rule's scope, allow user to delete it
			if (isset($project_id) &&
			$row['projects_id'] == $project_id &&
			$_SESSION['access_granted']) {
				echo '<span class="button">
					<form action="manage" id="delexcludedomain" method="post">
					<input type="submit" name="delete_excludedomain" value="delete">
					<input type="hidden" name="exclude_id" value="' . $row['id']
					. '">
					<input type="hidden" name="project_id" value="' .
					$project_id . '">
					</form>
					</span>';
			}

			// Identify the scope of the exclusion rule
			if ($row['projects_id'] == 0) {
				echo 'All projects</td>';
			} else {
				$query = "SELECT name FROM projects
					WHERE id=" . $row['projects_id'];

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

	if (isset($project_id) && $_SESSION['access_granted']) {
		echo '<p>
			<form action="manage" id="newexcludedomain" method="post">
			<input type="submit" name="confirmnew_excludedomain"
			value="Exclude a domain from ' . $project_name . '">
			<input type="hidden" name="project_name" value="' . $project_name .
			'">
			<input type="hidden" name="project_id" value="' . $project_id .'">
			</form>
			</p>';
	}

	echo '</div> <!-- .sub-block -->

	<div class="sub-block">';

	$query = "SELECT id,email,projects_id FROM exclude
		WHERE email IS NOT NULL" .
		$project_id_clause . "
		ORDER BY projects_id ASC,
		email ASC";

	$result = query_db($db,$query,'Getting all excluded emails');

	if ($result->num_rows > 0) {

		echo '<table>
			<tr>
			<th class="quarter">Emails</th>
			<th class="quarter">Lines of code excluded</th>
			<th class="half">Applies to</th>
			</tr>';

		// Get the number of lines of code affected by each exclude
		while ($row = $result->fetch_assoc()) {

			$query = "SELECT " . $stat_clause . " AS added
				FROM gitdm_master m
				RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id
				LEFT JOIN repos r ON m.repos_id = r.id
				WHERE d.email='" . $row['email'] . "'" . $project_clause;

			$result_lines = query_db($db,$query,
				'Getting excluded lines for project ' . $project_name .
				', email ' . $row['email']);

			$lines = $result_lines->fetch_assoc();

			echo '<tr><td>' . $row['email'] . '</td><td>' . number_format($lines['added']) . '</td><td>';

			// If current page is in rule's scope, allow user to delete it
			if (isset($project_id) &&
			$row['projects_id'] == $project_id &&
			$_SESSION['access_granted']) {

				echo '<span class="button">
					<form action="manage" id="delexcludeemail" method="post">
					<input type="submit" name="delete_excludeemail"
					value="delete">
					<input type="hidden" name="exclude_id" value="' . $row['id']
					. '">
					<input type="hidden" name="project_id" value="' .
					$projects_id . '">
					</form>
					</span>';

			}


			// Identify the scope of the exclusion rule
			if ($row['projects_id'] == 0) {
				echo 'All projects</td>';
			} else {
				$query = "SELECT name FROM projects
					WHERE id=" . $row['projects_id'];

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

	if (isset($project_id) && $_SESSION['access_granted']) {
		echo '<form action="manage" id="newexcludeemail" method="post">
			<input type="submit" name="confirmnew_excludeemail"
			value="Exclude an email from ' . $project_name . '">
			<input type="hidden" name="project_name" value="' . $project_name .
			'">
			<input type="hidden" name="project_id" value="' . $project_id .'">
			</form>';
	}

	echo '</div> <!-- .sub-block -->';
}

function write_import_table_header() {
	echo '<div class="content-block">
		<h2>Add new repos</h2>
		<form action="manage" onClick="toggle_select(event)"
		id="import_repos" method="post">
		<table>
		<tr>
		<th class="quarter">&nbsp;</th>
		<th>&nbsp;</th>
		</tr>';
}

function write_import_table_subheader($section) {
	echo '<tr>
		<td colspan="2"><strong>' . $section . '</strong></td>
		</tr>';
}

function write_import_table_row($repo_name,$git_links,$is_already_used) {
	echo '<tr';
	if ($is_already_used) {
		echo 'class="disabled"';
	}
	echo '>
		<td><input type="checkbox" name="repos[]" class="checkbox"';
	if ($is_already_used) {
		echo ' disabled="true" checked="checked"
			title="This repo is already in use" value="' . $repo_name .
			'-existing"';
	} else {
		echo ' value="' . $repo_name . '"';
	}

	echo '> ' . $repo_name . '</td><td>';

	// Present options, disable rows where git repo is already in the database
	foreach ($git_links as $git_link) {
		echo '<input type="radio" name="radio_' . $repo_name . '" class="select"
			value="' . $git_link . '" disabled="true"';

		if ($is_already_used == $git_link) {
			echo ' checked="checked" title="This repo is already in use"';
		}
		echo '> ' . $git_link . '<br>';
	}
	echo '</td>
		</tr>';

}

function write_import_table_footer($project_id) {
	echo '</table>
	<p>
	<input type="hidden" name="project_id" value="' . $project_id . '">
	<input type="submit" name="import_repos" value="Import selections"></p>
	</div> <!-- .content-block --></form>';
}

function write_stat_selector_submenu($raw_uri,$stat) {
	// Strip out existing stat parameter from URL, write submenu

	if (strpos($raw_uri,'&stat=')) {
		$prefix = substr($raw_uri,0,strpos($raw_uri,'&stat='));
		$suffix = substr($raw_uri,strpos($raw_uri,'&',strpos($raw_uri,'&stat=')+1));

		if (strlen($raw_uri) == strlen($suffix)) {
			$clean_uri = $prefix;
		} else {
			$clean_uri = $prefix . $suffix;
		}
	} else {
		$clean_uri = $raw_uri;
	}

	echo '<h2>Metric</h2><div id="stat-selector">
	<span class="first item';
	if ($stat == '') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri . '">Lines added</a></span>
	<span class="item';
	if ($stat == 'removed') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri. '&stat=removed">Lines removed</a></span>
	<span class="item';
	if ($stat == 'patches') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri . '&stat=patches">Patches</a></span>
	<span class="item';
	if ($stat == 'contributors') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri . '&stat=contributors">Unique contributors</a></span>
	</div> <!-- #stat-selector -->';

}

?>
