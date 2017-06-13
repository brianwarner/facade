<?php

/*
* Copyright 2016-2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

$title = "";

include_once "includes/header.php";
include_once "includes/db.php";
include_once "includes/display.php";

list($db,$db_people) = setup_db();

include_once "includes/warnings.php";

$report_attribution = get_setting($db,'report_attribution');

$query = "SELECT NULL FROM projects";
$result_projects = query_db($db,$query,'Getting number of projects');

$query = "SELECT NULL FROM repos";
$result_repos = query_db($db,$query,'Getting number of repos');

$query = "SELECT DISTINCT " . $report_attribution . "_email FROM analysis_data";
$result_email = query_db($db,$query,'Getting number of developers');

$query = "SELECT SUM(added) FROM analysis_data";
$result_added = query_db($db,$query,'Getting lines of code');
$added = $result_added->fetch_assoc();

$query = "SELECT DISTINCT " . $report_attribution . "_affiliation " .
	"FROM analysis_data WHERE " . $report_attribution . "_affiliation != '(Unknown)'";
$result_affiliations = query_db($db,$query,'Getting affiliations');

$start_date = new DateTime(get_setting($db,'start_date'));

$length_of_time = $start_date->diff(new DateTime(date("y-m-d",time())));

echo '<div class="content-block content-highlight">

	<p>You are currently tracking <strong>' .
	number_format($added['SUM(added)']) . ' line';

if ($added['SUM(added)'] != 1) {
	echo 's';
}

echo ' of code</strong>, committed by <strong>' .
	number_format($result_email->num_rows) . ' developer';

if ($result_email->num_rows != 1) {
	echo 's';
}

echo '</strong>,<br>from <strong>' .
	number_format($result_affiliations->num_rows) . ' known organization';

if ($result_affiliations->num_rows != 1) {
	echo 's';
}

echo '</strong>, working in <strong>' . number_format($result_repos->num_rows)
	. ' repo';

if ($result_repos->num_rows != 1) {
	echo 's';
}

echo '</strong>, on <strong>' . number_format($result_projects->num_rows) .
	' project';

if ($result_projects->num_rows != 1) {
	echo 's';
}

echo '</strong><br>over ';

if (get_setting($db,'end_date') == 'yesterday') {
	echo 'the last ';
}

if ($length_of_time->y) {

	echo '<strong>' . $length_of_time->y . ' year';
	if ($length_of_time->y > 1) {
		echo 's';
	}
	echo '</strong>, ';
}

if (($length_of_time->m) || ($length_of_time->y > 0)) {

	echo '<strong>' . $length_of_time->m . ' month';
	if ($length_of_time->m != 1) {
		echo 's';
	}
	echo '</strong>';

	if ($length_of_time->y > 0) {
		echo ',';
	}
	echo ' and ';
}

echo '<strong>' . $length_of_time->d . ' day';
if ($length_of_time->d != 1) {
	echo 's';
}

echo '</strong>.</div> <!-- .content-block, .content-highlight -->';

include_once "includes/footer.php";

$db->close();
$db_people->close();

?>
