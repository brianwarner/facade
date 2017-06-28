<?php

/*
* Copyright 2017 Brian Warner
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

include_once "includes/header.php";
include_once "includes/db.php";
include_once "includes/display.php";

list($db,$db_people) = setup_db();

if (($_POST['user']) && ($_POST['pass']) && ($_POST['login'])) {

	$user = sanitize_input($db,$_POST['user'],64);
	$pass = sanitize_input($db,$_POST['pass'],64);

	$query = "SELECT password FROM auth WHERE user='$user'";
	$result = query_db($db,$query,'checking password');

	if ($result->num_rows == 1) {

		$identity = $result->fetch_assoc();

		if (password_verify($pass,$identity["password"])) {

			$_SESSION['access_granted'] = 1;
			$_SESSION['user'] = $user;

			$query = "INSERT INTO auth_history (user,status)
				VALUES ('" . $_SESSION['user'] . "','Logged in')";

			query_db($db,$query,'Updating history.');

			echo '<meta http-equiv="refresh" content="0;./user">';

		} else {
			echo '<meta http-equiv="refresh" content="0;./user?failed">';
		}
	} else {
		echo '<meta http-equiv="refresh" content="0;./user?failed">';
	}
} elseif (($_SESSION['user']) && ($_SESSION['access_granted'])) {

	if ($_POST['changeemail']) {

		if (($_POST['password']) && ($_POST['new_email'])) {

			$pass = sanitize_input($db,$_POST['password'],64);
			$new_email = sanitize_input($db,$_POST['new_email'],64);

			$query = "SELECT password FROM auth
				WHERE user='" . $_SESSION['user'] . "'";

			$result = query_db($db,$query,'checking identity');

			if ($result->num_rows == 1) {

				$identity = $result->fetch_assoc();

				if (password_verify($pass,$identity["password"])){

					$query = "UPDATE auth
						SET email='$new_email'
						WHERE user='" . $_SESSION['user'] . "'";

					query_db($db,$query,"updating email for " . $_SESSION['user']);

					$query = "INSERT INTO auth_history (user,status)
						VALUES ('" . $_SESSION['user'] . "','Email changed to " . $new_email . "')";

					query_db($db,$query,'Updating history.');

					echo '<meta http-equiv="refresh" content="0;./user?emailchanged">';
				} else {
					echo '<meta http-equiv="refresh" content="0;./user?emailfailed">';
				}
			} else {
				echo '<meta http-equiv="refresh" content="0;./user?emailfailed">';
			}
		} else {
			echo '<meta http-equiv="refresh" content="0;./user?emailfailed">';
		}
	} elseif ($_POST['changepassword']) {
		if (($_POST['password']) && ($_POST['new_password']) && ($_POST['con_password'])) {

			$pass = sanitize_input($db,$_POST['password'],64);
			$new_pass = sanitize_input($db,$_POST['new_password'],64);
			$con_pass = sanitize_input($db,$_POST['con_password'],64);

			$query = "SELECT password FROM auth
				WHERE user='" . $_SESSION['user'] . "'";

			$result = query_db($db,$query,'checking password');

			if ($result->num_rows == 1) {

				$identity = $result->fetch_assoc();

				if (password_verify($pass,$identity['password'])) {

					if ($new_pass == $con_pass) {

						$query = "UPDATE auth
							SET password='" . password_hash($new_pass,PASSWORD_DEFAULT) . "'
							WHERE user='" . $_SESSION['user'] . "'";

						query_db($db,$query,'updating password for ' . $_SESSION['user']);

						$query = "INSERT INTO auth_history (user,status)
							VALUES ('" . $_SESSION['user'] . "','Password changed')";

						query_db($db,$query,'Updating history.');

						echo '<meta http-equiv="refresh" content="0;./user?passwordchanged">';
					} else {
						echo '<meta http-equiv="refresh" content="0;./user?passwordfailed">';
					}
				} else {
					echo '<meta http-equiv="refresh" content="0;./user?passwordfailed">';
				}
			} else {
				echo '<meta http-equiv="refresh" content="0;./user?passwordfailed">';
			}
		} else {
			echo '<meta http-equiv="refresh" content="0;./user?passwordfailed">';
		}
	}
} else {
	echo '<meta http-equiv="refresh" content="0;./user">';
}

$db->close();
$db_people->close();

?>
