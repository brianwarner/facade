<?php

/*
* Copyright 2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:      GPL-2.0
*/

$safe_to_export = TRUE;

if (get_setting($db,'utility_status') != 'Idle') {
	echo '<div class="info">Facade is doing an analysis. Reports will not be
		updated until it finishes.</div>';

	$safe_to_export = FALSE;

} else {

	$find_null_affiliations = "SELECT NULL FROM analysis_data WHERE
		author_affiliation IS NULL OR
		committer_affiliation IS NULL";

	$null_affiliations = query_db($db,$find_null_affiliations,'Finding null affiliations');

	if ($null_affiliations->num_rows > 0) {
		echo '<div class="info">Affiliation or alias information has been changed,
			and these reports are out of date. They will be rebuilt the next
			time Facade does an analysis.</div>';

		$safe_to_export = FALSE;

	}

}

?>
