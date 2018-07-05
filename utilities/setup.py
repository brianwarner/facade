#!/usr/bin/python3

# Copyright 2016-2018 Brian Warner
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier:	Apache-2.0

# Create all tables, and initialize the settings table with default values.

import sys
import os.path
import MySQLdb
import getpass
import imp
import bcrypt
from string import Template
import string
import random
import warnings
import configparser

#### Settings table ####

def create_settings(reset=0):

# Create and populate the default settings table.

	# Only increment this when you've added the support to facade-worker.py
	database_version = 7

	# default settings
	start_date = "2014-01-01";
	repo_directory = os.path.join(base_dir,'git-repos/')

	if reset:

		clear = "DROP TABLE IF EXISTS settings"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS settings ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"setting VARCHAR(32) NOT NULL,"
		"value VARCHAR(128) NOT NULL,"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

	initialize = ("INSERT INTO settings (setting,value) VALUES"
		"('start_date',%s),"
		"('repo_directory',%s),"
		"('utility_status','Idle'),"
		"('log_level','Quiet'),"
		"('report_date','committer'),"
		"('report_attribution','author'),"
		"('working_author','done'),"
		"('affiliations_processed',current_timestamp(6)),"
		"('aliases_processed',current_timestamp(6)),"
		"('google_analytics','disabled'),"
		"('update_frequency','24'),"
		"('database_version','%s'),"
		"('results_visibility','show')")

	cursor.execute(initialize, (start_date,repo_directory,database_version))
	db.commit()

#### Log tables ####

def create_repos_fetch_log(reset=0):

# A new entry is logged every time a repo update is attempted

	if reset:
		clear = "DROP TABLE IF EXISTS repos_fetch_log"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repos_fetch_log ("
		"repos_id INT UNSIGNED NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"date TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),"
		"INDEX `repos_id,status` (repos_id,status))")

	cursor.execute(create)
	db.commit()

def create_analysis_log(reset=0):

# Log the analysis for each repo

	if reset:
		clear = "DROP TABLE IF EXISTS analysis_log"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS analysis_log ("
		"repos_id INT UNSIGNED NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"date_attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),"
		"INDEX `repos_id` (repos_id))")

	cursor.execute(create)
	db.commit()

def create_utility_log(reset=0):

# Create the table that will track the state of the utility script that
# maintains repos and does the analysis.

	if reset:
		clear = "DROP TABLE IF EXISTS utility_log"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS utility_log ("
		"id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"level VARCHAR(8) NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

#### Project and repo tables ####

def create_projects(reset=0):

# Create the table that tracks high level project descriptions

	if reset:
		clear = "DROP TABLE IF EXISTS projects"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS projects ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"name VARCHAR(128) NOT NULL,"
		"description VARCHAR(256),"
		"website VARCHAR(128),"
		"recache BOOL DEFAULT TRUE,"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

def create_repos(reset=0):

# Each project could have multiple repos. When a new repo is added, "status"
# will be set to "New" so that the first action is a git clone.  When it
# succeeds, "status" will be changed so that subsequent updates use git
# pull. When it's time to update the repo, "status" will be set to "Update".
# When the repo has been updated, it will be set to "Current". When a repo is
# deleted, status will be set to "Delete" and it will be cleared the next time
# repo-management.py runs.

	if reset:
		clear = "DROP TABLE IF EXISTS repos"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repos ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"projects_id INT UNSIGNED NOT NULL,"
		"git VARCHAR(256) NOT NULL,"
		"path VARCHAR(256),"
		"name VARCHAR(256),"
		"added TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),"
		"status VARCHAR(32) NOT NULL)")

	cursor.execute(create)
	db.commit()

def create_working_commits(reset=0):

# As the analysis proceeds, the commit currently being analyzed will be stored
# in the working_commits table.  If Facade begins an analysis and discovers a
# working commit in the table, it probably means the last run was interrupted
# and the data needs to be purged from the analysis_data table and recalculated.
# This was formerly handled as a single column in the repos table, but by doing
# it this way we can potentially work on multiple commits simultaneously.

	if reset:
		clear = "DROP TABLE IF EXISTS working_commits"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS working_commits ("
		"repos_id INT UNSIGNED NOT NULL,"
		"working_commit VARCHAR(40))")

	cursor.execute(create)
	db.commit()

#### Affiliation tables ####

def create_affiliations(reset=0):

# Track which domains/emails should be associated with what organizations. Also
# populate table with some sample entries.

	if reset:
		clear = "DROP TABLE IF EXISTS affiliations"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor_people.execute(clear)
			db_people.commit()

	create = ("CREATE TABLE IF NOT EXISTS affiliations ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"domain VARCHAR (64) NOT NULL,"
		"affiliation VARCHAR (64) NOT NULL,"
		"start_date DATE NOT NULL DEFAULT '1970-01-01',"
		"active BOOL NOT NULL DEFAULT TRUE,"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),"
		"UNIQUE `domain,affiliation,start_date` (domain,affiliation,start_date),"
		"INDEX `domain,active` (domain,active))")

	cursor_people.execute(create)
	db_people.commit()

	if reset:
		populate = ("INSERT INTO affiliations(domain,affiliation) VALUES "
			"('samsung.com','Samsung'),"
			"('linuxfoundation.org','Linux Foundation'),"
			"('ibm.com','IBM'),"
			"('brian@bdwarner.com','(Hobbyist)')")

		cursor_people.execute(populate)
		db_people.commit()

		populate = ("INSERT INTO affiliations(domain,affiliation,start_date) VALUES "
			"('brian@bdwarner.com','Samsung','2015-07-05'),"
			"('brian@bdwarner.com','The Linux Foundation','2011-01-06'),"
			"('brian@bdwarner.com','IBM','2006-05-20')")

		cursor_people.execute(populate)
		db_people.commit()

def create_aliases(reset=0):

# Store aliases to reduce individuals to one identity, and populate table with
# sample entries

	if reset:
		clear = "DROP TABLE IF EXISTS aliases"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor_people.execute(clear)
			db_people.commit()

	create = ("CREATE TABLE IF NOT EXISTS aliases ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"canonical VARCHAR(128) NOT NULL,"
		"alias VARCHAR(128) NOT NULL,"
		"active BOOL NOT NULL DEFAULT TRUE,"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),"
		"UNIQUE `canonical,alias` (canonical,alias),"
		"INDEX `alias,active` (alias,active))")

	cursor_people.execute(create)
	db_people.commit()

	if reset:
		populate = ("INSERT INTO aliases (canonical,alias) VALUES "
			"('brian@bdwarner.com','brian.warner@samsung.com'),"
			"('brian@bdwarner.com','brian.warner@linuxfoundation.org'),"
			"('brian@bdwarner.com','bdwarner@us.ibm.com')")

		cursor_people.execute(populate)
		db_people.commit()

def create_excludes(reset=0):

# Create the table that will track what should be ignored.

	if reset:
		clear = "DROP TABLE IF EXISTS exclude"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS exclude ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128),"
		"domain VARCHAR(128))")

	cursor.execute(create)
	db.commit()

def create_special_tags(reset=0):

# Entries in this table are matched against email addresses found during
# analysis categorize subsets of people.  For example, people who worked for a
# certain organization who should be categorized separately, to benchmark
# performance against the rest of a company.

	if reset:
		clear = "DROP TABLE IF EXISTS special_tags"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS special_tags ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"email VARCHAR(128) NOT NULL,"
		"start_date DATE NOT NULL,"
		"end_date DATE,"
		"tag VARCHAR(64) NOT NULL,"
		"UNIQUE `email,start_date,tag` (email,start_date,tag))")

	cursor.execute(create)
	db.commit()

#### Analysis tables ####

def create_analysis(reset=0):

# Analysis data

	if reset:
		clear = "DROP TABLE IF EXISTS analysis_data"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS analysis_data ("
		"repos_id INT UNSIGNED NOT NULL,"
		"commit VARCHAR(40) NOT NULL,"
		"author_name VARCHAR(128) NOT NULL,"
		"author_raw_email VARCHAR(128) NOT NULL,"
		"author_email VARCHAR(128) NOT NULL,"
		"author_date VARCHAR(10) NOT NULL,"
		"author_affiliation VARCHAR(128),"
		"committer_name VARCHAR(128) NOT NULL,"
		"committer_raw_email VARCHAR(128) NOT NULL,"
		"committer_email VARCHAR(128) NOT NULL,"
		"committer_date VARCHAR(10) NOT NULL,"
		"committer_affiliation VARCHAR(128),"
		"added INT UNSIGNED NOT NULL,"
		"removed INT UNSIGNED NOT NULL,"
		"whitespace INT UNSIGNED NOT NULL,"
		"filename VARCHAR(4096) NOT NULL,"
		"date_attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),"
		"INDEX `author_email,author_affiliation,author_date` (author_email,author_affiliation,author_date),"
		"INDEX `committer_email,committer_affiliation,committer_date` (committer_email,committer_affiliation,committer_date),"
		"INDEX `repos_id,commit` (repos_id,commit),"
		"INDEX `author_raw_email` (author_raw_email),"
		"INDEX `committer_raw_email` (committer_raw_email),"
		"INDEX `author_affiliation` (author_affiliation),"
		"INDEX `committer_affiliation` (committer_affiliation))")

	cursor.execute(create)
	db.commit()

#### Cache tables ####

def create_unknown_caches(reset=0):

# After each facade-worker run, any unknown contributors and their email domain
# are cached in this table to make them easier to fetch later.

	if reset:
		clear = "DROP TABLE IF EXISTS unknown_cache"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS unknown_cache ("
		"type VARCHAR(10) NOT NULL,"
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"domain VARCHAR(128),"
		"added BIGINT UNSIGNED NOT NULL,"
		"INDEX `type,projects_id` (type,projects_id))")

	cursor.execute(create)
	db.commit()

def create_web_caches(reset=0):

# After each facade-worker run, cache results used in summary tables to decrease
# load times when the database gets large. Also enables a read-only kiosk mode.
# Must store separate data for monthly and annual data because while you can
# easily add monthly LoC and patch data and get meaningful annual stats,
# contributors can't be added across months to get to total annual number.

	# Weekly caches by project

	if reset:
		clear = "DROP TABLE IF EXISTS project_weekly_cache"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS project_weekly_cache ("
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"week TINYINT UNSIGNED NOT NULL,"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL,"
		"INDEX `projects_id,year,affiliation` (projects_id,year,affiliation),"
		"INDEX `projects_id,year,email` (projects_id,year,email),"
		"INDEX `projects_id,affiliation` (projects_id,affiliation),"
		"INDEX `projects_id,email` (projects_id,email))")

	cursor.execute(create)
	db.commit()

	# Monthly caches by project

	if reset:
		clear = "DROP TABLE IF EXISTS project_monthly_cache"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS project_monthly_cache ("
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"month TINYINT UNSIGNED NOT NULL,"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL,"
		"INDEX `projects_id,year,affiliation` (projects_id,year,affiliation),"
		"INDEX `projects_id,year,email` (projects_id,year,email),"
		"INDEX `projects_id,affiliation` (projects_id,affiliation),"
		"INDEX `projects_id,email` (projects_id,email))")

	cursor.execute(create)
	db.commit()

	# Annual caches by project

	if reset:
		clear = "DROP TABLE IF EXISTS project_annual_cache"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS project_annual_cache ("
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL,"
		"INDEX `projects_id,affiliation` (projects_id,affiliation),"
		"INDEX `projects_id,email` (projects_id,email))")

	cursor.execute(create)
	db.commit()

	# Weekly caches by repo

	if reset:
		clear = "DROP TABLE IF EXISTS repo_weekly_cache"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repo_weekly_cache ("
		"repos_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"week TINYINT UNSIGNED NOT NULL,"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL,"
		"INDEX `repos_id,year,affiliation` (repos_id,year,affiliation),"
		"INDEX `repos_id,year,email` (repos_id,year,email),"
		"INDEX `repos_id,affiliation` (repos_id,affiliation),"
		"INDEX `repos_id,email` (repos_id,email))")

	cursor.execute(create)
	db.commit()

	# Monthly caches by repo

	if reset:
		clear = "DROP TABLE IF EXISTS repo_monthly_cache"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repo_monthly_cache ("
		"repos_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"month TINYINT UNSIGNED NOT NULL,"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL,"
		"INDEX `repos_id,year,affiliation` (repos_id,year,affiliation),"
		"INDEX `repos_id,year,email` (repos_id,year,email),"
		"INDEX `repos_id,affiliation` (repos_id,affiliation),"
		"INDEX `repos_id,email` (repos_id,email))")

	cursor.execute(create)
	db.commit()

	# Annual caches by repo

	if reset:
		clear = "DROP TABLE IF EXISTS repo_annual_cache"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repo_annual_cache ("
		"repos_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL,"
		"INDEX `repos_id,affiliation` (repos_id,affiliation),"
		"INDEX `repos_id,email` (repos_id,email))")

	cursor.execute(create)
	db.commit()

#### Authentication tables ####

def create_auth(reset=0):

# These are used for basic user authentication and account history.

	if reset:
		clear = "DROP TABLE IF EXISTS auth"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()

		clear = "DROP TABLE IF EXISTS auth_history"

		# Suppress warnings about tables not existing

		with warnings.catch_warnings():
			warnings.simplefilter("ignore")

			cursor.execute(clear)
			db.commit()


	create = ("CREATE TABLE IF NOT EXISTS auth ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"user VARCHAR(64) UNIQUE NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"password VARCHAR(64) NOT NULL,"
		"created TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

	create = ("CREATE TABLE IF NOT EXISTS auth_history ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"user VARCHAR(64) NOT NULL,"
		"status VARCHAR(96) NOT NULL,"
		"attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

	user = ''
	email = ''
	hashed = ''

	print("\nSetting administrator credentials.\n")

	while not user:
		user = input(' User: ').strip()

	while not email:
		email = input(' Email: ').strip()

	while not hashed:
		password = ''
		conf_password = ''

		while not password:
			password = getpass.getpass(' Password: ').strip()

		while not conf_password:
			conf_password = getpass.getpass(' Confirm password: ').strip()

		if password == conf_password:
			hashed = bcrypt.hashpw(password.encode('utf8'),bcrypt.gensalt())
		else:
			print("Passwords do not match.\n")

	query = ("INSERT INTO auth (user,email,password)"
		"VALUES (%s,%s,%s)")

	cursor.execute(query, (user,email,hashed))
	db.commit()

	query = ("INSERT INTO auth_history (user,status)"
		"VALUES (%s,'Created')")

	cursor.execute(query, (user, ))
	db.commit()

# ==== The real program starts here ==== #

# First make sure the database file has been setup

base_dir = os.path.dirname(os.path.abspath(__file__))[:-9]

print ("========== Facade database setup  ==========\n\n"
	"What do you want to do?\n"
	" (C)reate database config file and initialize tables. Optionally create database and user.\n"
	" (I)nitialize tables only. This will clear any existing data.\n"
	" (P)rint the configuration instructions for setting up Apache.\n"
	" (R)eset admin credentials.\n")

action = input('(c/i/p/r): ').strip()

if action.lower() == 'c':

	print ("========== Creating database credentials file ==========\n\n"
		"This will overwrite any existing db.cfg file.\n"
		"If you do not do this, the existing file will be used.\n"
		"Create new setup file?\n")

	confirm_creds = input('yes/no: ').strip().lower()

	if not confirm_creds:
		confirm_creds = 'no'

	if confirm_creds == 'yes':

		print("\n===== Facade database user information =====\n")

		db_user = input('Facade database username (leave blank for random): ').strip()
		db_pass = getpass.getpass('Facade database password (leave blank for random): ').strip()

		if not db_user:
			db_user = ''.join((random.choice(string.ascii_letters+string.digits)) for x in range(16))

		if not db_pass:
			db_pass = ''.join((random.choice(string.ascii_letters+string.digits)) for x in range(16))

		print ("\nShould Facade create this user? (requires root, "
			"not needed if the user already exists)\n")

		create_user = input('yes/no (default yes): ').strip()

		if not create_user:
			create_user = 'yes'

		print("\n===== Database information =====\n")

		db_host = input('Database host (default: localhost): ').strip()

		if not db_host:
			db_host = 'localhost'

		db_name = input('Database name (leave blank for random): ').strip()

		if not db_name:
			db_name = 'facade_'+''.join((random.choice(string.ascii_letters+string.digits)) for x in range(16))

		print ("\nShould Facade create the database? (requires root, "
			"not needed if the database already exists and uses utf8mb4)\n")

		create_db = input('yes/no (default yes): ').strip()

		if not create_db:
			create_db = 'yes'

		print("\nShould Facade use a different database for affiliations and aliases?\n")

		people_db = input('yes/no (default no): ').strip()

		if not people_db:
			people_db = 'no'

		if people_db.lower() == 'yes':

			db_user_people = input('Affiliations and aliases database username (leave blank for random): ').strip()
			db_pass_people = getpass.getpass('Affiliations and aliases database password (leave blank for random): ').strip()

			if not db_user_people:
				db_user_people = ''.join((random.choice(string.ascii_letters+string.digits)) for x in range(16))

			if not db_pass_people:
				db_pass_people = ''.join((random.choice(string.ascii_letters+string.digits)) for x in range(16))

			print ("\nShould Facade create this user? (requires root, "
				"not needed if the user already exists)\n")

			create_user_people = input('yes/no (default yes): ').strip()

			if not create_user_people:
				create_user_people = 'yes'

			print("\n===== Affiliations and aliases database information =====\n")

			db_host_people = input('Affiliations and aliases database host (default: localhost): ').strip()

			if not db_host_people:
				db_host_people = 'localhost'

			db_name_people = input('Affiliations and aliases database name (leave blank for random): ').strip()

			if not db_name_people:
				db_name_people = 'facade_people_'+''.join((random.choice(string.ascii_letters+string.digits)) for x in range(16))

			print ("\nShould Facade create the affiliations and aliases database? (requires root, "
				"not needed if the database already exists and uses utf8mb4)\n")

			create_db_people = input('yes/no (default yes): ').strip()

			if not create_db_people:
				create_db_people = 'yes'

		else:

			print("\nUsing main Facade database to store affiliations and aliases\n")

			db_user_people = db_user
			db_pass_people = db_pass
			db_host_people = db_host
			db_name_people = db_name
			create_db_people = 'no'
			create_user_people = 'no'


		if (create_db.lower() == 'yes' or create_db_people.lower() == 'yes'
			or create_user.lower() == 'yes' or create_user_people.lower() == 'yes'):

			root_pw = getpass.getpass('\nmysql root password: ').strip()

			try:
				root_db = MySQLdb.connect( host=db_host,
					user = 'root',
					passwd = root_pw,
					charset='utf8mb4')
				root_cursor = root_db.cursor(MySQLdb.cursors.DictCursor)

			except:
				print('Could not connect to database as root')
				sys.exit(1)

			if create_db.lower() == 'yes':

				try:
					create_database = ("CREATE DATABASE IF NOT EXISTS %s "
						"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
						% db_name)

					root_cursor.execute(create_database)
					root_db.commit()

				except:

					print('Could not create database: %s' % db_name)
					sys.exit(1)

			if create_db_people.lower() == 'yes':

				try:
					create_database = ("CREATE DATABASE IF NOT EXISTS %s "
						"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
						% db_name_people)

					root_cursor.execute(create_database)
					root_db.commit()

				except:
					print('Could not create database: %s' % db_name)
					sys.exit(1)

			if create_user.lower() == 'yes':

				try:
					create_user = ("CREATE USER IF NOT EXISTS '%s' IDENTIFIED BY '%s'"
						% (db_user,db_pass))

					root_cursor.execute(create_user)
					root_db.commit()

					grant_privileges = ("GRANT ALL PRIVILEGES ON %s.* to '%s'"
						% (db_name,db_user))

					root_cursor.execute(grant_privileges)
					root_db.commit()

					flush_privileges = ("FLUSH PRIVILEGES")

					root_cursor.execute(flush_privileges)
					root_db.commit()

				except:
					print('Could not create user and grant privileges: %s' % db_user)
					sys.exit(1)

			if create_user_people.lower() == 'yes':

				try:
					create_user = ("CREATE USER IF NOT EXISTS '%s' IDENTIFIED BY '%s'"
						% (db_user_people,db_pass_people))

					root_cursor.execute(create_user)
					root_db.commit()

					grant_privileges = ("GRANT ALL PRIVILEGES ON %s.* to '%s'"
						% (db_name_people,db_user_people))

					root_cursor.execute(grant_privileges)
					root_db.commit()

					flush_privileges = ("FLUSH PRIVILEGES")

					root_cursor.execute(flush_privileges)
					root_db.commit()

				except:
					print('Could not create user and grant privileges: %s' % db_user)
					sys.exit(1)

			root_cursor.close()
			root_db.close()

		db_config = configparser.RawConfigParser()

		db_config.add_section('main_database')
		db_config.set('main_database','user',db_user)
		db_config.set('main_database','pass',db_pass)
		db_config.set('main_database','name',db_name)
		db_config.set('main_database','host',db_host)

		db_config.add_section('people_database')
		db_config.set('people_database','user',db_user_people)
		db_config.set('people_database','pass',db_pass_people)
		db_config.set('people_database','name',db_name_people)
		db_config.set('people_database','host',db_host_people)

		with open('db.cfg','w') as db_file:
			db_config.write(db_file)

		db_values = {'db_user': db_user,
			'db_pass': db_pass,
			'db_name': db_name,
			'db_host': db_host,
			'db_user_people': db_user_people,
			'db_pass_people': db_pass_people,
			'db_name_people': db_name_people,
			'db_host_people': db_host_people}

		print('\nDatabase setup complete\n')


try:
	config = configparser.ConfigParser()
	config.read('db.cfg')

	# Read in the people connection info

	db_user = config['main_database']['user']
	db_pass = config['main_database']['pass']
	db_name = config['main_database']['name']
	db_host = config['main_database']['host']

	db = MySQLdb.connect(
		host = db_host,
		user = db_user,
		passwd = db_pass,
		db = db_name,
		charset = 'utf8mb4')

	cursor = db.cursor(MySQLdb.cursors.DictCursor)

	db_user_people = config['people_database']['user']
	db_pass_people = config['people_database']['pass']
	db_name_people = config['people_database']['name']
	db_host_people = config['people_database']['host']

	db_people = MySQLdb.connect(
		host = db_host_people,
		user = db_user_people,
		passwd = db_pass_people,
		db = db_name_people,
		charset = 'utf8mb4')

	cursor_people = db_people.cursor(MySQLdb.cursors.DictCursor)

except:
    sys.exit("Can't find db.cfg.")

if action.lower() == 'i' or action.lower() == 'c':

	print ("========== Initializing database tables ==========\n\n"
		"This will set up your tables, and will clear any existing data.\n"
		"Are you sure?\n")

	confirm = input('yes/no: ')

	if not confirm:
		confirm = 'no'

	if confirm == "yes":
		print("\nSetting up database tables.\n")

		create_settings('clear')

		create_repos_fetch_log('clear')
		create_analysis_log('clear')
		create_utility_log('clear')

		create_projects('clear')
		create_repos('clear')
		create_working_commits('clear')

		create_excludes('clear')
		create_special_tags('clear')

		create_analysis('clear')

		create_unknown_caches('clear')
		create_web_caches('clear')

		# Check if there's info in the affiliations and aliases table

		try:
			check_affiliations = "SELECT NULL FROM affiliations"

			cursor_people.execute(check_affiliations)
			affiliations = list(cursor_people)

		except:
			affiliations = ''

		if affiliations:
			print ('\nThere appears to be data in the affiliations table. If you are\n'
				'sharing the table with another Facade instance, clearing this\n'
				'table will also delete affiliation data for that instance too.\n'
				'Do you want to clear this data, or keep it?\n')

			clear_affiliations = input('keep/clear (default keep): ').strip().lower()

			if clear_affiliations == 'clear':
				create_affiliations('clear')
			else:
				print('\nLeaving affiliations data as it is.\n')
		else:
			create_affiliations('clear')

		try:
			check_aliases = "SELECT NULL FROM aliases"

			cursor_people.execute(check_aliases)
			aliases = list(cursor_people)

		except:
			aliases = ''

		if aliases:
			print ('\nThere appears to be data in the aliases table. If you are\n'
				'sharing the table with another Facade instance, clearing this\n'
				'table will also delete alias data for that instance too.\n'
				'Do you want to clear this data, or keep it?\n')

			clear_aliases = input('keep/clear (default keep): ').strip().lower()

			if clear_aliases == 'clear':
				create_aliases('clear')
			else:
				print('\nLeaving alias data as it is.\n')
		else:
			create_aliases('clear')


		create_auth('clear')

	else:
		print("\nExiting without doing anything.\n")

if action.lower() == 'i' or action.lower() == 'c' or action.lower() == 'p':

	print ("\n========== Generating Apache2 Configs ==========\n")

	print("Step 1: Create a new file in /etc/apache2/sites-available called facade.conf "
		"with the following contents:\n\n"
		"# Start copying here\n"
		"<VirtualHost *:80>\n"
		"	# Auto-generated site config for Facade\n"
		"	ServerAdmin webmaster@localhost\n"
		"	DocumentRoot %s\n"
		"	ErrorLog ${APACHE_LOG_DIR}/error.log\n"
		"	CustomLog ${APACHE_LOG_DIR}/access.log combined\n"
		"</VirtualHost>\n"
		"# End copying here\n\n" % os.path.join(base_dir,'web/'))

	print("Step 2: Add the following lines to /etc/apache2/apache2.conf:\n\n"
		"# Start copying here\n"
		"<Directory %s>\n"
		"	# Auto-generated directory entry for Facade\n"
		"	Options Indexes FollowSymLinks\n"
		"	AllowOverride All\n"
		"	Require all granted\n"
		"</Directory>\n"
		"# End copying here\n\n" % os.path.join(base_dir,'web/'))

	print("Step 3: Run this in the terminal:\n\n"
		"  sudo a2dissite 000-default && sudo a2ensite facade && sudo a2enmod "
		"rewrite && sudo systemctl reload apache2\n\n")

	print("You should now be able to visit http://localhost and see Facade.\n")

elif action.lower() == 'r':

	print ("========== Resetting admin credentials ==========\n\n"
		"Ok, so you forgot your password. It happens to the best of us.\n"
		"Are you sure you want to reset the admin credentials?\n")

	confirm = input('(yes): ')

	if confirm.lower() == "yes":

		create_auth('clear')

	else:
		print("\nExiting without doing anything.\n")

else:

	print("\nExiting without doing anything.\n")
