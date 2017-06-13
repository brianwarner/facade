<?php

/*
* Copyright 2016-2017 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

session_start();

?>

<html>
<head>
<title>Facade</title>
<link type="text/css" rel="stylesheet" media="all" href="/style.css">

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
