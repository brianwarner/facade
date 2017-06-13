<?php

/*
* Copyright 2016-2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

$title = "Download Results";

include_once "includes/db.php";
include_once "includes/header.php";
include_once "includes/display.php";

list($db,$db_people) = setup_db();

include_once "includes/warnings.php";

$attribution = get_setting($db,'report_attribution');

// Make sure there is data to export
$query = "SELECT NULL from analysis_data";
$result = query_db($db,$query,'Checking if analysis has been run');

// Make sure the data isn't changing

if (get_setting($db,'utility_status') != 'Idle') {

	echo '<div class="content-block">
		<h3>Your data isn\'t ready yet</strong></h3>
		<p>Facade is still working, which means the analysis data is being
		updated. Please check back later.</p>';

} elseif ($result->num_rows > 0) {

	echo '<div class="content-block">
		<h2>All Project Data</h2>

		<table>
		<tr><td class="quarter">All results: </td>
		<td>
		<a href="results-as-csv">csv</a></td>
		</tr>
		<tr>
		<td>All results, with tags: </td>
		<td><a href="results-as-csv?with-tags">csv</a></td>
		</tr>
		</table>

		</div><!-- content-block -->

		<div class="content-block">
		<h2>Filter results</h2>
		<form method=GET action="results-as-csv" id="filter">

		<div class="sub-block">
		<h3>Dates to include</h3>

		<table>
		<tr>
		<td class="quarter">Patches committed after:</td><td>
		<select id="select_start_date" name="start"
		onchange="custom_input(this,\'custom_start_date\',\'70\')">
		<option value="default">Default (' . get_setting($db,"start_date") .
		')</option>
		<option value="custom">Custom</option>
		</select>
		<input type="text" id="custom_start_date" name="start_date"
		class="custom-input hidden"></td>
		</tr>

		</table>

		</div> <!-- .sub-block -->

		<div class="sub-block">
		<h3>Projects to include</h3>
		<p>Limit the results to these projects.</p>
		<table>
		<tr>
		<th><input type="checkbox" onClick="toggle_projects(this)"
		class="checkbox">&nbsp;</th>
		</tr>';

	$query = "SELECT id,name FROM projects ORDER BY name ASC";
	$result = query_db($db,$query,"Getting project names");

	while($row = $result->fetch_assoc()) {
		echo '<tr>
			<td><label><input type="checkbox" name="projects[]" value="' .
			$row["id"] . '" class="checkbox">' . $row["name"] .
			'</label></td>';
	}

	echo '</table>
		</div> <!-- .sub-block -->

		<div class="sub-block">
		<h3>Affilitations</h3>
		<p>Limit results to these affiliations:</p>

		<table>
		<tr>
		<th><input type="checkbox" onClick="toggle_affiliations(this)"
		class="checkbox">&nbsp;</th></tr>
		</table>
		<div class="scroll-list">
		<table>';

		$report_attribution = get_setting($db,'report_attribution');

		$query = "SELECT DISTINCT " . $report_attribution . "_affiliation " .
			"FROM analysis_data ORDER BY " . $report_attribution . "_affiliation";

		$result = query_db($db,$query,"Getting affiliations");

	while($row = $result->fetch_assoc()) {
		echo '<tr>
			<td><label><input type="checkbox" name="affiliations[]"
			value="' . $row[$report_attribution . "_affiliation"] . '"
			class="checkbox">' . $row[$report_attribution . "_affiliation"] .
			'</label></td>';
	}

	echo '</table>

	</div> <!-- .scroll-list -->
	</div> <!-- .sub-block -->

	<div class="sub-block">
	<h3>Special tags</h3>

	<p>Apply these tags to the results.</p>
	<table>
	<tr>
	<th><input type="checkbox" onClick="toggle_tags(this)"
		class="checkbox">&nbsp;</th></tr>';

	$query = "SELECT DISTINCT tag FROM special_tags";
	$result = query_db($db,$query,"Getting tags");

	while($row = $result->fetch_assoc()) {
		echo '<tr>
			<td><label><input type="checkbox" name="tags[]" value="' .
			$row["tag"] . '" class="checkbox">' . $row["tag"] .
			'</label></td>';
	}
	echo '</table>
	</div><!-- .sub-block -->

	<div class="sub-block">
	<input type="submit" name="filter" value="get filtered results as csv">

	</div> <!-- .content-block -->';

	// Determine if there is data for the unknown contributors table
	$query = "SELECT NULL FROM unknown_cache";
	$result = query_db($db,$query,"Figure out if there's anything to display.");

	if ($result->num_rows > 0) {

		echo '<div class="content-block">
			<h2>Top unknown ' . $attribution . 's from all projects</h2>';

		unknown_results_as_table($db);

		echo '</div> <!-- .content-block">';
	}

} else {

	echo '<div class="content-block">

	<p><strong>No data yet.</strong></p>
	<p>Make sure you have added at least one project with at least one repo, and
	run facade-worker.py (preferably as a daily cron job).</p>
	</div> <!-- .content-block -->';

}

include_once "includes/footer.php";

$db->close();
$db_people->close();

?>
