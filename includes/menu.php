<?php

/*
* Copyright 2016-2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/


echo '<div id="menu-item-wrapper">

<span class="menu-item"><a href="./">Home</a></span>
<span class="menu-item"><a href="projects">Projects</a></span>
<span class="menu-item"><a href="repositories">Repositories</a></span>';
if ($_SESSION['access_granted']) {
	echo '<span class="menu-item"><a href="people">People</a></span>
<span class="menu-item"><a href="tags">Tags</a></span>';
}
echo '<span class="menu-item"><a href="results">Results</a></span>';

if ($_SESSION['access_granted']) {
	echo '<span class="menu-item"><a href="configure">Configure</a></span>
		<span class="menu-item logout"><a href="user">' . $_SESSION['user'] . '</a></span>';
}

echo '</div> <!-- #menu-item-wrapper -->';

?>
