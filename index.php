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

$title = "";

include_once "includes/db.php";
list($db,$db_people) = setup_db();

include_once "includes/header.php";
include_once "includes/display.php";
include_once "includes/warnings.php";

$report_attribution = get_setting($db,'report_attribution');

$query = "SELECT NULL FROM projects";
$result_projects = query_db($db,$query,'Getting number of projects');

$query = "SELECT NULL FROM repos";
$result_repos = query_db($db,$query,'Getting number of repos');

$query = "SELECT COUNT(DISTINCT email) AS total
	FROM project_annual_cache";
$result_email = query_db($db,$query,'Getting number of developers');
$emails = $result_email->fetch_assoc();

$query = "SELECT SUM(added) AS total
	FROM project_annual_cache";
$result_added = query_db($db,$query,'Getting lines of code');
$added = $result_added->fetch_assoc();

$query = "SELECT COUNT(DISTINCT affiliation) AS total
	FROM project_annual_cache
	WHERE affiliation != '(Unknown)'";
$result_affiliations = query_db($db,$query,'Getting affiliations');
$affiliations = $result_affiliations->fetch_assoc();

$start_date = new DateTime(get_setting($db,'start_date'));

$length_of_time = $start_date->diff(new DateTime(date("y-m-d",time())));

echo '<div class="content-block content-highlight">

	<p>You are currently tracking <strong>' .
	number_format($added['total']) . ' line';

if ($added['total'] != 1) {
	echo 's';
}

echo ' of code</strong>, committed by <strong>' .
	number_format($emails['total']) . ' developer';

if ($emails['total'] != 1) {
	echo 's';
}

echo '</strong>,<br>from <strong>' .
	number_format($affiliations['total']) . ' known organization';

if ($affiliations['total'] != 1) {
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

echo '</strong><br>over the last ';

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
