#!/usr/bin/python

# Copyright 2016 Brian Warner
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

try:
    imp.find_module('db')
    from db import db,cursor
except:
    sys.exit("Can't find db.py. Have you created it?")

def create_settings(reset=0):

# Create and populate the default settings table.

	# default settings
	start_date = "2000-01-01";
	end_date = "yesterday";
	interval = "daily";
	gitdm = "/opt/gitdm/";
	repo_directory = "/opt/facade/git-trees/";

	if reset:
		clear = "DROP TABLE IF EXISTS settings"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS settings ("
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"setting VARCHAR(32) NOT NULL,"
		"value VARCHAR(128) NOT NULL,"
		"last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

	cursor.execute(create)
	db.commit()

	initialize = ("INSERT INTO settings (setting,value) VALUES"
		"('start_date','%s'),"
		"('end_date','%s'),"
		"('interval','%s'),"
		"('gitdm','%s'),"
		"('repo_directory','%s'),"
		"('utility_status','Idle'),"
		"('log_level','Quiet')"
		% (start_date,end_date,interval,gitdm,repo_directory))

	cursor.execute(initialize)
	db.commit()

	print "Settings table created."

def create_projects(reset=0):

# Create the table that tracks high level project descriptions

	if reset:
		clear = "DROP TABLE IF EXISTS projects"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS projects ("
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"name VARCHAR(64) NOT NULL,"
		"description VARCHAR(256),"
		"website VARCHAR(64),"
		"last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)")

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
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"projects_id INT NOT NULL,"
		"git VARCHAR(256) NOT NULL,"
		"path VARCHAR(256),"
		"name VARCHAR(256),"
		"added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
		"status VARCHAR(32) NOT NULL)")

	cursor.execute(create)
	db.commit()

def create_gitdm_configs(reset=0):

# Create the table that will watch gitdm's map files for changes.

	if reset:
		clear = "DROP TABLE IF EXISTS gitdm_configs"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS gitdm_configs ("
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"configfile VARCHAR(128) NOT NULL,"
		"configtype VARCHAR(32) NOT NULL,"
		"md5sum VARCHAR(32) NOT NULL,"
		"status VARCHAR(32) NOT NULL,"
		"last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)")

	cursor.execute(create)
	db.commit()

def create_excludes(reset=0):

# Create the table that will track what should be ignored.

	if reset:
		clear = "DROP TABLE IF EXISTS exclude"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS exclude ("
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"projects_id INT NOT NULL,"
		"email VARCHAR(64),"
		"domain VARCHAR(64))")

	cursor.execute(create)
	db.commit()

def create_repos_fetch_log(reset=0):

# A new entry is logged every time a repo update is attempted:
#  * If the update succeeds, it will be logged as "Success" and gitdm will run.
#  * If it fails, it will be logged as "Failed" and gitdm will not run.
#  * If a failed repository updates later, gitdm will be run for all "Failed"
#	 dates and their log status will be updated to "Reconciled".

	if reset:
		clear = "DROP TABLE IF EXISTS repos_fetch_log"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repos_fetch_log ("
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"repos_id INT NOT NULL,"
		"status VARCHAR(16) NOT NULL,"
		"date_attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

	cursor.execute(create)
	db.commit()

def create_gitdm_master(reset=0):

# A new entry is logged every time a gitdm analysis hs been attempted:
#  * If gitdm succeeds, it will be logged as "Success".
#  * If it fails, it will be logged as "Failed" and gitdm try again next time.
#  * If gitdm later succees on a repository that previously failed, the log
#	 status will be updated to "Reconciled".

	if reset:
		clear = "DROP TABLE IF EXISTS gitdm_master"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS gitdm_master ("
		"id BIGINT AUTO_INCREMENT PRIMARY KEY,"
		"repos_id INT NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"date_attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
		"start_date VARCHAR(10))")

	cursor.execute(create)
	db.commit()

def create_gitdm_data(reset=0):

# Create the raw data table

	if reset:
		clear = "DROP TABLE IF EXISTS gitdm_data"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS gitdm_data ("
		"id BIGINT AUTO_INCREMENT PRIMARY KEY,"
		"gitdm_master_id BIGINT NOT NULL,"
		"name VARCHAR(64) NOT NULL,"
		"email VARCHAR(64) NOT NULL,"
		"affiliation VARCHAR(64) NOT NULL,"
		"added INT NOT NULL,"
		"removed INT NOT NULL,"
		"changesets INT NOT NULL)")

	cursor.execute(create)
	db.commit()

def create_special_tags(reset=0):

# Entries in this table are matched against email addresses found by gitdm to
# categorize subsets of people.  For example, people who worked for a certain
# organization who should be categorized separately, to benchmark performance
# against the rest of a company.

	if reset:
		clear = "DROP TABLE IF EXISTS special_tags"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS special_tags ("
		"id BIGINT AUTO_INCREMENT PRIMARY KEY,"
		"email VARCHAR(128) NOT NULL,"
		"start_date DATE NOT NULL,"
		"end_date DATE,"
		"tag VARCHAR(64) NOT NULL)")

	cursor.execute(create)
	db.commit()

def create_utility_log(reset=0):

# Create the table that will track the state of the utility script that
# maintains repos and calls gitdm.

	if reset:
		clear = "DROP TABLE IF EXISTS utility_log"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS utility_log ("
		"id BIGINT AUTO_INCREMENT PRIMARY KEY,"
		"level VARCHAR(8) NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

	cursor.execute(create)
	db.commit()

def create_unknown_cache(reset=0):

# After each facade-worker run, any unknown contributors and their email domain
# are cached in this table to make them easier to fetch later.

	if reset:
		clear = "DROP TABLE IF EXISTS unknown_cache"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS unknown_cache ("
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"projects_id INT NOT NULL,"
		"email VARCHAR(64) NOT NULL,"
		"domain VARCHAR(64),"
		"added INT NOT NULL)")

	cursor.execute(create)
	db.commit()

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
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"user VARCHAR(64) NOT NULL,"
		"email VARCHAR(64) NOT NULL,"
		"password VARCHAR(64) NOT NULL,"
		"created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
		"last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)")

	cursor.execute(create)
	db.commit()

	create = ("CREATE TABLE IF NOT EXISTS auth_history ("
		"id INT AUTO_INCREMENT PRIMARY KEY,"
		"user VARCHAR(64) NOT NULL,"
		"status VARCHAR(96) NOT NULL,"
		"attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)")

	cursor.execute(create)
	db.commit()

	user = ''
	email = ''
	hashed = ''

	print "Setting administrator credentials.\n"

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

if not os.path.isfile('db.py'):
	sys.exit("It appears you haven't configured db.py yet. Please do this.")

if not os.path.isfile('../includes/db.php'):
	sys.exit("It appears you haven't configured db.php yet. Please do this.")

print ("========== Facade database setup  ==========\n\n"
	"What do you want to do?\n"
	" (I)nitialize database. This will set up your database, and will clear any existing data.\n"
	" (U)pdate database while preserving settings, projects, and repos.\n")

action = raw_input('(i/u): ')

if action.lower() == 'i':

	print ("========== Initializing database tables ==========\n\n"
		"This will set up your database, and will clear any existing data.\n"
		"Are you sure?\n")

	confirm = raw_input('(yes): ')

	if confirm == "yes":
		print "Setting up database."

		create_settings('clear')
		create_projects('clear')
		create_repos('clear')
		create_gitdm_configs('clear')
		create_excludes('clear')
		create_repos_fetch_log('clear')
		create_gitdm_master('clear')
		create_gitdm_data('clear')
		create_special_tags('clear')
		create_utility_log('clear')
		create_unknown_cache('clear')
		create_auth('clear')

	else:
		print "Exiting without doing anything."

elif action.lower() == 'u':

	print ("========== Updating database tables ==========\n\n"
		"This will attempt to add and alter your database tables while preserving your major settings.\n"
		"It will reset your accumulated gitdm data, which means it will be rebuilt the next time\n"
		"facade-worker.py runs. This minimizes the risk of stale data.\n\n"
		"This may or may not work. Are you sure you want to continue?\n")

	confirm = raw_input('(yes): ')

	if confirm.lower() == "yes":
		print "Attempting update."

		create_gitdm_configs('clear')
		create_repos_fetch_log('clear')
		create_gitdm_master('clear')
		create_gitdm_data('clear')
		create_unknown_cache('clear')
		create_auth('clear')

	else:
		print "Exiting without doing anything."

else:

	print "Exiting without doing anything."
