<?php

/*
* Copyright 2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

$title = "";

include_once 'includes/header.php';
include_once 'includes/db.php';
$db = setup_db();

$user = $_SESSION['user'];

$_SESSION = array();
session_destroy();

$query = "INSERT INTO auth_history (user,status)
	VALUES ('" . $user . "','Logged out')";

query_db($db,$query,'Updating history.');

echo '<meta http-equiv="refresh" content="0;/">';

?>
