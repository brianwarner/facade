<?php

/*
* Copyright 2016-2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

$title = "About Facade";

include_once "includes/header.php";
include_once "includes/db.php";
list($db,$db_people) = setup_db();

echo '<div class="content-block">

<p>Facade is open source software, licensed under GPL v2. If you have changes,
fixes, or improvements, please consider proposing them back as a patch or pull
request. The project sources can be found at <a
href="https://github.com/brianwarner/facade">https://github.com/brianwarner/facade</a>.
This is also a good place to ask for help.</p>
<p>Facade comes with no warranties, express or implied.</p>

<p>&copy; Brian Warner 2016 - ' . date("Y") . '</p>

</div> <!-- .content-block -->';

include_once "includes/footer.php";

$db->close();
$db_people->close();
?>
