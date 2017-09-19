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

session_start();

?>

<html>
<head>
<title>Facade</title>
<link type="text/css" rel="stylesheet" media="all" href="/style.css">

<?php

$analytics = get_setting($db,"google_analytics");

if ($analytics != "disabled") {

	echo '<!-- Global Site Tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=' .
$analytics . '"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments)};
  gtag(\'js\', new Date());

  gtag(\'config\', \'' . $analytics . '\');
</script>
';

}
?>

<script language="javascript">
	function toggle_projects(source) {
		checkboxes = document.getElementsByName('projects[]');
		for(var i=0, n=checkboxes.length;i<n;i++) {
			checkboxes[i].checked = source.checked;
		}
	}

	function toggle_tags(source) {
		checkboxes = document.getElementsByName('tags[]');
		for(var i=0, n=checkboxes.length;i<n;i++) {
			checkboxes[i].checked = source.checked;
		}
	}

	function toggle_affiliations(source) {
		checkboxes = document.getElementsByName('affiliations[]');
		for(var i=0, n=checkboxes.length;i<n;i++) {
			checkboxes[i].checked = source.checked;
		}
	}

	function custom_input(source,input_id,width) {
		if (source.value=='custom') {
			document.getElementById(input_id).style.visibility='visible';
			source.style.width=width;
		} else {
			document.getElementById(input_id).style.visibility='hidden';
			source.style.width='auto';
		}
	}

	function toggle_select(source) {
		radiobuttons = document.getElementsByName('radio_' + source.target.value);
		if (source.target.checked) {
			for(var i=0, n=radiobuttons.length;i<n;i++) {
				radiobuttons[i].removeAttribute('disabled');
			}
			radiobuttons[0].checked = source.target.checked;
		} else {
			for(var i=0, n=radiobuttons.length;i<n;i++) {
				radiobuttons[i].setAttribute('disabled','disabled');
				radiobuttons[i].checked = source.target.checked;
			}
		}
	}
</script>

</head>

<body>

<div id="page-wrapper">

<div id="header-wrapper">

<div id="header">

<span id="site-title">Facade</span><br>
<span id="site-subtitle">See who is actually doing the work in your projects</span>

</div> <!-- #header -->

<div class="menu">
<?php include "menu.php" ?>
</div> <!-- .menu -->

</div> <!-- #header-wrapper -->

<div id="content-wrapper">

<div id="content-title">
<h1><?php echo $title ?></h1>
</div> <!-- #content-title -->

<div id="content">
