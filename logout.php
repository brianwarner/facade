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

include_once 'includes/header.php';
include_once 'includes/db.php';

list($db,$db_people) = setup_db();

$user = $_SESSION['user'];

$_SESSION = array();
session_destroy();

$query = "INSERT INTO auth_history (user,status)
	VALUES ('" . $user . "','Logged out')";

query_db($db,$query,'Updating history.');

$db->close();
$db_people->close();

echo '<h2>Logging out...</h2><meta http-equiv="refresh" content="0;./">';

?>
