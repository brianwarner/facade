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
