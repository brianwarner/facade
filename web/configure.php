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

$title = "Configuration";

include_once "includes/db.php";

list($db,$db_people) = setup_db();

include_once "includes/header.php";

// Check if user is authenticated.  If not, bounce to login page
if (!$_SESSION['access_granted']) {
	echo '<meta http-equiv="refresh" content="0;/user">';
	die;
}

if ($_SERVER["REQUEST_METHOD"] == "POST") {

	$setting = sanitize_input($db,$_POST["setting"],32);

	if ($_POST["confirmedit"]) {

		echo '<div class="content-block"><form action="configure" id="editsettings"
			method="POST"><input type="hidden" name="setting" value="' . $setting . '">';

		if ($setting == "start_date") {

			echo '<h2>Edit date that analysis begins</h2>
				<p><strong>Note:</strong> Changing this will affect your entire
				database, as current data outside the date range will be
				dropped. New dates will be rebuilt.</p>

				<p>Changes will take effect the next time facade-worker.py is
				run.</p>

				<p>Begin on a specific date (yyyy-mm-dd):
				<span class="text"><input type="text" name="value"></span></p>';

		} elseif ($setting == "repo_directory") {

			echo '<h2>Where are you keeping the data?</h2>
				<p><strong>Note:</strong> You should pause your repo maintenance
				cron job until this is set. If you are moving your repositories,
				copy them to the new location and then change this. Changing
				this setting will not move the repos automatically; you must do
				that yourself.  Afterwards, make sure you run the maintenance
				script at least once before the daily analysis to ensure
				everything was found and updated properly.</p>

				<p>System path to git repository directory:
				<span class="text"><input type="text" name="value"></span></p>

				<p><input type="checkbox" name="rebuild_repos"> Re-clone all git
				repos at new location instead of moving existing repos. Will not
				cause you to lose analysis data.</p>';

		} elseif ($setting == "log_level") {

			echo '<h2>How much info do you want to collect?</h2>
				<p><label><input type="radio" name="log_level_radio"
				value="Quiet" id="log_level_quiet" checked="checked">Only log
				errors.</label></p>

				<p><label><input type="radio" name="log_level_radio"
				value="Info" id="log_level_info"> Information on analysis,
				including when everything starts and finishes.</label></p>

				<p><label><input type="radio" name="log_level_radio"
				value="Verbose" id="log_level_verbose"> Generate information on
				repo and project-specific activity.</label></p>

				<p><label><input type="radio" name="log_level_radio"
				value="Debug" id="log_level_debug"> Log everything, which will
				generate a lot of information. Only use this when you are
				debugging.</label></p>';

		} elseif ($setting == "report_date") {

			echo '<h2>What date should be used for web-based reports?</h2>

				<p><strong>Note:</strong> This setting determines how commits
				are organized in the web UI. They can either be counted by the
				author date (when the patch was created) or the committer date
				(when the patch was applied). Committer date may be more
				meaningful in general situations.</p>

				<p>This does not affect data exported as a CSV, which will
				always contain both fields. However, to see the changes you will
				need to re-run facade-worker.py</p>

				<p><label><input type="radio" name="date_radio" value="author"
				id="author_date" checked="checked">Author</label></p>

				<p><label><input type="radio" name="date_radio" value="committer"
				id="committer_date">Committer</label></p>';

		} elseif ($setting == "report_attribution") {

			echo '<h2>What email/affiliation should be used for web-based reports?</h2>

				<p><strong>Note:</strong> This setting determines how commits
				are organized in the web UI. They can either be organized by
				author email (who created the patch) or the committer email
				(who applied the patch).</p>

				<p>This does not affect data exported as a CSV, which will
				always contain both fields. However, to see the changes you will
				need to re-run facade-worker.py</p>

				<p><label><input type="radio" name="attribution_radio" value="author"
				id="author_email" checked="checked">Author</label></p>

				<p><label><input type="radio" name="attribution_radio" value="committer"
				id="committer_email">Committer</label></p>';

		} elseif ($setting == "google_analytics") {

			echo '<h2>What is your Google Analytics tracking code?</h2>

				<p><strong>Note:</strong> This can be found in your Google Analytics
				account, and is	usually in the format <i>UA-#######-#</i>. Copy and
				paste that code here.</p>

				<p>To remove the tracking code, leave this field blank.</p>

				<p>Google Analytics tracking code:
				<span class="text"><input type="text" name="google_analytics"></span></p>';

		} elseif ($setting == "update_frequency") {

			echo '<h2>How often should Facade attempt to update analysis data?</h2>

				<p><strong>Note:</strong> This determines the frequency at which Facade
				analyzes a repo. You must also have a cron job which runs facade-worker.py
				on at least the same frequency as this setting.</p>

				<p>A shorter interval here means more network traffic, as Facade will check
				for updates in the upstream repos each time. However, it also means
				analysis jobs will finish more quickly and the stats will be less out of
				date.</p>

				<p>Newly added repos will always be cloned the next time
				facade-worker.py runs, and repos which have been manually triggered will
				also run. For this reason, a (much) higher cron job frequency is
				recommended, so you see your changes sooner.</p>

				<p><label><input type="radio" name="update_radio" value="4"
				id="update_4">Every 4 hours</label></p>

				<p><label><input type="radio" name="update_radio" value="12"
				id="update_12">Every 12 hours</label></p>

				<p><label><input type="radio" name="update_radio" value="24"
				id="update_24" checked="checked">Every 24 hours (recommended)</label></p>';

		} elseif ($setting == "results_visibility") {

			echo '<h2>Should the results page be visible to unauthenticated users?</h2>

				<p>This setting adjusts how much anonymous users can see.
				Generating results is computationally intensive and can really
				eat up bandwidth, so you may want to hide the results tab for
				externally facing instances.</p>

				<p>All configuration options will only be available to authenticated
				users, regardless of this setting.</p>

				<p><label><input type="radio" name="access_radio" value="show"
				id="access_true" checked="checked">Show the results tab</label></p>

				<p><label><input type="radio" name="access_radio" value="hide"
				id="access_false">Hide the results tab</label></p>';

		} else {
			echo '<div class="info">Unknown setting.</div>';
		}

		echo '<input type="submit" name="edit" value="Apply"></form></div>';

	} elseif ($_POST["edit"]) {

		$value = sanitize_input($db,$_POST["value"],128);

		if ($setting == "log_level") {
			$value = sanitize_input($db,$_POST["log_level_radio"],10);
		}

		if ($setting == "report_date") {
			$value = sanitize_input($db,$_POST["date_radio"],11);
		}

		if ($setting == "report_attribution") {
			$value = sanitize_input($db,$_POST["attribution_radio"],11);
		}

		if ($setting == "google_analytics") {

			if (strlen($_POST["google_analytics"]) == 0) {
				$value = 'disabled';
			} else {
				$value = sanitize_input($db,$_POST["google_analytics"],15);
			}
		}

		if ($setting == "update_frequency") {
			$value = sanitize_input($db,$_POST["update_radio"],2);
		}

		if ($setting == "results_visibility") {
			$value = sanitize_input($db,$_POST["access_radio"],4);
		}

		if ($value) {

			$safe_setting = TRUE;

			// Gripe if the new start date will cause a null date range
			if ($setting == "start_date") {

				if ($value > date("Y-m-d",time())) {

					echo '<div class="info"><p>Check your start date,
						as it appears to be in the future.</p></div>';
				}
			}

			if ($setting == "repo_directory") {

				if (sanitize_input($db,$_POST["rebuild_repos"],1)) {
					$query = "UPDATE repos SET status='New'";
					query_db($db,$query,"Preparing to rebuid repos");
				}

				if (substr($value,0,1) != '/') {

					echo '<div class="info"><p><strong>WARNING:</strong><br>You
						appear to be using a relative path. This is not
						safe.</p></div>';
					$safe_setting = FALSE;
				}

				if ($value == '/') {

					echo '<div class="info"><p><strong>WARNING:</strong><br>You
						have set your repo directory to root. This is ok if you
						<i>really</i> know what you are doing, but you could
						also <i>really</i> screw up your system.</p><p>You have
						been warned.</p></div>';

				}

				if (substr($value,-1) != '/') {
					$value = $value . "/";
				}
			}

			if ($safe_setting) {

				$query = "INSERT INTO settings (setting,value)
					VALUES ('" . $setting . "','" . $value . "')";
				query_db($db,$query,"Updating settings");

			}

		} else {

			echo '<div class="info"><p>Cowardly refusing to apply an empty
				setting.</p></div>';
		}

	}
}

$query = "SELECT last_modified
	FROM settings
	WHERE setting='utility_status'
	ORDER BY last_modified DESC LIMIT 1";

$result = query_db($db,$query,"Get the time of the last status change");

$last_modified = strtotime($result->fetch_assoc()['last_modified']);

echo '<div class="content-block">

<div class="sub-block">
<h2>Status</h2>
<table>

<tr>
<td class="half"><strong>Current status of facade-worker
script</strong></td>
<td class="half">' . stripslashes(get_setting($db,"utility_status")) . ' since
' . date("F j, Y", $last_modified) . ' at ' . date("H:i", $last_modified) .'</td>
</tr>

</table>

</div> <!-- .sub-block -->

<div class="sub-block">

<h2>Data collection and display</h2>

<table>

<tr>
<td class="half"><div class="detail"><strong>Analyze patches committed after this date</strong>
<span class="detail-text"><i>format: yyyy-mm-dd<br>default: 2000-01-01</i></td>
<td class="half">' . get_setting($db,"start_date") .
edit_setting_button("start_date") . '</span></div></td>
</tr>

<tr>
<td class="half"><div class="detail"><strong>Use this email when generating
reports that are displayed on the website</strong>
<span class="detail-text"><i>format: author, committer<br>default: author</i></td>
<td class="half">' . get_setting($db,"report_attribution") .
edit_setting_button("report_attribution") . '</span></div></td>
</tr>

<tr>
<td class="half"><div class="detail"><strong>Use this date when generating
reports that are displayed on the website</strong>
<span class="detail-text"><i>format: author, committer<br>default: committer</i></td>
<td class="half">' . get_setting($db,"report_date") .
edit_setting_button("report_date") . '</span></div></td>
</tr>

<tr>
<td class="half"><div class="detail"><strong>Display the results page for
unauthenticated users</strong>
<span class="detail-text"><i>format: true, false<br>default: true</i></td>
<td class="half">' . get_setting($db,"results_visibility") .
edit_setting_button("results_visibility") . '</span></div></td>
</tr>
</table>

</div> <!-- .sub-block -->

<div class="sub-block">

<h2>System</h2>

<table>
<tr>
<td class="half"><div class="detail"><strong>Location of git repos (must be writable by user account doing
the analysis)</strong><span class="detail-text"><i>format: system path<br>default:
/opt/facade/git-trees/</i></td>
<td class="half">' . get_setting($db,"repo_directory") .
edit_setting_button("repo_directory") . '</span></div></td>
</tr>
<tr>
<td class="half"><div class="detail"><strong>Hours between attempted updates</strong><span class="detail-text"><i>default: 24 hours</i></td>
<td class="half">' . get_setting($db,"update_frequency") . edit_setting_button("update_frequency") .'</span></div></td>
</tr>
<tr>
<td class="half"><div class="detail"><strong>Log level</strong><span class="detail-text"><i>default: Quiet</i></td>
<td class="half">' . get_setting($db,"log_level") . edit_setting_button("log_level") .
'</span></div></td>
</tr>
<tr>
<td class="half"><div class="detail"><strong>Database version</strong><span class="detail-text"><i>Run setup.py and choose "u" to update.</i></td>
<td class="half">' . get_setting($db,"database_version") . '</span></div></td>
</tr>
</table>

</div> <!-- .sub-block -->

<div class="sub-block">

<h2>Google Analytics</h2>

<table>
<tr>
<td class="half"><div class="detail"><strong>Google Analytics tracking
ID</strong><span class="detail-text"><i>Typically something like
UA-#######-#</i></span></div></td>
<td class="half">' . get_setting($db,"google_analytics") .
edit_setting_button("google_analytics") . '</td>
</tr>
</table>

</div> <!-- .sub-block -->

<div class="sub-block">

<h2>Import / Export</h2>

<p>When importing projects and repos, <strong>all existing project and
repo data will be removed</strong>. This is to ensure the mappings between
project and repos remain consistent.</p>

<table>
<tr><td class="quarter">Project definitions</td>
<td class="quarter">
<form action="manage" method="post" enctype="multipart/form-data">
<input type="submit" name="export_projects_csv" value="Export"></td>
<td class="half"><input type="file" name="import_file" id="import_file">&nbsp;
<input type="submit" name="import_projects_csv" value="Import"></form></td></tr>
<tr><td>Repo definitions</td>
<td>
<form action="manage" method="post" enctype="multipart/form-data">
<input type="submit" name="export_repos_csv" value="Export"</td>
<td><input type="file" name="import_file" id="import_file">&nbsp;
<input type="submit" name="import_repos_csv" value="Import">&nbsp;or&nbsp;
<input type="submit" name="import_clone_repos_csv" value="Import and clone"><br>
</form></td></tr>
<tr><td>Aliases</td>
<td>
<form action="manage" method="post" enctype="multipart/form-data">
<input type="submit" name="export_aliases_csv" value="Export"</td>
<td><input type="file" name="import_file" id="import_file">&nbsp;
<input type="submit" name="import_aliases_csv" value="Import"></form></td></tr>
<tr><td>Affiliations</td>
<td><form action="manage" method="post" enctype="multipart/form-data">
<input type="submit" name="export_affiliations_csv" value="Export"</td>
<td><input type="file" name="import_file" id="import_file">&nbsp;
<input type="submit" name="import_affiliations_csv" value="Import"></form></td></tr>
<tr><td>Tags</td>
<td><form action="manage" method="post" enctype="multipart/form-data">
<input type="submit" name="export_tags_csv" value="Export"</td>
<td><input type="file" name="import_file" id="import_file">&nbsp;
<input type="submit" name="import_tags_csv" value="Import"></form></td></tr>
<tr><td>Facade settings</td>
<td><form action="manage" method="post" enctype="multipart/form-data">
<input type="submit" name="export_settings_csv" value="Export"</td>
<td><input type="file" name="import_file" id="import_file">&nbsp;
<input type="submit" name="import_settings_csv" value="Import"></form></td></tr>
</table>

</div> <!-- .sub-block -->

</div> <!-- .content-block -->';

include_once "includes/footer.php";
$db->close();
$db_people->close();
?>
