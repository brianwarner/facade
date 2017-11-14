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


echo '<div id="menu-item-wrapper">

<span class="menu-item"><a href="./">Home</a></span>
<span class="menu-item"><a href="projects">Projects</a></span>
<span class="menu-item"><a href="repositories">Repositories</a></span>';
if ($_SESSION['access_granted']) {
	echo '<span class="menu-item"><a href="people">People</a></span>
<span class="menu-item"><a href="tags">Tags</a></span>';
}

if ((get_setting($db,'results_visibility') == 'show') ||
	($_SESSION['access_granted'])) {

	echo '<span class="menu-item"><a href="results">Results</a></span>';
}

if ($_SESSION['access_granted']) {
	echo '<span class="menu-item"><a href="configure">Configure</a></span>
		<span class="menu-item logout"><a href="user">' . $_SESSION['user'] . '</a></span>';
}

echo '</div> <!-- #menu-item-wrapper -->';

?>
