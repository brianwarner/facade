<?php

/*
* Copyright 2017 Brian Warner
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

if (!empty($_SESSION['access_granted']) && !empty($_SESSION['user'])) {

	if (isset($_GET['emailfailed'])) {
		echo '<div class="error">Warning: Email not updated.</div>';
	} elseif (isset($_GET['emailchanged'])) {
		echo '<div class="info">Email successfully changed.</div>';
	} elseif (isset($_GET['passwordfailed'])) {
		echo '<div class="error">Warning: Password not changed.</div>';
	} elseif (isset($_GET['passwordchanged'])) {
		echo '<div class="info">Password succesfully changed.</div>';
	}

	echo '<h1>Welcome, ' . $_SESSION['user'] . '</h1>

		<div class="content-block">

		<h2>Update your email</h2>

			<form action="manage-users" method="post">
			<p><label>New email:</label><br>
			<span class="text"><input type="text" name="new_email"></span></p>
			<p><label>Current password:</label><br>
			<span class="text"><input type="password" name="password"></span></p>
			<p><input type="submit" value="Update email" name="changeemail"></p>
			</form>

		</div> <!-- .content-block -->

		<div class="content-block">

		<h2>Change your password</h2>

			<form action="manage-users" method="post">
			<p><label>Current password:</label><br>
			<span class="text"><input type="password" name="password"></span></p>
			<p><label>New password:</label><br>
			<span class="text"><input type="password" name="new_password"></span></p>
			<p><label>Confirm new password:</label><br>
			<span class="text"><input type="password" name="con_password"></span></p>
			<p><input type="submit" value="Change password" name="changepassword"></p>
			</form>

		</div> <!-- .content-block -->

		<div class="content-block">

			<form action="logout">
			<input type="submit" value="Log out">
			</form>
		</div> <!-- .content-block -->';

} else {

	if (isset($_GET["failed"])) {
		echo '<div class="error">Login failed.</div>';
	}

	echo '
		<form action="manage-users" method="post">
		<p><label>Username:</label><br>
		<span class="text"><input type="text" name="user"></span></p>
		<p><label>Password:</label><br>
		<span class="text"><input type="password" name="pass"></span></p>
		<input type="submit" value="Log in" name="login">
		</form>';
}

include_once 'includes/footer.php';

$db->close();
$db_people->close();

?>
