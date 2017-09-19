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

$title = "About Facade";

include_once "includes/db.php";
list($db,$db_people) = setup_db();
include_once "includes/header.php";

echo '<div class="content-block">

<p>Facade is open source software, licensed under Apache 2.0. If you have changes,
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
