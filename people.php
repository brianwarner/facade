<?php

/*
* Copyright 2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

$title = "Affiliations and Aliases";

include_once "includes/header.php";
include_once "includes/db.php";
include_once "includes/display.php";

list($db,$db_people) = setup_db();

// Protect against unauthorized access
if (!$_SESSION['access_granted']) {
	echo '<meta http-equiv="refresh" content="0;/user">';
	die;
}

echo '<div class="content-block">
<p>Facade will attempt to determine the affiliation of a contributor based upon
the contents of this table. It will first attempt to determine if an email is a
known alias for a contributor\'s primary email address. Next it will attempt to
find an exact affiliation match for the email. If it cannot find an exact match,
it will then attempt to match the domain. If no match is found, the affiliation
is marked (Unknown).</p> <p>Since people change companies, and companies get
acquired, you can define overlapping date ranges for the same email address or
domain. Facade will figure out which one applies to the author and committer
date in each commit.</p> <p>You will need to re-run the facade-worker.py script
to see changes take effect.</p> </div> <!-- .content-block -->

<div class="content-block"> <h2>Aliases</h2> ';


// Show aliases
$get_aliases = "SELECT * FROM aliases WHERE active = TRUE ORDER BY canonical ASC";

$result = query_db($db_people,$get_aliases,'Fetching aliases');

if ($result->num_rows > 0) {

	echo '<div class="scroll-list">
			<table>
			<tr><th class="quarter">Primary email</th>
			<th class="quarter">Alias</th>
			<th class="half">&nbsp;</th></tr>';

	while ($alias = $result->fetch_assoc()) {

		echo '<tr><td>' . $alias['canonical'] . '</td>
			<td>' . $alias['alias'] . '</td><td><span class="button">
			<form action="manage" id="delete_alias" method="post">
			<input type=hidden value="' . $alias['id'] . '" name="id">
			<input type="submit" name="delete_alias" value="delete"></span>
			</form></td></tr>';

	}

	echo '</table>
		</div> <!-- .scroll-list -->';
} else {
	echo '<p><strong>No aliases defined</strong></p>';
}

echo '<form action="manage" id="newalias" method="post">
<p><input type="submit" name="confirmnew_alias"
value="Add a new alias"></form></p>';

echo '</div> <!-- .content-block --> <div class="content-block">
<h2>Affiliations</h2>';

// Show domain name mappings first
$get_affiliations = "SELECT * FROM affiliations WHERE domain NOT LIKE '%@%'
	AND active = TRUE ORDER BY domain ASC";

$result = query_db($db_people,$get_affiliations,'Fetching affiliations');

if ($result->num_rows > 0) {

	echo '<div class="sub-block">
			<h3>Affiliations by domain</h3>
			<div class="scroll-list">
			<table>
			<tr><th class="quarter">Domain</th>
			<th class="quarter">Affiliation</th>
			<th class="half">Starting on</th></tr>';

	while ($affiliation = $result->fetch_assoc()) {

		echo '<tr><td>' . $affiliation['domain'] . '</td>
			<td>' . $affiliation['affiliation'] . '</td>
			<td>';

		if ($affiliation['start_date'] != '1970-01-01') {
			echo $affiliation['start_date'];
		}
		echo '<span class="button">
		<form action="manage" id="delete_affiliation" method="post">
		<input type=hidden value="' . $affiliation['id'] . '" name="id">
		<input type="submit" name="delete_affiliation" value="delete"></span>
		</form></td></tr>';

	}
	echo '</table>
		</div> <!-- .scroll-list -->
		</div> <!-- .sub-block -->';
}

// Next show email mappings
$get_affiliations = "SELECT * FROM affiliations WHERE domain LIKE '%@%'
	AND active = TRUE ORDER BY domain ASC, start_date DESC";

$result = query_db($db_people,$get_affiliations,'Fetching affiliations');

if ($result->num_rows > 0) {

	echo '<div class="sub-block">
			<h3>Affiliations by email</h3>
			<div class="scroll-list">
			<table>
			<tr><th class="quarter">Email</th>
			<th class="quarter">Affiliation</th>
			<th class="half">Starting on</th></tr>';

	while ($affiliation = $result->fetch_assoc()) {

		echo '<tr><td>' . $affiliation['domain'] . '</td>
			<td>' . $affiliation['affiliation'] . '</td>
			<td>';

		if ($affiliation['start_date'] != '1970-01-01') {
			echo $affiliation['start_date'];
		}
		echo '<span class="button">
		<form action="manage" id="delete_affiliation" method="post">
		<input type=hidden value="' . $affiliation['id'] . '" name="id">
		<input type="submit" name="delete_affiliation" value="delete"></span>
		</form></td></tr>';

	}

	echo '</table></div> <!-- .scroll-list -->';

} else {
	echo '<p><strong>No affiliations defined</strong></p>';
}

echo '<form action="manage" id="newaffiliation" method="post">
<p><input type="submit" name="confirmnew_affiliation"
value="Add a new affiliation"></form></p>

</div> <!-- .sub-block -->
</div> <!-- .content-block -->';

include_once "includes/footer.php";

$db->close();
$db_people->close();

?>
