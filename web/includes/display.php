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
		$affiliation_clause = "affiliation = '" . $db->real_escape_string($affiliation) . "' AND ";
	}

	if ($email != 'All') {
		$email_clause = "email = '" . $db->real_escape_string($email) . "' AND ";
	}

	if ($stat == 'contributors') {
		$stat_clause = "COUNT(DISTINCT(email))";
	} elseif ($stat == 'patches') {
		$stat_clause = "SUM(patches)";
	} elseif ($stat == 'removed') {
		$stat_clause = "SUM(removed)";
	} elseif ($stat == 'whitespace') {
		$stat_clause = "SUM(whitespace)";
	} elseif ($stat == 'files') {
		$stat_clause = "COUNT(DISTINCT(files))";
	} else {
		$stat_clause = "sum(added)";
	}

	// Put some logic in to change this.

	$sort_field = "sum(added)";
	$sort_order = "DESC";

	// Figure out how many results we have, total

	$query = "SELECT " . $type . "
		FROM " . $cache_table .
		" WHERE " . $year_clause . $scope . "s_id=" . $id .
		" GROUP BY " . $type .
		" ORDER BY " . $sort_field . " " . $sort_order;

	$result = query_db($db,$query,"Get number of results");

	$total_entities = $result->num_rows;

	// Get the sorted list of results.

	$query = "SELECT " . $type . "
		FROM " . $cache_table .
		" WHERE " . $year_clause . $affiliation_clause . $email_clause .
		$scope . "s_id=" .	$id . " GROUP BY " . $type .
		" ORDER BY " . $sort_field . " " . $sort_order .
		$results_clause;

	$result = query_db($db,$query,"Get initial list of results");

	// Make sure we have results

	if ($total_entities) {

        if ($stat == 'contributors') {
            echo '<h3>Unique ' . get_setting($db,'report_attribution') . ' emails';
        } else {
            if ($stat == 'removed') {
                echo '<h3>Lines of code removed by ';
			} elseif ($stat == 'whitespace') {
				echo '<h3>Whitespace changes by ';
            } elseif ($stat == 'patches') {
                echo '<h3>Patches landed by ';
            } elseif ($stat == 'files') {
                echo '<h3>Files changed by ';
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

				echo get_setting($db,'report_attribution');
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
				WHERE " . $year_clause . $email_clause . $scope . "s_id=" . $id . "
				AND " . $type . "='" . $db->real_escape_string($list[$type]) . "'
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

			if (($stat == 'contributors') || ($stat == 'files')) {

				// If doing contribs or files, overwrite $total with meaningful number

				$query = "SELECT " . $stat_clause . " AS stat
					FROM " . $cache_table . "
					WHERE " . $year_clause . $scope . "s_id=" . $id . "
					AND " . $type . "='" . $db->real_escape_string($list[$type]) . "'";

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
				WHERE " . $year_clause . $scope . "s_id=" . $id . "
				GROUP BY period ORDER BY period ASC";

			$result_total = query_db($db,$query,"Get totals");

			while ($period_total = $result_total->fetch_assoc()) {
				$summary[$period_total['period']] = $period_total['stat'];
			}

			foreach ($summary as $summary_data) {
				echo '<td class="total">' . number_format($summary_data)
					. "</td>\n";
			}

			if (($stat == 'contributors') || ($stat == 'files')) {

				// If doing contribs or files, overwrite $grand_total with meaningful number

				$query = "SELECT " . $stat_clause . " AS stat
					FROM " . $cache_table . "
					WHERE " . $year_clause . $scope . "s_id=" . $id;

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

function unknown_results_as_table ($db,$project_id = NULL) {

	// Displays unknown domains and email, sorted by lines of code added.

	$attribution = get_setting($db,'report_attribution');

	if (isset($project_id)) {
		$project_clause = ' AND projects_id=' . $project_id;
	}

	echo '<div class="sub-block">
		<h3>Domains with <i>(Unknown)</i> affiliation</h3>

		<table>
		<tr>
		<th class="quarter">Domain</th>
		<th>Lines of code added</th>
		</tr>';

	$query = "SELECT domain,sum(added) FROM unknown_cache
		WHERE type = '" . $attribution . "'"
		. $project_clause .
		" GROUP BY domain
		ORDER BY sum(added) DESC LIMIT 20";

	$result = query_db($db,$query,"Getting unknown entries");

	while ($row = $result->fetch_assoc()) {
		echo '<tr>
			<td>' . $row["domain"] . '</td>
			<td>' . number_format($row["sum(added)"]);

			if ($_SESSION['access_granted']) {

				echo '<span class="button"><form action="manage" method="post" class="short">
					<input type=hidden name="domain" value="' . $row["domain"] . '">
					<input type=hidden name="project_id" value="' . $project_id . '">
					<input type=submit value="add an affiliation" name="confirmnew_affiliation">
					</form></span>';
			}

			echo '</td>
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

	$query = "SELECT email,added FROM unknown_cache
		WHERE type = '" . $attribution . "'"
		. $project_clause . "
		ORDER BY added DESC LIMIT 20";

	$result = query_db($db,$query,"Getting unknown entries");

	while ($row = $result->fetch_assoc()) {
		echo '<tr>
			<td>' . $row["email"] . '</td>
			<td>' . number_format($row["added"]);

			if ($_SESSION['access_granted']) {
				echo '<span class="button"><form action="manage" method="post" class="short">
					<input type=hidden name="domain" value="' . $row["email"] . '">
					<input type=hidden name="project_id" value="' . $project_id . '">
					<input type=submit value="add as an alias" name="confirmnew_alias">
					<input type=submit value="add an affiliation" name="confirmnew_affiliation">
					</form></span>';
				}
			echo '</td>
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
			<th class="quarter">Analysis Status</th>
			</tr>';

		while ($row_repo = $result_repo->fetch_assoc()) {

			echo '<tr';

			echo '>
				<td><a href="repositories?repo=' . $row_repo["id"] .
				'" class="linked">' . $row_repo["git"] . '</a></td>
				<td>';

			$query = "SELECT status FROM repos_fetch_log
				WHERE repos_id=" . $row_repo["id"] . "
				ORDER BY date DESC LIMIT 1";

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

			$query = "SELECT status,date FROM repos_fetch_log
				WHERE repos_id=" . $row_repo["id"] . "
				AND status='Up-to-date'
				ORDER BY date DESC LIMIT 1";

			$result_repo_log = query_db($db,$query,"Select last successful repo status for " . $row_repo["git"]);

			$row_repo_log = $result_repo_log->fetch_assoc();

			if ($row_repo_log["date"]) {
				$date_attempted = strtotime($row_repo_log["date"]);
				echo '<span class="detail-text">Last successful pull at<br>' .
					date("H:i", $date_attempted) . ' on ' .
					date("M j, Y", $date_attempted). '</span>';
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

			// Get the analysis status

			$query = "SELECT status,date_attempted FROM analysis_log WHERE repos_id = " .
				$row_repo['id'] . " ORDER BY date_attempted DESC";

			$result_analysis = query_db($db,$query,'Get last analysis status');
			$analysis_status = $result_analysis->fetch_assoc();

			if ($analysis_status) {
				echo '<strong>' . $analysis_status['status'] . '</strong><span
				class="detail-text">Last attempted at<br>' .
				date("H:i", strtotime($analysis_status['date_attempted'])) . '
				on ' . date("M j, Y", strtotime($analysis_status['date_attempted'])) .
				'</span>';
			} else {
				// If the return is empty, there must be no status
				echo '<strong><span style="color:green">New</span></strong>';
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

function list_excludes($db,$project_id,$project_name,$type) {

/* List all excluded domains and emails given the project_id. Project ID of 0
 * returns global exclusions, and project ID -1 returns all exclusion rules.
 * $type must be either 'domain' or 'email. */

	$stat = "sum(a.added)";
	$report_attribution = get_setting($db,'report_attribution');

	echo '<div class="sub-block">';

	if ($project_id == 0) {
		// Return stats for all excluded domain/email stats
		$exclude_scope = '';

	} else {
		// Just return the project's excluded domains/emails, including globals.
		$exclude_scope = 'AND (projects_id = ' . $project_id . ' OR
			projects_id = 0)';
	}

	$get_excludes = "SELECT id,projects_id,$type AS type FROM exclude
		WHERE $type IS NOT NULL $exclude_scope ORDER BY projects_id";

	$excludes = query_db($db,$get_excludes,'Getting all excluded ' . $type . 's');

	if ($excludes->num_rows > 0) {

		// If excludes are found, print the table
		echo '<table>
			<tr>
			<th class="quarter">Author\'s ' . $type . '</th>
			<th class="quarter">Lines of code affected</th>
			<th class="half">Applies to</th>
			</tr>';

		while ($exclude = $excludes->fetch_assoc()) {

			if ($exclude['projects_id'] == 0) {

				if ($project_id > 0) {

					// Limit stats to this project for global excludes
					$project = 'AND r.projects_id = ' . $project_id;
				} else {

					// Show stats across all projects for global excludes
					$project = '';
				}

				// Set an appropriate 'Applies to' name
				$name = "All projects";

			} else {

				// Limit excludes to their associated project
				$project = ' AND r.projects_id = ' . $exclude['projects_id'];

				// Set the 'Applies to' text for the appropriate project
				$get_name = "SELECT name FROM projects WHERE name != 
					'(Queued for removal)' AND id=" . $exclude['projects_id'];

				$name_result = query_db($db,$get_name,'getting name for display');

				$name = $name_result->fetch_assoc()['name'];
			}

			$get_details = "SELECT $stat AS stat FROM analysis_data a
				JOIN repos r ON a.repos_id = r.id
				WHERE " . $report_attribution . "_email
				LIKE '%" . $exclude['type'] . "%'" . $project;

			$details = query_db($db,$get_details,'Getting exclude details');

			$detail_stat = $details->fetch_assoc()['stat'];

			if (!$detail_stat) {
				$detail_stat = 0;
			}

			echo '<tr>
				<td>' . $exclude['type'] . '</td>
				<td>' . number_format($detail_stat) . '</td>
				<td>' . $name;

			// If current page is in the rule's scope, allow user to delete it
			if ($exclude['projects_id'] == $project_id &&
			$_SESSION['access_granted']) {
				echo '<span class="button">
					<form action="manage" id="delexclude' . $type . '" method="post">
					<input type="submit" name="delete_exclude' . $type . '" value="delete">
					<input type="hidden" name="exclude_id" value="' . $exclude['id']
					. '">
					<input type="hidden" name="project_id" value="' .
					$project_id . '">
					</form>
					</span>';
			}

			echo '</td>
				</tr>';

		}
		echo '</table>';

	} else {
		echo '<p><strong>No ' . $type . 's excluded</strong></p>';
	}

	if ($project_id >= 0 && $_SESSION['access_granted']) {
		echo '<p>
			<form action="manage" id="newexclude' . $type . '" method="post">
			<input type="submit" name="confirmnew_exclude' . $type . '"
			value="Exclude ' . $type . ' from ' . $project_name . '">
			<input type="hidden" name="project_name" value="' . $project_name .
			'">
			<input type="hidden" name="project_id" value="' . $project_id .'">
			</form>
			</p>';
	}

	echo '</div> <!-- .sub-block -->';
}

function write_import_table_header() {
	echo '<div class="content-block">
		<h2>Add new repos</h2>
		<form action="manage"
		id="import_repos" method="post">
		<table>
		<tr>
		<th class="quarter"><input type="checkbox" onClick="toggle_repos(this)"
			class="checkbox">&nbsp;</th>
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

	echo ' onClick="toggle_select(event)"> ' . $repo_name . '</td><td>';

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
	if ($stat == 'added') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri . '">Lines added</a></span>
	<span class="item';
	if ($stat == 'removed') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri. '&stat=removed">Lines removed</a></span>
	<span class="item';
	if ($stat == 'whitespace') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri . '&stat=whitespace">Whitespace changes</a></span>
	<span class="item';
	if ($stat == 'patches') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri. '&stat=patches">Patches</a></span>
	<span class="item';
	if ($stat == 'contributors') {
		echo ' active';
	}
	echo '"><a href="' . $clean_uri . '&stat=contributors">Unique contributors</a></span>
	</div> <!-- #stat-selector -->';

}

?>
