#!/usr/bin/python

# Copyright 2016-2017 Brian Warner
#
# This file is part of Facade, and is made available under the terms of the GNU
# General Public License version 2.
# SPDX-License-Identifier:        GPL-2.0
#
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

#### Settings table ####

def create_settings(reset=0):

# Create and populate the default settings table.

	# default settings
	start_date = "2014-01-01";
	working_dir = os.path.dirname(os.path.abspath(__file__))
	repo_directory = os.path.join(working_dir,'../git-repos/')

	if reset:
		clear = "DROP TABLE IF EXISTS settings"

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
		"('start_date','%s'),"
		"('repo_directory','%s'),"
		"('utility_status','Idle'),"
		"('log_level','Quiet'),"
		"('report_date','committer'),"
		"('report_attribution','author'),"
		"('working_author','done'),"
		"('affiliations_processed',current_timestamp(6)),"
		"('aliases_processed',current_timestamp(6))"
		% (start_date,repo_directory))

	cursor.execute(initialize)
	db.commit()

#### Log tables ####

def create_repos_fetch_log(reset=0):

# A new entry is logged every time a repo update is attempted

	if reset:
		clear = "DROP TABLE IF EXISTS repos_fetch_log"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repos_fetch_log ("
		"repos_id INT UNSIGNED NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"date TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

def create_analysis_log(reset=0):

# Log the analysis for each repo

	if reset:
		clear = "DROP TABLE IF EXISTS analysis_log"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS analysis_log ("
		"repos_id INT UNSIGNED NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"date_attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

def create_utility_log(reset=0):

# Create the table that will track the state of the utility script that
# maintains repos and does the analysis.

	if reset:
		clear = "DROP TABLE IF EXISTS utility_log"

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

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS projects ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"name VARCHAR(128) NOT NULL,"
		"description VARCHAR(256),"
		"website VARCHAR(128),"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

def create_repos(reset=0):

# Each project could have multiple repos. When a new repo is added, "status"
# will be set to "New" so that the first action is a git clone.  When it
# succeeds, "status" will be set to "Active" so that subsequent updates use git
# pull. When a repo is deleted, status will be set to "Delete" and it will be
# cleared the next time repo-management.py runs.

	if reset:
		clear = "DROP TABLE IF EXISTS repos"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repos ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"projects_id INT UNSIGNED NOT NULL,"
		"git VARCHAR(256) NOT NULL,"
		"path VARCHAR(256),"
		"name VARCHAR(256),"
		"added TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),"
		"status VARCHAR(32) NOT NULL,"
		"working_commit VARCHAR(40))")

	cursor.execute(create)
	db.commit()

#### Affiliation tables ####

def create_affiliations(reset=0):

# Track which domains/emails should be associated with what organizations. Also
# populate table with some sample entries.

	if reset:
		clear = "DROP TABLE IF EXISTS affiliations"

		cursor_people.execute(clear)
		db_people.commit()

	create = ("CREATE TABLE IF NOT EXISTS affiliations ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"domain VARCHAR (64) NOT NULL,"
		"affiliation VARCHAR (64) NOT NULL,"
		"start_date DATE NOT NULL DEFAULT '1970-01-01',"
		"active BOOL NOT NULL DEFAULT TRUE,"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),"
		"UNIQUE (domain,affiliation,start_date))")

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

		cursor_people.execute(clear)
		db_people.commit()

	create = ("CREATE TABLE IF NOT EXISTS aliases ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"canonical VARCHAR(128) NOT NULL,"
		"alias VARCHAR(128) NOT NULL,"
		"active BOOL NOT NULL DEFAULT TRUE,"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),"
		"UNIQUE (canonical,alias))")

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

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS special_tags ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"email VARCHAR(128) NOT NULL,"
		"start_date DATE NOT NULL,"
		"end_date DATE,"
		"tag VARCHAR(64) NOT NULL,"
		"UNIQUE (email,start_date,end_date,tag))")

	cursor.execute(create)
	db.commit()

#### Analysis tables ####

def create_analysis(reset=0):

# Analysis data

	if reset:
		clear = "DROP TABLE IF EXISTS analysis_data"

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
		"date_attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

#### Cache tables ####

def create_unknown_caches(reset=0):

# After each facade-worker run, any unknown contributors and their email domain
# are cached in this table to make them easier to fetch later.

	if reset:
		clear = "DROP TABLE IF EXISTS unknown_cache"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS unknown_cache ("
		"type VARCHAR(10) NOT NULL,"
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"domain VARCHAR(128),"
		"added BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

def create_web_caches(reset=0):

# After each facade-worker run, cache results used in summary tables to decrease
# load times when the database gets large. Also enables a read-only kiosk mode.
# Must store separate data for monthly and annual data because while you can
# easily add monthly LoC and patch data and get meaningful annual stats,
# contributors can't be added across months to get to total annual number.

	# Monthly caches by project

	if reset:
		clear = "DROP TABLE IF EXISTS project_monthly_cache"

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
		"patches BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

	# Annual caches by project

	if reset:
		clear = "DROP TABLE IF EXISTS project_annual_cache"

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
		"patches BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

	# Monthly caches by repo

	if reset:
		clear = "DROP TABLE IF EXISTS repo_monthly_cache"

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
		"patches BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

	# Annual caches by repo

	if reset:
		clear = "DROP TABLE IF EXISTS repo_annual_cache"

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
		"patches BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

#### Authentication tables ####

def create_auth(reset=0):

# These are used for basic user authentication and account history.

	if reset:
		clear = "DROP TABLE IF EXISTS auth"

		cursor.execute(clear)
		db.commit()

		clear = "DROP TABLE IF EXISTS auth_history"

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

	print "\nSetting administrator credentials.\n"

	while not user:
		user = raw_input(' User: ').strip()

	while not email:
		email = raw_input(' Email: ').strip()

	while not hashed:
		password = ''
		conf_password = ''

		while not password:
			password = getpass.getpass(' Password: ').strip()

		while not conf_password:
			conf_password = getpass.getpass(' Confirm password: ').strip()

		if password == conf_password:
			hashed = bcrypt.hashpw(password,bcrypt.gensalt())
		else:
			print "Passwords do not match.\n"

	query = ("INSERT INTO auth (user,email,password)"
		"VALUES ('%s','%s','%s')" % (user,email,hashed))

	cursor.execute(query)
	db.commit()

	query = ("INSERT INTO auth_history (user,status)"
		"VALUES ('%s','Created')" % user)

	cursor.execute(query)
	db.commit()

# ==== The real program starts here ==== #

# First make sure the database files have been setup

working_dir = os.path.dirname(os.path.abspath(__file__))

print ("========== Facade database setup  ==========\n\n"
	"What do you want to do?\n"
	" (C)reate database config files and initialize tables. Optionally create database and user.\n"
	" (I)nitialize tables only. This will clear any existing data.\n"
	" (U)pdate database while preserving settings, projects, and repos.\n"
	" (R)eset admin credentials.\n")

action = raw_input('(c/i/u/r): ').strip()

if action.lower() == 'c':

	print ("========== Creating database credential files ==========\n\n"
		"This will overwrite any existing db.py and creds.php files.\n"
		"If you do not do this, the existing files will be used.\n"
		"Create new setup files?\n")

	confirm_creds = raw_input('yes/no: ').strip().lower()

	if not confirm_creds:
		confirm_creds = 'no'

	if confirm_creds == 'yes':

		print "\n===== Facade database user information =====\n"

		db_user = raw_input('Facade database username (leave blank for random): ').strip()
		db_pass = getpass.getpass('Facade database password (leave blank for random): ').strip()

		if not db_user:
			db_user = ''.join((random.choice(string.letters+string.digits)) for x in range(16))

		if not db_pass:
			db_pass = ''.join((random.choice(string.letters+string.digits)) for x in range(16))

		print ("\nShould Facade create this user? (requires root, "
			"not needed if the user already exists)\n")

		create_user = raw_input('yes/no (default yes): ').strip()

		if not create_user:
			create_user = 'yes'

		print "\n===== Database information =====\n"

		db_host = raw_input('Database host (default: localhost): ').strip()

		if not db_host:
			db_host = 'localhost'

		db_name = raw_input('Database name (leave blank for random): ').strip()

		if not db_name:
			db_name = 'facade_'+''.join((random.choice(string.letters+string.digits)) for x in range(16))

		print ("\nShould Facade create the database? (requires root, "
			"not needed if the database already exists and uses utf8mb4)\n")

		create_db = raw_input('yes/no (default yes): ').strip()

		if not create_db:
			create_db = 'yes'

		print "\nShould Facade use a different database for affiliations and aliases?\n"

		people_db = raw_input('yes/no (default no): ').strip()

		if not people_db:
			people_db = 'no'

		if people_db.lower() == 'yes':

			db_user_people = raw_input('Affiliations and aliases database username (leave blank for random): ').strip()
			db_pass_people = getpass.getpass('Affiliations and aliases database password (leave blank for random): ').strip()

			if not db_user_people:
				db_user_people = ''.join((random.choice(string.letters+string.digits)) for x in range(16))

			if not db_pass_people:
				db_pass_people = ''.join((random.choice(string.letters+string.digits)) for x in range(16))

			print ("\nShould Facade create this user? (requires root, "
				"not needed if the user already exists)\n")

			create_user_people = raw_input('yes/no (default yes): ').strip()

			if not create_user_people:
				create_user_people = 'yes'

			print "\n===== Affiliations and aliases database information =====\n"

			db_host_people = raw_input('Affiliations and aliases database host (default: localhost): ').strip()

			if not db_host_people:
				db_host_people = 'localhost'

			db_name_people = raw_input('Affiliations and aliases database name (leave blank for random): ').strip()

			if not db_name_people:
				db_name_people = 'facade_people_'+''.join((random.choice(string.letters+string.digits)) for x in range(16))

			print ("\nShould Facade create the affiliations and aliases database? (requires root, "
				"not needed if the database already exists and uses utf8mb4)\n")

			create_db_people = raw_input('yes/no (default yes): ').strip()

			if not create_db_people:
				create_db_people = 'yes'

		else:

			print "\nUsing main Facade database to store affiliations and aliases\n"

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
				print 'Could not connect to database as root'
				sys.exit(1)

			if create_db.lower() == 'yes':

				try:
					create_database = ("CREATE DATABASE IF NOT EXISTS %s "
						"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
						% db_name)

					root_cursor.execute(create_database)
					root_db.commit()

				except:
					print 'Could not create database: %s' % db_name
					sys.exit(1)

			if create_db_people.lower() == 'yes':

				try:
					create_database = ("CREATE DATABASE IF NOT EXISTS %s "
						"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
						% db_name_people)

					root_cursor.execute(create_database)
					root_db.commit()

				except:
					print 'Could not create database: %s' % db_name
					sys.exit(1)

			if create_user.lower() == 'yes':

				try:
					create_user = ("CREATE USER IF NOT EXISTS '%s' IDENTIFIED BY '%s'"
						% (db_user,db_pass))

					root_cursor.execute(create_user)
					root_db.commit()

					grant_privileges = ("GRANT ALL PRIVILEGES ON %s.* to %s"
						% (db_name,db_user))

					root_cursor.execute(grant_privileges)
					root_db.commit()

					flush_privileges = ("FLUSH PRIVILEGES")

					root_cursor.execute(flush_privileges)
					root_db.commit()

				except:
					print 'Could not create user and grant privileges: %s' % db_user
					sys.exit(1)

			if create_user_people.lower() == 'yes':

				try:
					create_user = ("CREATE USER IF NOT EXISTS '%s' IDENTIFIED BY '%s'"
						% (db_user_people,db_pass_people))

					root_cursor.execute(create_user)
					root_db.commit()

					grant_privileges = ("GRANT ALL PRIVILEGES ON %s.* to %s"
						% (db_name_people,db_user_people))

					root_cursor.execute(grant_privileges)
					root_db.commit()

					flush_privileges = ("FLUSH PRIVILEGES")

					root_cursor.execute(flush_privileges)
					root_db.commit()

				except:
					print 'Could not create user and grant privileges: %s' % db_user
					sys.exit(1)

			root_cursor.close()
			root_db.close()

		db_values = {'db_user': db_user,
			'db_pass': db_pass,
			'db_name': db_name,
			'db_host': db_host,
			'db_user_people': db_user_people,
			'db_pass_people': db_pass_people,
			'db_name_people': db_name_people,
			'db_host_people': db_host_people}


		db_py_template_loc = os.path.join(working_dir,'db.py.template')
		db_py_loc = os.path.join(working_dir,'db.py')
		creds_php_template_loc = os.path.join(working_dir,'../includes/creds.php.template')
		creds_php_loc = os.path.join(working_dir,'../includes/creds.php')

		db_py_template = string.Template(open(db_py_template_loc).read())

		db_py_file = open(db_py_loc,'w')
		db_py_file.write(db_py_template.substitute(db_values))
		db_py_file.close()

		creds_php_template = string.Template(open(creds_php_template_loc).read())

		creds_php_file = open(creds_php_loc,'w')
		creds_php_file.write(creds_php_template.substitute(db_values))
		creds_php_file.close()

		print '\nDatabase setup complete\n'

try:
    imp.find_module('db')
    from db import db,db_people,cursor,cursor_people
except:
    sys.exit("Can't find db.py.")

if action.lower() == 'i' or action.lower() == 'c':

	print ("========== Initializing database tables ==========\n\n"
		"This will set up your tables, and will clear any existing data.\n"
		"Are you sure?\n")

	confirm = raw_input('yes/no: ')

	if not confirm:
		confirm = 'no'

	if confirm == "yes":
		print "\nSetting up database tables.\n"

		create_settings('clear')

		create_repos_fetch_log('clear')
		create_analysis_log('clear')
		create_utility_log('clear')

		create_projects('clear')
		create_repos('clear')

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

			clear_affiliations = raw_input('keep/clear (default keep): ').strip().lower()

			if clear_affiliations == 'clear':
				create_affiliations('clear')
			else:
				print '\nLeaving affiliations data as it is.\n'
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

			clear_aliases = raw_input('keep/clear (default keep): ').strip().lower()

			if clear_aliases == 'clear':
				create_aliases('clear')
			else:
				print '\nLeaving alias data as it is.\n'
		else:
			create_aliases('clear')


		create_auth('clear')

	else:
		print "\nExiting without doing anything\n."

elif action.lower() == 'u':

	print ("========== Updating database tables ==========\n\n"
		"This will attempt to add database tables while preserving your major settings.\n"
		"It will reset your analysis data, which means it will be rebuilt the next time\n"
		"facade-worker.py runs. This minimizes the risk of stale data.\n\n"
		"This may or may not work. Are you sure you want to continue?\n")

	confirm = raw_input('(yes): ')

	if confirm.lower() == "yes":
		print "\nAttempting update.\n"

		create_repos_fetch_log()
		create_analysis_log()
		create_utility_log()

		create_projects()
		create_repos()

		create_affiliations('clear')
		create_aliases('clear')
		create_excludes()
		create_special_tags()

		create_analysis('clear')

		create_unknown_caches('clear')
		create_web_caches('clear')

	else:
		print "\nExiting without doing anything.\n"

elif action.lower() == 'r':

	print ("========== Resetting admin credentials ==========\n\n"
		"Ok, so you forgot your password. It happens to the best of us.\n"
		"Are you sure you want to reset the admin credentials?\n")

	confirm = raw_input('(yes): ')

	if confirm.lower() == "yes":

		create_auth('clear')

	else:
		print "\nExiting without doing anything.\n"

else:

	print "\nExiting without doing anything.\n"
