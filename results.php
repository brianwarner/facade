<?php

/*
* Copyright 2016 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

$title = "Download Results";

include_once "includes/header.php";
include_once "includes/db.php";
include_once "includes/display.php";
$db = setup_db();

// Make sure there is data to export
$query = "SELECT NULL from gitdm_data";
$result = query_db($db,$query,'Checking if gitdm has been run');

if ($result->num_rows > 0) {

	echo '<div class="content-block"><h2>All Project Data</h2><table>
	<tr><td class="quarter">All results: </td><td><a href="results-as-csv">csv</a></td></tr>
	<tr><td>All results, with tags: </td><td><a href="results-as-csv?with-tags">csv</a></td></tr>
	</table></div><!-- content-block -->';


	echo '<div class="content-block"><h2>Filtered results</h2>
	<form method=GET action="results-as-csv" id="filter">

	<div class="sub-block">
	<h3>Dates to include</h3>

	<table>
	<tr><td class="eighth">Starting on:</td><td>
	<select id="select_start_date" name="start" onchange="custom_input(this,\'custom_start_date\',\'70\')">
	<option value="default">Default (' . get_setting($db,"start_date") . ')</option>
	<option value="custom">Custom</option>
	</select>
	<input type="text" id="custom_start_date" name="start_date" class="custom-input hidden"></td></tr>

	<tr><td>Ending on:</td><td>
	<select id="select_end_date" name="end" onchange="custom_input(this,\'custom_end_date\',\'70\')">
	<option value="default">Default (' . get_setting($db,"end_date") . ')</option>
	<option value="custom">Custom</option>
	</select>
	<input type="text" id="custom_end_date" name="end_date" class="custom-input hidden"></td></tr>

	</table>

	</div> <!-- .sub-block -->

	<div class="sub-block">
	<h3>Projects to include</h3>
	<table>
	<tr><th><input type="checkbox" onClick="toggle_projects(this)" class="checkbox">All projects</th></tr>
	';

	$query = "SELECT id,name FROM projects";
	$result = query_db($db,$query,"Getting project names");

	while($row = $result->fetch_assoc()) {
		echo '<tr><td><input type="checkbox" name="projects[]" value="' . $row["id"] . '" class="checkbox">' . $row["name"] . '</td>';
	}

	echo '</table></div><!-- .sub-block -->

	<div class="sub-block">
	<h3>Additional tags</h3>

	<table>
	<tr><th><input type="checkbox" onClick="toggle_tags(this)" class="checkbox">Include all tags</th></tr>';

	$query = "SELECT DISTINCT tag FROM special_tags";
	$result = query_db($db,$query,"Getting tags");

	while($row = $result->fetch_assoc()) {
		echo '<tr><td><input type="checkbox" name="tags[]" value="' . $row["tag"] . '" class="checkbox">' . $row["tag"] . '</td>';
	}

	echo '</table>
	</div> <!-- .sub-block -->
	<div class="sub-block">
	<input type="submit" name="filter" value="get filtered results as csv">

	</div> <!-- .content-block -->';

	// Determine if there is data for the unknown contributors table
	$query = "SELECT NULL FROM unknown_cache";
	$result = query_db($db,$query,"Figure out if there's anything to display.");

	if ($result->num_rows > 0) {

		echo '<div class="content-block"><h2>Top unknown contributors from all projects</h2>';

		unknown_results_as_table($db);

		echo '</div> <!-- .content-block">';
	}

} else {

	echo '<div class="content-block"><p><strong>No data yet.</strong></p><p>Make sure you have added at least one project with at least one repo, and run facade-worker.py (preferably as a daily cron job).</p></div> <!-- .content-block -->';

}


include_once "includes/footer.php";
close_db($db);
?>
