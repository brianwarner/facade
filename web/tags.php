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

$title = "Manage tags";

include_once "includes/db.php";
list($db,$db_people) = setup_db();

include_once "includes/header.php";

if (!$_SESSION['access_granted']) {
	echo '<meta http-equiv="refresh" content="0;user">';
	die;
}

$query = "SELECT NULL FROM special_tags";
$result = query_db($db,$query,'Check if any tags are in the database');

if ($result->num_rows > 0 ) {


	echo '<div class="content-block">
		<h2>Tags</h2><table>
		<tr>
		<th class="quarter">Tag</th>
		<th class="quarter">Email</th>
		<th class="quarter">Start date</th>
		<th class="quarter">End date</th>
		</tr>';

	$query = "SELECT * FROM special_tags
		ORDER BY tag, email";
	$result = query_db($db,$query,"getting existing tags");

	while ($row = $result->fetch_assoc()) {
		echo '<tr>
			<td>' . $row["tag"] . '</td>
			<td>' . $row["email"] . '</td>
			<td>' . $row["start_date"] . '</td>
			<td>';

		if ($row["end_date"] <> '9999-12-31') {
			echo $row["end_date"];
		}

		echo '<span class="button"><form
			action="manage" method="post">
			<input type="hidden" name="id" value="' . $row["id"] . '">
			<input type="submit" value="delete" name="delete_tag">
			</form></span></td>
			</tr>';
	}
	echo '</table>

	</div> <!-- .content-block -->';
}

echo '<div class="content-block">
	<h2>Add a tag</h2>
	<form action="manage" id="add_tag" method="post">
	<table class="2-col">
	<tr>
	<td class="eighth">Tag</td><td>
	<select id="select_tag" name="select_tag" class="select-85"
	onchange="custom_input(this,\'new_tag\',\'85\')">
	<option value="custom">Add new...</option>';

$query = "SELECT DISTINCT tag FROM special_tags";
$result = query_db($db,$query,"Getting tag names");

while ($row = $result->fetch_assoc()) {
	echo '<option value="' . $row["tag"] . '">' . $row["tag"] . '</option>';
}

echo '</select><input type="text" id="new_tag" name="new_tag"
	class="custom-input"></td>
	</tr>

	<tr>
	<td>Email</td>
	<td><span class="email"><input type="text" name="email"></span></td>
	</tr>

	<tr>
	<td>Start date</td>
	<td><span class="date"><input type="text" name="start_date"></span></td>
	</tr>

	<tr>
	<td>End date</td>
	<td><select id="select_end_date" name="end_date"
	onchange="custom_input(this,\'custom_date\',\'70\')">
	<option value="ongoing">Ongoing</option>
	<option value="custom">Custom</option>
	</select>

	<input type="text" id="custom_date" name="custom_end"
	class="custom-input hidden">
	</td>
	</tr>
	</table>
	<input type="submit" name="add_tag" value="add">
	</form>

	</div> <!-- .content-block -->';

include_once "includes/footer.php";

$db->close();
$db_people->close();

?>
