<?php

/*
* Copyright 2016 Brian Warner
*
* This file is part of Facade, and is made available under the terms of the GNU
* General Public License version 2.
* SPDX-License-Identifier:        GPL-2.0
*/

// Create all tables, and initialize the settings table with default values.

// First make sure the database file has been setup

if (!file_exists("../includes/db.php")) {
	exit("\nIt appears you haven't configured db.php yet. Please do this.\n\n");
}

include_once "../includes/db.php";
$db = setup_db();

echo "\n========== Initializing database tables ==========\n
This will set up your database, and will clear any existing data.

Are you sure you want to do this? (yes/no) ";

$input = fgets(STDIN);
if (strtolower(trim($input)) != 'yes') {
	echo "\nExiting without doing anything.\n\n";
	exit;
}

// Settings table default values:

$start_date = "2000-01-01";
$end_date = "yesterday";
$interval = "daily";
$gitdm = "/opt/gitdm";
$repo_directory = "/opt/facade/git-trees";

// Create the settings table:

$query = "DROP TABLE IF EXISTS settings;
	CREATE TABLE settings (
	id INT AUTO_INCREMENT PRIMARY KEY,
	setting VARCHAR(32) NOT NULL,
	value VARCHAR(128) NOT NULL,
	last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)";

multi_query_db($db,$query,"Create settings table");

// Initialize the settings table:

$query = "INSERT INTO settings (setting,value) VALUES 
	('start_date','$start_date'),
	('end_date','$end_date'),
	('interval','$interval'),
	('gitdm','$gitdm'),
	('repo_directory','$repo_directory'),
	('utility_status','Idle'),
	('log_level','Quiet')";

query_db($db,$query,"Initialize settings table with default data");

// Create the projects table

$query = "DROP TABLE IF EXISTS projects;
	CREATE TABLE projects (
	id INT AUTO_INCREMENT PRIMARY KEY,
	name VARCHAR(64) NOT NULL,
	description VARCHAR(256),
	website VARCHAR(64),
	last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)";

multi_query_db($db,$query,"Create projects table");

// Create the gitdm_configs table

$query = "DROP TABLE IF EXISTS gitdm_configs;
        CREATE TABLE gitdm_configs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        configfile VARCHAR(128) NOT NULL,
        configtype VARCHAR(32) NOT NULL,
	md5sum VARCHAR(32) NOT NULL,
	status VARCHAR(32) NOT NULL,
        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)";

multi_query_db($db,$query,"Create settings table");

/* Create the repos table:

Each project could have multiple repos. When a new repo is added,
	"status" will be set to "New" so that the first action
	is a git clone.  When it succeeds, "status" will be set
	to "Active" so that subsequent updates use git pull. When
	a repo is deleted, status will be set to "Delete" and it
	will be cleared the next time repo-management.py runs.
*/

$query = "DROP TABLE IF EXISTS repos;
	CREATE TABLE repos (
	id INT AUTO_INCREMENT PRIMARY KEY,
	projects_id INT NOT NULL,
	git VARCHAR(256) NOT NULL,
	path VARCHAR(256),
	name VARCHAR(256),
	added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	status VARCHAR(32) NOT NULL
)";

multi_query_db($db,$query,"Create repos table");

/* Create the exclude table:

Each project may have a unique list of domains, emails, or affiliations
	that should be excluded.
*/

$query = "DROP TABLE IF EXISTS exclude;
	CREATE TABLE exclude (
	id INT AUTO_INCREMENT PRIMARY KEY,
	projects_id INT NOT NULL,
	email VARCHAR(64),
	domain VARCHAR(64)
)";

multi_query_db($db,$query,"Create exclude table");

/* Create the fetch log

A new entry is logged every time a repo update is attempted:
	* If the update succeeds, it will be logged as "Success" and gitdm will run.
	* If it fails, it will be logged as "Failed" and gitdm will not run.
	* If a failed repository updates later, gitdm will be run for all "Failed" dates
		and their log status will be updated to "Reconciled".
*/

$query = "DROP TABLE IF EXISTS repos_fetch_log;
	CREATE TABLE repos_fetch_log (
	id INT AUTO_INCREMENT PRIMARY KEY,
	repos_id INT NOT NULL,
	status VARCHAR(16) NOT NULL,
	date_attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)";

multi_query_db($db,$query,"Create repos fetch log table");

/* Create the gitdm log

A new entry is logged every time a gitdm analysis hs been attempted:
	* If gitdm succeeds, it will be logged as "Success".
	* If it fails, it will be logged as "Failed" and gitdm try again next time.
	* If gitdm later succees on a repository that previously failed, the log
		status will be updated to "Reconciled".
*/

$query = "DROP TABLE IF EXISTS gitdm_master;
	CREATE TABLE gitdm_master (
	id BIGINT AUTO_INCREMENT PRIMARY KEY,
	repos_id INT NOT NULL,
	status VARCHAR(128) NOT NULL,
	date_attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	start_date VARCHAR(10)
)";

multi_query_db($db,$query,"Create gitdm master");

// Create the raw data table

$query = "DROP TABLE IF EXISTS gitdm_data;
	CREATE TABLE gitdm_data (
	id BIGINT AUTO_INCREMENT PRIMARY KEY,
	gitdm_master_id BIGINT NOT NULL,
	name VARCHAR(64) NOT NULL,
	email VARCHAR(64) NOT NULL,
	affiliation VARCHAR(64) NOT NULL,
	added INT NOT NULL,
	removed INT NOT NULL,
	changesets INT NOT NULL
)";

multi_query_db($db,$query,"Create raw gitdm data table");

/* Load the stored procedure that will create the temporary calendar table.
	This will be used to determine if there are any gaps in the analysis.
*/

$query = 'DROP PROCEDURE IF EXISTS make_cal_table;
CREATE PROCEDURE make_cal_table(start_date DATE, end_date DATE)
BEGIN
DROP TABLE IF EXISTS cal_table;
CREATE TABLE cal_table(date DATE);
WHILE start_date <= end_date DO
INSERT INTO cal_table (date) VALUES (start_date);
SET start_date = date_add(start_date, INTERVAL 1 DAY);
END WHILE;
END;';

multi_query_db($db,$query,"Create stored procedure");


/* Create the special tags table

Entries in this table are matched against email addresses found by gitdm to
	categorize subsets of people.  For example, people who worked for a
	certain organization who should be categorized separately, to
	benchmark performance against the rest of a company.
*/

$query = "DROP TABLE IF EXISTS special_tags;
	CREATE TABLE special_tags (
	id BIGINT AUTO_INCREMENT PRIMARY KEY,
	email VARCHAR(128) NOT NULL,
	start_date DATE NOT NULL,
	end_date DATE,
	tag VARCHAR(64) NOT NULL
)";

multi_query_db($db,$query,"Create special tags table");

/* Create the utility script log

Entries in this table will track the state of the utility script that maintains
	repos and calls gitdm.
*/

$query = "DROP TABLE IF EXISTS utility_log;
	CREATE TABLE utility_log (
	id BIGINT AUTO_INCREMENT PRIMARY KEY,
	level VARCHAR(8) NOT NULL,
	status VARCHAR(128) NOT NULL,
	attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)";

multi_query_db($db,$query,"Create script logs table");

/* Create the unknown contributor cache table

After each facade-worker run, any unknown contributors and their email domain
are cached in this table to make them easier to fetch later.
*/

$query = "DROP TABLE IF EXISTS unknown_cache;
	CREATE TABLE unknown_cache (
	id INT AUTO_INCREMENT PRIMARY KEY,
	projects_id INT NOT NULL,
	email VARCHAR(64) NOT NULL,
	domain VARCHAR(64),
	added INT NOT NULL
)";

multi_query_db($db,$query,"Create unknown contributor cache table");

/* Create the auth tables

These are used for basic user authentication and account history.
*/

include_once "includes/db.php";
$db = setup_db();

$query = "DROP TABLE IF EXISTS auth;
	CREATE TABLE auth (
	id INT AUTO_INCREMENT PRIMARY KEY,
	user VARCHAR(64) NOT NULL,
	email VARCHAR(64) NOT NULL,
	password VARCHAR(64) NOT NULL,
	created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)";

multi_query_db($db,$query,"Create auth table");

$query = "DROP TABLE IF EXISTS auth_history;
	CREATE TABLE auth_history (
	id INT AUTO_INCREMENT PRIMARY KEY,
	user VARCHAR(64) NOT NULL,
	status VARCHAR(96) NOT NULL,
	attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)";

multi_query_db($db,$query,"Create auth_history table");

/*
Create the administor
*/

$user = "";
$pass = "";
$pass_confirm = "";
$email = "";

while ($user == "") {

	echo "Administrator user name: ";
	$user = trim(fgets(STDIN));

	if ($user == "") {
		echo "Username cannot be empty.\n\n";
	}
}

while (($pass != $pass_confirm) || ($pass == "")) {

	echo "Administrator password: ";
	$pass = trim(fgets(STDIN));

	echo "Confirm password: ";
	$pass_confirm = trim(fgets(STDIN));

	if ($pass == "") {
		echo "Password cannot be empty.\n\n";
	} else if ($pass != $pass_confirm) {
		echo "Passwords do not match.\n\n";
	}
}

while ($email == "") {

	echo "Administrator email: ";
	$email = trim(fgets(STDIN));

	if ($email == "") {
		echo "Email cannot be empty.\n\n";
	}
}

$query = "INSERT INTO auth (user,email,password)
	VALUES ('$user','$email','$pass')";

multi_query_db($db,$query,"Add administrator");

$query = "INSERT INTO auth_history (user,status)
	VALUES ('$user','Created')";

multi_query_db($db,$query,"Log user");

close_db($db);

?>
