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

# Git repo maintenance
#
# This script is responsible for cloning new repos and keeping existing repos up
# to date. It can be run as often as you want (and will detect when it's
# already running, so as not to spawn parallel processes), but once or twice per
# day should be more than sufficient. Each time it runs, it updates the repo
# and checks for any parents of HEAD that aren't already accounted for in the
# repos. It also rebuilds analysis data, checks any changed affiliations and
# aliases, and caches data for display.

import sys
import platform
import imp
import time
import datetime
import html.parser
import subprocess
import os
import getopt
import xlsxwriter
import configparser

if platform.python_implementation() == 'PyPy':
	import pymysql
else:
	import MySQLdb

global log_level

html = html.parser.HTMLParser()

# Important: Do not modify the database number unless you've also added an
# update clause to update_db!

upstream_db = 7

#### Database update functions ####

def increment_db(version):

	# Helper function to increment the database number

	increment_db = ("INSERT INTO settings (setting,value) "
		"VALUES ('database_version',%s)")
	cursor.execute(increment_db, (version, ))
	db.commit()

	print("Database updated to version: %s" % version)

def update_db(version):

	# This function should incrementally step any version of the database up to
	# the current schema. After executing the database operations, call
	# increment_db to bring it up to the version with which it is now compliant.

	print("Attempting database update")

	if version < 0:

		increment_db(0)

	if version < 1:
		# for commit f49b2f0e46b32997a72508bc83a6b1e834069588
		add_update_frequency = ("INSERT INTO settings (setting,value) "
			"VALUES ('update_frequency',24)")
		cursor.execute(add_update_frequency)
		db.commit

		increment_db(1)

	if version < 2:
		add_recache_to_projects = ("ALTER TABLE projects ADD COLUMN "
			"recache BOOL DEFAULT TRUE")
		cursor.execute(add_recache_to_projects)
		db.commit

		increment_db(2)

	if version < 3:
		add_results_setting = ("INSERT INTO settings (setting,value) "
			"VALUES ('results_visibility','show')")
		cursor.execute(add_results_setting)
		db.commit

		increment_db(3)

	if version < 4:
		add_working_commits_table = ("CREATE TABLE IF NOT EXISTS working_commits ("
			"repos_id INT UNSIGNED NOT NULL,"
			"working_commit VARCHAR(40))")

		cursor.execute(add_working_commits_table)
		db.commit

		# Make sure all working commits are processed

		get_working_commits = ("SELECT id,working_commit "
			"FROM repos WHERE working_commit > ''")

		cursor.execute(get_working_commits)

		working_commits = list(cursor)

		for commit in working_commits:
			trim_commit(commit['id'],commit['working_commit'])

		# Now it's safe to discard the (now unused) column

		remove_working_commit_column = ("ALTER TABLE repos DROP COLUMN "
			"working_commit")

		cursor.execute(remove_working_commit_column)
		db.commit

		increment_db(4)

	if version < 5:

		add_weekly_project_cache = ("CREATE TABLE IF NOT EXISTS project_weekly_cache ("
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

		cursor.execute(add_weekly_project_cache)
		db.commit

		add_weekly_repo_cache = ("CREATE TABLE IF NOT EXISTS repo_weekly_cache ("
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

		cursor.execute(add_weekly_repo_cache)
		db.commit

		increment_db(5)

	if version < 6:

		# As originally written, the UNIQUE wasn't working because it allowed
		# multiple NULL values in end_date.

		drop_special_tags_constraint = ("ALTER TABLE special_tags "
			"DROP INDEX `email,start_date,end_date,tag`")

		cursor.execute(drop_special_tags_constraint)
		db.commit

		add_unique_in_special_tags = ("ALTER TABLE special_tags "
			"ADD UNIQUE `email,start_date,tag` (email,start_date,tag)")

		cursor.execute(add_unique_in_special_tags)
		db.commit

		increment_db(6)

	if version < 7:

		# Using NULL for en unbounded nd_date in special_tags ended up being
		# difficult when doing certain types of reports. The logic is much
		# cleaner if we just use an end_date that is ridiculously far into the
		# future.

		remove_null_end_dates_in_special_tags = ("UPDATE special_tags "
			"SET end_date = '9999-12-31' WHERE end_date IS NULL")

		cursor.execute(remove_null_end_dates_in_special_tags)
		db.commit

		increment_db(7)

	print("No further database updates.\n")

def migrate_database_config():

# Since we're changing the way we store database credentials, we need a way to
# transparently migrate anybody who was using the old file. Someday after a long
# while this can disappear.

	try:
		# If the old database config was found, write a new config
		imp.find_module('db')

		db_config = configparser.ConfigParser()

		from db import db_user,db_pass,db_name,db_host
		from db import db_user_people,db_pass_people,db_name_people,db_host_people

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

		print("Migrated old style config file to new.")
	except:
		# If nothing is found, the user probably hasn't run setup yet.
		sys.exit("Can't find database config. Have you run setup.py?")

	try:
		os.remove('db.py')
		os.remove('db.pyc')
		print("Removed unneeded config files")
	except:
		print("Attempted to remove unneeded config files")

	return db_user,db_pass,db_name,db_host,db_user_people,db_pass_people,db_name_people,db_host_people

#### Global helper functions ####

def database_connection(db_host,db_user,db_pass,db_name):

# Return a database connection based upon which interpreter we're using. CPython
# can use any database connection, although MySQLdb is preferred over pymysql
# for performance reasons. However, PyPy can't use MySQLdb at this point,
# instead requiring a pure python MySQL client. This function returns a database
# connection that should provide maximum performance depending upon the
# interpreter in use.

	if platform.python_implementation() == 'PyPy':

		db = pymysql.connect(
			host = db_host,
			user = db_user,
			passwd = db_pass,
			db = db_name,
			charset = 'utf8mb4')

		cursor = db.cursor(pymysql.cursors.DictCursor)

	else:

		db = MySQLdb.connect(
			host = db_host,
			user = db_user,
			passwd = db_pass,
			db = db_name,
			charset = 'utf8mb4')

		cursor = db.cursor(MySQLdb.cursors.DictCursor)

	return db,cursor

def get_setting(setting):

# Get a setting from the database

	query = ("SELECT value FROM settings WHERE setting=%s ORDER BY "
		"last_modified DESC LIMIT 1")
	cursor.execute(query, (setting, ))
	return cursor.fetchone()["value"]

def update_status(status):

# Update the status displayed in the UI

	query = ("UPDATE settings SET value=%s WHERE setting='utility_status'")
	cursor.execute(query, (status, ))
	db.commit()

def log_activity(level,status):

# Log an activity based upon urgency and user's preference.  If the log level is
# "Debug", then just print it and don't save it in the database.

	log_options = ('Error','Quiet','Info','Verbose','Debug')

	if log_level == 'Debug' and level == 'Debug':
		sys.stderr.write("* %s\n" % status)
		return

	if log_options.index(level) <= log_options.index(log_level):
		query = ("INSERT INTO utility_log (level,status) VALUES (%s,%s)")
		cursor.execute(query, (level, status))
		db.commit()
		sys.stderr.write("* %s\n" % status)

def update_repo_log(repos_id,status):

# Log a repo's fetch status

	log_message = ("INSERT INTO repos_fetch_log (repos_id,status) "
		"VALUES (%s,%s)")

	cursor.execute(log_message, (repos_id, status))
	db.commit()

def trim_commit(repo_id,commit):

# Quickly remove a given commit

	remove_commit = ("DELETE FROM analysis_data "
		"WHERE repos_id=%s "
		"AND commit=%s")

	cursor.execute(remove_commit, (repo_id, commit))
	db.commit()

	log_activity('Debug','Trimmed commit: %s' % commit)

def store_working_author(email):

# Store the working author during affiliation discovery, in case it is
# interrupted and needs to be trimmed.

	store = ("UPDATE settings "
		"SET value = %s "
		"WHERE setting = 'working_author'")

	cursor.execute(store, (email, ))
	db.commit()

	log_activity('Debug','Stored working author: %s' % email)

def trim_author(email):

# Remove the affiliations associated with an email. Used when an analysis is
# interrupted during affiliation layering, and the data will be corrupt.

	trim = ("UPDATE analysis_data "
		"SET author_affiliation = NULL "
		"WHERE author_email = %s")

	cursor.execute(trim, (email, ))
	db.commit()

	trim = ("UPDATE analysis_data "
		"SET committer_affiliation = NULL "
		"WHERE committer_email = %s")

	cursor.execute(trim, (email, ))
	db.commit()

	store_working_author('done')

	log_activity('Debug','Trimmed working author: %s' % email)

def analyze_commit(repo_id,repo_loc,commit):

# This function analyzes a given commit, counting the additions, removals, and
# whitespace changes. It collects all of the metadata about the commit, and
# stashes it in the database.  A new database connection is opened each time in
# case we are running in multithreaded mode, since MySQL cursors are not
# currently threadsafe.

### Local helper functions ###

	def check_swapped_emails(name,email):

	# Sometimes people mix up their name and email in their git settings

		if name.find('@') >= 0 and email.find('@') == -1:
			log_activity('Debug','Found swapped email/name: %s/%s' % (email,name))
			return email,name
		else:
			return name,email

	def strip_extra_amp(email):

	# Some repos have multiple ampersands, which really messes up domain pattern
	# matching. This extra info is not used, so we discard it.

		if email.count('@') > 1:
			log_activity('Debug','Found extra @: %s' % email)
			return email[:email.find('@',email.find('@')+1)]
		else:
			return email

	def discover_alias(email):

	# Match aliases with their canonical email
		fetch_canonical = ("SELECT canonical "
			"FROM aliases "
			"WHERE alias=%s "
			"AND active = TRUE")

		cursor_people_local.execute(fetch_canonical, (email, ))
		db_people_local.commit()

		canonical = list(cursor_people_local)

		if canonical:
			for email in canonical:
				return email['canonical']
		else:
			return email

	def store_commit(repos_id,commit,filename,
		author_name,author_email,author_date,
		committer_name,committer_email,committer_date,
		added,removed, whitespace):

	# Fix some common issues in git commit logs and store data.

		# Sometimes git is misconfigured and name/email get swapped
		author_name, author_email = check_swapped_emails(author_name,author_email)
		committer_name,committer_email = check_swapped_emails(committer_name,committer_email)

		# Some systems append extra info after a second @
		author_email = strip_extra_amp(author_email)
		committer_email = strip_extra_amp(committer_email)

		store = ("INSERT INTO analysis_data (repos_id,commit,filename,"
			"author_name,author_raw_email,author_email,author_date,"
			"committer_name,committer_raw_email,committer_email,committer_date,"
			"added,removed,whitespace) "
			"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")

		cursor_local.execute(store, (
			repos_id,commit,filename,
			author_name,author_email,discover_alias(author_email),author_date,
			committer_name,committer_email,discover_alias(committer_email),committer_date,
			added,removed,whitespace))

		db_local.commit()

		log_activity('Debug','Stored commit: %s' % commit)

### The real function starts here ###

	header = True
	filename = ''
	filename = ''
	added = 0
	removed = 0
	whitespace = 0

	# Set up new threadsafe database connections if multithreading. Otherwise
	# use the gloabl database connections so we don't incur a performance
	# penalty.

	if multithreaded:
		db_local,cursor_local = database_connection(
			db_host,
			db_user,
			db_pass,
			db_name)

		db_people_local,cursor_people_local = database_connection(
			db_host_people,
			db_user_people,
			db_pass_people,
			db_name_people)

	else:
		db_local = db
		cursor_local = cursor

		db_people_local = db_people
		cursor_people_local = cursor_people

	# Read the git log

	git_log = subprocess.Popen(["git --git-dir %s log -p -M %s -n1 "
		"--pretty=format:'"
		"author_name: %%an%%nauthor_email: %%ae%%nauthor_date:%%ai%%n"
		"committer_name: %%cn%%ncommitter_email: %%ce%%ncommitter_date: %%ci%%n"
		"parents: %%p%%nEndPatch' "
		% (repo_loc,commit)], stdout=subprocess.PIPE, shell=True)

	# Stash the commit we're going to analyze so we can back it out if something
	# goes wrong later.
	store_working_commit = ("INSERT INTO working_commits "
		"(repos_id,working_commit) VALUES (%s,%s)")

	cursor_local.execute(store_working_commit, (repo_id,commit))
	db_local.commit()

	log_activity('Debug','Stored working commit and analyzing : %s' % commit)

	for line in git_log.stdout.read().decode("utf-8",errors="ignore").split(os.linesep):
		if len(line) > 0:

			if line.find('author_name:') == 0:
				author_name = line[13:]
				continue

			if line.find('author_email:') == 0:
				author_email = line[14:]
				continue

			if line.find('author_date:') == 0:
				author_date = line[12:22]
				continue

			if line.find('committer_name:') == 0:
				committer_name = line[16:]
				continue

			if line.find('committer_email:') == 0:
				committer_email = line[17:]
				continue

			if line.find('committer_date:') == 0:
				committer_date = line[16:26]
				continue

			if line.find('parents:') == 0:
				if len(line[9:].split(' ')) == 2:

					# We found a merge commit, which won't have a filename
					filename = '(Merge commit)';

					added = 0
					removed = 0
					whitespace = 0
				continue

			if line.find('--- a/') == 0:
				if filename == '(Deleted) ':
					filename = filename + line[6:]
				continue

			if line.find('+++ b/') == 0:
				if not filename.find('(Deleted) ') == 0:
					filename = line[6:]
				continue

			if line.find('rename to ') == 0:
				filename = line[10:]
				continue

			if line.find('deleted file ') == 0:
				filename = '(Deleted) '
				continue

			if line.find('diff --git') == 0:

				# Git only displays the beginning of a file in a patch, not
				# the end. We need some kludgery to discern where one starts
				# and one ends. This is the last line always separating
				# files in commits. But we only want to do it for the second
				# time onward, since the first time we hit this line it'll be
				# right after parsing the header and there won't be any useful
				# information contained in it.

				if not header:

					store_commit(repo_id,commit,filename,
						author_name,author_email,author_date,
						committer_name,committer_email,committer_date,
						added,removed,whitespace)

				header = False

				# Reset stats and prepare for the next section
				whitespaceCheck = []
				resetRemovals = True
				filename = ''
				added = 0
				removed = 0
				whitespace = 0
				continue

			# Count additions and removals and look for whitespace changes
			if not header:
				if line[0] == '+':

					# First check if this is a whitespace change
					if len(line.strip()) == 1:
						# Line with zero length
						whitespace += 1

					else:
						# Compare against removals, detect whitespace changes
						whitespaceChange = False

						for check in whitespaceCheck:

							# Mark matches of non-trivial length
							if line[1:].strip() == check and len(line[1:].strip()) > 8:
								whitespaceChange = True

						if whitespaceChange:
							# One removal was whitespace, back it out
							removed -= 1
							whitespace += 1
							# Remove the matched line
							whitespaceCheck.remove(check)

						else:
							# Did not trigger whitespace criteria
							added += 1

					# Once we hit an addition, next removal line will be new.
					# At that point, start a new collection for checking.
					resetRemovals = True

				if line[0] == '-':
					removed += 1
					if resetRemovals:
						whitespaceCheck = []
						resetRemovals = False
					# Store the line to check next add lines for a match
					whitespaceCheck.append(line[1:].strip())

	# Store the last stats from the git log
	store_commit(repo_id,commit,filename,
		author_name,author_email,author_date,
		committer_name,committer_email,committer_date,
		added,removed,whitespace)

	# Remove the working commit.
	remove_commit = ("DELETE FROM working_commits "
		"WHERE repos_id = %s AND working_commit = %s")
	cursor_local.execute(remove_commit, (repo_id,commit))
	db_local.commit()

	log_activity('Debug','Completed and removed working commit: %s' % commit)

	# If multithreading, clean up the local database

	if multithreaded:
		cursor_local.close()
		cursor_people_local.close()
		db_local.close()
		db_people_local.close()

#### Facade main functions ####

def git_repo_cleanup():

# Clean up any git repos that are pending deletion

	update_status('Purging deleted repos')
	log_activity('Info','Processing deletions')

	repo_base_directory = get_setting('repo_directory')

	query = "SELECT id,projects_id,path,name FROM repos WHERE status='Delete'"
	cursor.execute(query)

	delete_repos = list(cursor)

	for row in delete_repos:

		# Remove the files on disk

		cmd = ("rm -rf %s%s/%s%s"
			% (repo_base_directory,row['projects_id'],row['path'],row['name']))

		return_code = subprocess.Popen([cmd],shell=True).wait()

		# Remove the analysis data

		remove_analysis_data = "DELETE FROM analysis_data WHERE repos_id=%s"
		cursor.execute(remove_analysis_data, (row['id'], ))

		optimize_table = "OPTIMIZE TABLE analysis_data"
		cursor.execute(optimize_table)
		db.commit()

		# Remove cached repo data

		remove_repo_weekly_cache = "DELETE FROM repo_weekly_cache WHERE repos_id=%s"
		cursor.execute(remove_repo_weekly_cache, (row['id'], ))
		db.commit()

		optimize_table = "OPTIMIZE TABLE repo_weekly_cache"
		cursor.execute(optimize_table)
		db.commit()

		remove_repo_monthly_cache = "DELETE FROM repo_monthly_cache WHERE repos_id=%s"
		cursor.execute(remove_repo_monthly_cache, (row['id'], ))
		db.commit()

		optimize_table = "OPTIMIZE TABLE repo_monthly_cache"
		cursor.execute(optimize_table)
		db.commit()

		remove_repo_annual_cache = "DELETE FROM repo_annual_cache WHERE repos_id=%s"
		cursor.execute(remove_repo_annual_cache, (row['id'], ))
		db.commit()

		optimize_table = "OPTIMIZE TABLE repo_annual_cache"
		cursor.execute(optimize_table)
		db.commit()

		# Set project to be recached if just removing a repo

		set_project_recache = ("UPDATE projects SET recache=TRUE "
			"WHERE id=%s")
		cursor.execute(set_project_recache,(row['projects_id'], ))
		db.commit()

		# Remove the entry from the repos table

		query = "DELETE FROM repos WHERE id=%s"
		cursor.execute(query, (row['id'], ))
		db.commit()

		log_activity('Verbose','Deleted repo %s' % row['id'])

		cleanup = '%s/%s%s' % (row['projects_id'],row['path'],row['name'])

		# Remove any working commits

		remove_working_commits = "DELETE FROM working_commits WHERE repos_id=%s"
		cursor.execute(remove_working_commits, (row['id'], ))
		db.commit()

		# Remove the repo from the logs

		remove_logs = ("DELETE FROM repos_fetch_log WHERE repos_id = %s")

		cursor.execute(remove_logs, (row['id'], ))
		db.commit()

		optimize_table = "OPTIMIZE TABLE repos_fetch_log"
		cursor.execute(optimize_table)
		db.commit()

		# Attempt to cleanup any empty parent directories

		while (cleanup.find('/',0) > 0):
			cleanup = cleanup[:cleanup.rfind('/',0)]

			cmd = "rmdir %s%s" % (repo_base_directory,cleanup)
			subprocess.Popen([cmd],shell=True).wait()
			log_activity('Verbose','Attempted %s' % cmd)

		update_repo_log(row['id'],'Deleted')

	# Clean up deleted projects

	get_deleted_projects = "SELECT id FROM projects WHERE name='(Queued for removal)'"
	cursor.execute(get_deleted_projects)

	deleted_projects = list(cursor)

	for project in deleted_projects:

		# Remove cached data for projects which were marked for deletion

		clear_annual_cache = ("DELETE FROM project_annual_cache WHERE "
			"projects_id=%s")
		cursor.execute(clear_annual_cache, (project['id'], ))
		db.commit()

		optimize_table = "OPTIMIZE TABLE project_annual_cache"
		cursor.execute(optimize_table)
		db.commit()

		clear_monthly_cache = ("DELETE FROM project_monthly_cache WHERE "
			"projects_id=%s")
		cursor.execute(clear_monthly_cache, (project['id'], ))
		db.commit()

		optimize_table = "OPTIMIZE TABLE project_monthly_cache"
		cursor.execute(optimize_table)
		db.commit()

		clear_weekly_cache = ("DELETE FROM project_weekly_cache WHERE "
			"projects_id=%s")
		cursor.execute(clear_weekly_cache, (project['id'], ))
		db.commit()

		optimize_table = "OPTIMIZE TABLE project_weekly_cache"
		cursor.execute(optimize_table)
		db.commit()

		clear_unknown_cache = ("DELETE FROM unknown_cache WHERE "
			"projects_id=%s")
		cursor.execute(clear_unknown_cache, (project['id'], ))
		db.commit()

		optimize_table = "OPTIMIZE TABLE project_weekly_cache"
		cursor.execute(optimize_table)
		db.commit()

		# Remove any projects which were also marked for deletion

		remove_project = "DELETE FROM projects WHERE id=%s"
		cursor.execute(remove_project, (project['id'], ))
		db.commit()

	log_activity('Info','Processing deletions (complete)')

def git_repo_initialize():

# Select any new git repos so we can set up their locations and git clone

	update_status('Fetching new repos')
	log_activity('Info','Fetching new repos')

	query = "SELECT id,projects_id,git FROM repos WHERE status LIKE 'New%'";
	cursor.execute(query)

	new_repos = list(cursor)

	for row in new_repos:
		print(row["git"])
		update_repo_log(row['id'],'Cloning')

		git = html.unescape(row["git"])

		# Strip protocol from remote URL, set a unique path on the filesystem
		if git.find('://',0) > 0:
			repo_relative_path = git[git.find('://',0)+3:][:git[git.find('://',0)+3:].rfind('/',0)+1]
		else:
			repo_relative_path = git[:git.rfind('/',0)+1]

		# Get the full path to the directory where we'll clone the repo
		repo_path = ('%s%s/%s' %
			(repo_base_directory,row["projects_id"],repo_relative_path))

		# Get the name of repo
		repo_name = git[git.rfind('/',0)+1:]
		if repo_name.find('.git',0) > -1:
			repo_name = repo_name[:repo_name.find('.git',0)]

		# Check if there will be a storage path collision
		query = ("SELECT NULL FROM repos WHERE CONCAT(projects_id,'/',path,name) = %s")
		cursor.execute(query, ('{}/{}{}'.format(row["projects_id"], repo_relative_path, repo_name), ))
		db.commit()

		# If there is a collision, append a slug to repo_name to yield a unique path
		if cursor.rowcount:

			slug = 1
			is_collision = True
			while is_collision:

				if os.path.isdir('%s%s-%s' % (repo_path,repo_name,slug)):
					slug += 1
				else:
					is_collision = False

			repo_name = '%s-%s' % (repo_name,slug)

			log_activity('Verbose','Identical repo detected, storing %s in %s' %
				(git,repo_name))

		# Create the prerequisite directories
		return_code = subprocess.Popen(['mkdir -p %s' %repo_path],shell=True).wait()

		# Make sure it's ok to proceed
		if return_code != 0:
			print("COULD NOT CREATE REPO DIRECTORY")

			update_repo_log(row['id'],'Failed (mkdir)')
			update_status('Failed (mkdir %s)' % repo_path)
			log_activity('Error','Could not create repo directory: %s' %
				repo_path)

			sys.exit("Could not create git repo's prerequisite directories. "
				" Do you have write access?")

		update_repo_log(row['id'],'New (cloning)')

		query = ("UPDATE repos SET status='New (Initializing)', path=%s, "
			"name=%s WHERE id=%s")

		cursor.execute(query, (repo_relative_path,repo_name,row["id"]))
		db.commit()

		log_activity('Verbose','Cloning: %s' % git)

		cmd = "git -C %s clone '%s' %s" % (repo_path,git,repo_name)
		return_code = subprocess.Popen([cmd], shell=True).wait()

		if (return_code == 0):
			# If cloning succeeded, repo is ready for analysis
			# Mark the entire project for an update, so that under normal
			# circumstances caches are rebuilt only once per waiting period.

			update_project_status = ("UPDATE repos SET status='Update' WHERE "
				"projects_id=%s")
			cursor.execute(update_project_status, (row['projects_id'], ))
			db.commit()

			# Since we just cloned the new repo, set it straight to analyze.
			query = ("UPDATE repos SET status='Analyze',path=%s, name=%s "
				"WHERE id=%s")

			cursor.execute(query, (repo_relative_path,repo_name,row["id"]))
			db.commit()

			update_repo_log(row['id'],'Up-to-date')
			log_activity('Info','Cloned %s' % git)

		else:
			# If cloning failed, log it and set the status back to new
			update_repo_log(row['id'],'Failed (%s)' % return_code)

			query = ("UPDATE repos SET status='New (failed)' WHERE id=%s")

			cursor.execute(query, (row['id'], ))
			db.commit()

			log_activity('Error','Could not clone %s' % git)

	log_activity('Info', 'Fetching new repos (complete)')

def check_for_repo_updates():

# Check the last time a repo was updated and if it has been longer than the
# update_frequency, mark its project for updating during the next analysis.

	update_status('Checking if any repos need to update')
	log_activity('Info','Checking repos to update')

	update_frequency = get_setting('update_frequency')

	get_initialized_repos = ("SELECT id FROM repos WHERE status NOT LIKE 'New%' "
		"AND status != 'Delete' "
		"AND status != 'Analyze'")
	cursor.execute(get_initialized_repos)
	repos = list(cursor)

	for repo in repos:

		# Figure out which repos have been updated within the waiting period

		get_last_update = ("SELECT NULL FROM repos_fetch_log WHERE "
			"repos_id=%s AND status='Up-to-date' AND "
			"date >= CURRENT_TIMESTAMP(6) - INTERVAL %s HOUR ")

		cursor.execute(get_last_update, (repo['id'], update_frequency))

		# If the repo has not been updated within the waiting period, mark it.
		# Also mark any other repos in the project, so we only recache the
		# project once per waiting period.

		if cursor.rowcount == 0:
			mark_repo = ("UPDATE repos r JOIN projects p ON p.id = r.projects_id "
				"SET status='Update' WHERE "
				"r.id=%s ")
			cursor.execute(mark_repo, (repo['id'], ))
			db.commit()

	# Mark the entire project for an update, so that under normal
	# circumstances caches are rebuilt only once per waiting period.

	update_project_status = ("UPDATE repos r LEFT JOIN repos s ON r.projects_id=s.projects_id "
		"SET r.status='Update' WHERE s.status='Update' AND "
		"r.status != 'Analyze'")
	cursor.execute(update_project_status)
	db.commit()

	log_activity('Info','Checking repos to update (complete)')

def force_repo_updates():

# Set the status of all non-new repos to "Update".

	update_status('Forcing all non-new repos to update')
	log_activity('Info','Forcing repos to update')

	get_repo_ids = ("UPDATE repos SET status='Update' WHERE status "
		"NOT LIKE 'New%' AND STATUS!='Delete'")
	cursor.execute(get_repo_ids)
	db.commit()

	log_activity('Info','Forcing repos to update (complete)')

def force_repo_analysis():

# Set the status of all non-new repos to "Analyze".

	update_status('Forcing all non-new repos to be analyzed')
	log_activity('Info','Forcing repos to be analyzed')

	set_to_analyze = ("UPDATE repos SET status='Analyze' WHERE status "
		"NOT LIKE 'New%' AND STATUS!='Delete'")
	cursor.execute(set_to_analyze)
	db.commit()

	log_activity('Info','Forcing repos to be analyzed (complete)')

def git_repo_updates():

# Update existing repos

	update_status('Updating repos')
	log_activity('Info','Updating existing repos')

	repo_base_directory = get_setting('repo_directory')

	query = ("SELECT id,projects_id,git,name,path FROM repos WHERE "
		"status='Update'");
	cursor.execute(query)

	existing_repos = list(cursor)

	for row in existing_repos:

		log_activity('Verbose','Attempting to update %s' % row['git'])
		update_repo_log(row['id'],'Updating')

		attempt = 0

		# Try two times. If it fails the first time, reset and clean the git repo,
		# as somebody may have done a rebase. No work is being done in the local
		# repo, so there shouldn't be legit local changes to worry about.

		while attempt < 2:

			cmd = ("git -C %s%s/%s%s pull"
				% (repo_base_directory,row['projects_id'],row['path'],row['name']))

			return_code = subprocess.Popen([cmd],shell=True).wait()

			# If the attempt succeeded, then don't try any further fixes. If
			# the attempt to fix things failed, give up and try next time.
			if return_code == 0 or attempt == 1:
				break

			elif attempt == 0:

				log_activity('Verbose','git pull failed, attempting reset and '
					'clean for %s' % row['git'])

				cmd_reset = ("git -C %s%s/%s%s reset --hard origin/master"
					% (repo_base_directory,row['projects_id'],row['path'],row['name']))

				return_code_reset = subprocess.Popen([cmd_reset],shell=True).wait()

				cmd_clean = ("git -C %s%s/%s%s clean -df"
					% (repo_base_directory,row['projects_id'],row['path'],row['name']))

				return_code_clean = subprocess.Popen([cmd_clean],shell=True).wait()

			attempt += 1

		if return_code == 0:

			set_to_analyze = "UPDATE repos SET status='Analyze' WHERE id=%s"
			cursor.execute(set_to_analyze, (row['id'], ))
			db.commit()

			update_repo_log(row['id'],'Up-to-date')
			log_activity('Verbose','Updated %s' % row["git"])

		else:
			update_repo_log(row['id'],'Failed (%s)' % return_code)
			log_activity('Error','Could not update %s' % row["git"])

	log_activity('Info','Updating existing repos (complete)')

def analysis():

# Run the analysis by looping over all active repos. For each repo, we retrieve
# the list of commits which lead to HEAD. If any are missing from the database,
# they are filled in. Then we check to see if any commits in the database are
# not in the list of parents, and prune them out.
#
# We also keep track of the last commit to be processed, so that if the analysis
# is interrupted (possibly leading to partial data in the database for the
# commit being analyzed at the time) we can recover.

### Local helper functions ###

	def update_analysis_log(repos_id,status):

	# Log a repo's analysis status

		log_message = ("INSERT INTO analysis_log (repos_id,status) "
			"VALUES (%s,%s)")

		cursor.execute(log_message, (repos_id,status))
		db.commit()

### The real function starts here ###

	update_status('Running analysis')
	log_activity('Info','Beginning analysis')

	start_date = get_setting('start_date')

	repo_list = "SELECT id,projects_id,path,name FROM repos WHERE status='Analyze'"
	cursor.execute(repo_list)
	repos = list(cursor)

	for repo in repos:

		update_analysis_log(repo['id'],'Beginning analysis')
		log_activity('Verbose','Analyzing repo: %s (%s)' % (repo['id'],repo['name']))

		# First we check to see if the previous analysis didn't complete

		get_status = ("SELECT working_commit FROM working_commits WHERE repos_id=%s")

		cursor.execute(get_status, (repo['id'], ))
		working_commits = list(cursor)
		#cursor.fetchone()['working_commit']

		# If there's a commit still there, the previous run was interrupted and
		# the commit data may be incomplete. It should be trimmed, just in case.
		for commit in working_commits:
			trim_commit(repo['id'],commit['working_commit'])

			# Remove the working commit.
			remove_commit = ("DELETE FROM working_commits "
				"WHERE repos_id = %s AND working_commit = %s")
			cursor.execute(remove_commit, (repo['id'],commit['working_commit']))
			db.commit()

			log_activity('Debug','Removed working commit: %s' % commit['working_commit'])

		# Start the main analysis

		update_analysis_log(repo['id'],'Collecting data')

		repo_loc = ('%s%s/%s%s/.git' % (repo_base_directory,
			repo["projects_id"], repo["path"],
			repo["name"]))
		# Grab the parents of HEAD

		parents = subprocess.Popen(["git --git-dir %s log --ignore-missing "
			"--pretty=format:'%%H' --since=%s" % (repo_loc,start_date)],
			stdout=subprocess.PIPE, shell=True)

		parent_commits = set(parents.stdout.read().decode("utf-8",errors="ignore").split(os.linesep))

		# If there are no commits in the range, we still get a blank entry in
		# the set. Remove it, as it messes with the calculations

		if '' in parent_commits:
			parent_commits.remove('')

		# Grab the existing commits from the database

		existing_commits = set()

		find_existing = ("SELECT DISTINCT commit FROM analysis_data WHERE repos_id=%s")

		cursor.execute(find_existing, (repo['id'], ))

		for commit in list(cursor):
			existing_commits.add(commit['commit'])

		# Find missing commits and add them

		missing_commits = parent_commits - existing_commits

		log_activity('Debug','Commits missing from repo %s: %s' %
			(repo['id'],len(missing_commits)))

		if multithreaded:

			from multiprocessing import Pool

			pool = Pool()

			for commit in missing_commits:

				result =pool.apply_async(analyze_commit,(repo['id'],repo_loc,commit))

			pool.close()
			pool.join()

		else:
			for commit in missing_commits:
				analyze_commit(repo['id'],repo_loc,commit)

		update_analysis_log(repo['id'],'Data collection complete')

		update_analysis_log(repo['id'],'Beginning to trim commits')

		# Find commits which are out of the analysis range

		trimmed_commits = existing_commits - parent_commits

		log_activity('Debug','Commits to be trimmed from repo %s: %s' %
			(repo['id'],len(trimmed_commits)))

		for commit in trimmed_commits:

			trim_commit(repo['id'],commit)

		set_complete = "UPDATE repos SET status='Complete' WHERE id=%s"

		cursor.execute(set_complete, (repo['id'], ))

		update_analysis_log(repo['id'],'Commit trimming complete')

		update_analysis_log(repo['id'],'Complete')

	log_activity('Info','Running analysis (complete)')

def nuke_affiliations():

# Delete all stored affiliations in the database. Normally when you
# add/remove/change affiliation data via the web UI, any potentially affected
# records will be deleted and then rebuilt on the next run. However, if you
# manually add affiliation records via the database or import them by some other
# means, there's no elegant way to discover which affiliations are affected. So
# this is the scorched earth way: remove them all to force a total rebuild.
# Brutal but effective.

	log_activity('Info','Nuking affiliations')

	nuke = ("UPDATE analysis_data SET author_affiliation = NULL, "
			"committer_affiliation = NULL")

	cursor.execute(nuke)
	db.commit()

	log_activity('Info','Nuking affiliations (complete)')

def fill_empty_affiliations():

# When a record is added, it has no affiliation data. Also, when an affiliation
# mapping is changed via the UI, affiliation data will be set to NULL. This
# function finds any records with NULL affiliation data and fills them.

### Local helper functions ###

	def update_affiliation(email_type,email,affiliation,start_date):

		update = ("UPDATE analysis_data "
			"SET %s_affiliation = %%s "
			"WHERE %s_email = %%s "
			"AND %s_affiliation IS NULL "
			"AND %s_date >= %%s" %
			(email_type, email_type, email_type, email_type))

		cursor.execute(update, (affiliation, email, start_date))
		db.commit()

	def discover_null_affiliations(attribution,email):

	# Try a bunch of ways to match emails to attributions in the database. First it
	# tries to match exactly. If that doesn't work, it tries to match by domain. If
	# domain doesn't work, it strips subdomains from the email and tries again.

		# First we see if there's an exact match. This will also catch malformed or
		# intentionally mangled emails (e.g. "developer at domain.com") that have
		# been added as an affiliation rather than an alias.

		find_exact_match = ("SELECT affiliation,start_date "
			"FROM affiliations "
			"WHERE domain = %s "
			"AND active = TRUE "
			"ORDER BY start_date DESC")

		cursor_people.execute(find_exact_match, (email, ))
		db_people.commit

		matches = list(cursor_people)

		if not matches and email.find('@') < 0:

			# It's not a properly formatted email, leave it NULL and log it.

			log_activity('Info','Unmatchable email: %s' % email)

			return

		if not matches:

			# Now we go for a domain-level match. Try for an exact match.

			domain = email[email.find('@')+1:]

			find_exact_domain = ("SELECT affiliation,start_date "
				"FROM affiliations "
				"WHERE domain= %s "
				"AND active = TRUE "
				"ORDER BY start_date DESC")

			cursor_people.execute(find_exact_domain, (domain, ))
			db_people.commit()

			matches = list(cursor_people)

		if not matches:

			# Then try stripping any subdomains.

			find_domain = ("SELECT affiliation,start_date "
				"FROM affiliations "
				"WHERE domain = %s "
				"AND active = TRUE "
				"ORDER BY start_date DESC")

			cursor_people.execute(find_domain, (domain[domain.rfind('.',0,domain.rfind('.',0))+1:], ))
			db_people.commit()

			matches = list(cursor_people)

		if not matches:

			# One last check to see if it's an unmatched academic domain.

			if domain[-4:] in '.edu':
				matches.append({'affiliation':'(Academic)','start_date':'1970-01-01'})

		# Done looking. Now we process any matches that were found.

		if matches:

			log_activity('Debug','Found domain match for %s' % email)

			for match in matches:
				update = ("UPDATE analysis_data "
					"SET %s_affiliation = %%s "
					"WHERE %s_email = %%s "
					"AND %s_affiliation IS NULL "
					"AND %s_date >= %%s" %
					(attribution, attribution, attribution, attribution))

				cursor.execute(update, (match['affiliation'], email, match['start_date']))
				db.commit()

	def discover_alias(email):

	# Match aliases with their canonical email

		fetch_canonical = ("SELECT canonical "
			"FROM aliases "
			"WHERE alias=%s "
			"AND active = TRUE")

		cursor_people.execute(fetch_canonical, (email, ))
		db_people.commit()

		canonical = list(cursor_people)

		if canonical:
			for email in canonical:
				return email['canonical']
		else:
			return email

### The real function starts here ###

	update_status('Filling empty affiliations')
	log_activity('Info','Filling empty affiliations')

	# Process any changes to the affiliations or aliases, and set any existing
	# entries in analysis_data to NULL so they are filled properly.

	# First, get the time we started fetching since we'll need it later

	cursor.execute("SELECT current_timestamp(6) as fetched")

	affiliations_fetched = cursor.fetchone()['fetched']

	# Now find the last time we worked on affiliations, to figure out what's new

	affiliations_processed = get_setting('affiliations_processed')

	get_changed_affiliations = ("SELECT domain FROM affiliations WHERE "
		"last_modified >= %s")

	cursor_people.execute(get_changed_affiliations, (affiliations_processed, ))

	changed_affiliations = list(cursor_people)

	# Process any affiliations which changed since we last checked

	for changed_affiliation in changed_affiliations:

		log_activity('Debug','Resetting affiliation for %s' %
			changed_affiliation['domain'])

		set_author_to_null = ("UPDATE analysis_data SET author_affiliation = NULL "
			"WHERE author_email LIKE CONCAT('%%',%s)")

		cursor.execute(set_author_to_null, (changed_affiliation['domain'], ))
		db.commit()

		set_committer_to_null = ("UPDATE analysis_data SET committer_affiliation = NULL "
			"WHERE committer_email LIKE CONCAT('%%',%s)")

		cursor.execute(set_committer_to_null, (changed_affiliation['domain'], ))
		db.commit()

	# Update the last fetched date, so we know where to start next time.

	update_affiliations_date = ("UPDATE settings SET value=%s "
		"WHERE setting = 'affiliations_processed'")

	cursor.execute(update_affiliations_date, (affiliations_fetched, ))
	db.commit()

	# On to the aliases, now

	# First, get the time we started fetching since we'll need it later

	cursor.execute("SELECT current_timestamp(6) as fetched")

	aliases_fetched = cursor.fetchone()['fetched']

	# Now find the last time we worked on aliases, to figure out what's new

	aliases_processed = get_setting('aliases_processed')

	get_changed_aliases = ("SELECT alias FROM aliases WHERE "
		"last_modified >= %s")

	cursor_people.execute(get_changed_aliases, (aliases_processed, ))

	changed_aliases = list(cursor_people)

	# Process any aliases which changed since we last checked

	for changed_alias in changed_aliases:

		log_activity('Debug','Resetting affiliation for %s' %
			changed_alias['alias'])

		set_author_to_null = ("UPDATE analysis_data SET author_affiliation = NULL "
			"WHERE author_raw_email LIKE CONCAT('%%',%s)")

		cursor.execute(set_author_to_null,(changed_alias['alias'], ))
		db.commit()

		set_committer_to_null = ("UPDATE analysis_data SET committer_affiliation = NULL "
			"WHERE committer_raw_email LIKE CONCAT('%%',%s)")

		cursor.execute(set_committer_to_null, (changed_alias['alias'], ))
		db.commit()

		reset_author = ("UPDATE analysis_data "
			"SET author_email = %s "
			"WHERE author_raw_email = %s")

		cursor.execute(reset_author, (discover_alias(changed_alias['alias']),changed_alias['alias']))
		db.commit

		reset_committer = ("UPDATE analysis_data "
			"SET committer_email = %s "
			"WHERE committer_raw_email = %s")

		cursor.execute(reset_committer,	(discover_alias(changed_alias['alias']),changed_alias['alias']))
		db.commit

	# Update the last fetched date, so we know where to start next time.

	update_aliases_date = ("UPDATE settings SET value=%s "
		"WHERE setting = 'aliases_processed'")

	cursor.execute(update_aliases_date, (aliases_fetched, ))
	db.commit()

	# Now rebuild the affiliation data

	working_author = get_setting('working_author')

	if working_author != 'done':
		log_activity('Error','Trimming author data in affiliations: %s' %
			working_author)
		trim_author(working_author)

	# Figure out which projects have NULL affiliations so they can be recached

	set_recache = ("UPDATE projects p "
		"JOIN repos r ON p.id = r.projects_id "
		"JOIN analysis_data a ON r.id = a.repos_id "
		"SET recache=TRUE WHERE "
		"author_affiliation IS NULL OR "
		"committer_affiliation IS NULL")
	cursor.execute(set_recache)
	db.commit()

	# Find any authors with NULL affiliations and fill them

	find_null_authors = ("SELECT DISTINCT author_email AS email, "
		"MIN(author_date) AS earliest "
		"FROM analysis_data "
		"WHERE author_affiliation IS NULL "
		"GROUP BY author_email")

	cursor.execute(find_null_authors)

	null_authors = list(cursor)

	log_activity('Debug','Found %s authors with NULL affiliation' %
		len(null_authors))

	for null_author in null_authors:

		email = null_author['email']

		store_working_author(email)

		discover_null_affiliations('author',email)

	store_working_author('done')

	# Find any committers with NULL affiliations and fill them

	find_null_committers = ("SELECT DISTINCT committer_email AS email, "
		"MIN(committer_date) AS earliest "
		"FROM analysis_data "
		"WHERE committer_affiliation IS NULL "
		"GROUP BY committer_email")

	cursor.execute(find_null_committers)

	null_committers = list(cursor)

	log_activity('Debug','Found %s committers with NULL affiliation' %
		len(null_committers))

	for null_committer in null_committers:

		email = null_committer['email']

		store_working_author(email)

		discover_null_affiliations('committer',email)

	# Now that we've matched as much as possible, fill the rest as (Unknown)

	fill_unknown_author = ("UPDATE analysis_data "
		"SET author_affiliation = '(Unknown)' "
		"WHERE author_affiliation IS NULL")

	cursor.execute(fill_unknown_author)
	db.commit()

	fill_unknown_committer = ("UPDATE analysis_data "
		"SET committer_affiliation = '(Unknown)' "
		"WHERE committer_affiliation IS NULL")

	cursor.execute(fill_unknown_committer)
	db.commit()

	store_working_author('done')

	log_activity('Info','Filling empty affiliations (complete)')

def invalidate_caches():

# Invalidate all caches

	update_status('Invalidating caches')
	log_activity('Info','Invalidating caches')

	invalidate_cache = "UPDATE projects SET recache = TRUE"
	cursor.execute(invalidate_cache)
	db.commit()

	log_activity('Info','Invalidating caches (complete)')

def rebuild_unknown_affiliation_and_web_caches():

# When there's a lot of analysis data, calculating display data on the fly gets
# pretty expensive. Instead, we crunch the data based upon the user's preferred
# statistics (author or committer) and store them. We also store all records
# with an (Unknown) affiliation for display to the user.

	update_status('Caching data for display')
	log_activity('Info','Caching unknown affiliations and web data for display')

	report_date = get_setting('report_date')
	report_attribution = get_setting('report_attribution')

	# Clear stale caches

	clear_project_weekly_cache = ("DELETE c.* FROM project_weekly_cache c "
		"JOIN projects p ON c.projects_id = p.id WHERE "
		"p.recache=TRUE")
	cursor.execute(clear_project_weekly_cache)
	db.commit()

	clear_project_monthly_cache = ("DELETE c.* FROM project_monthly_cache c "
		"JOIN projects p ON c.projects_id = p.id WHERE "
		"p.recache=TRUE")
	cursor.execute(clear_project_monthly_cache)
	db.commit()

	clear_project_annual_cache = ("DELETE c.* FROM project_annual_cache c "
		"JOIN projects p ON c.projects_id = p.id WHERE "
		"p.recache=TRUE")
	cursor.execute(clear_project_annual_cache)
	db.commit()

	clear_repo_weekly_cache = ("DELETE c.* FROM repo_weekly_cache c "
		"JOIN repos r ON c.repos_id = r.id "
		"JOIN projects p ON r.projects_id = p.id WHERE "
		"p.recache=TRUE")
	cursor.execute(clear_repo_weekly_cache)
	db.commit()

	clear_repo_monthly_cache = ("DELETE c.* FROM repo_monthly_cache c "
		"JOIN repos r ON c.repos_id = r.id "
		"JOIN projects p ON r.projects_id = p.id WHERE "
		"p.recache=TRUE")
	cursor.execute(clear_repo_monthly_cache)
	db.commit()

	clear_repo_annual_cache = ("DELETE c.* FROM repo_annual_cache c "
		"JOIN repos r ON c.repos_id = r.id "
		"JOIN projects p ON r.projects_id = p.id WHERE "
		"p.recache=TRUE")
	cursor.execute(clear_repo_annual_cache)
	db.commit()

	clear_unknown_cache = ("DELETE c.* FROM unknown_cache c "
		"JOIN projects p ON c.projects_id = p.id WHERE "
		"p.recache=TRUE")
	cursor.execute(clear_unknown_cache)
	db.commit()

	log_activity('Verbose','Caching unknown authors and committers')

	# Cache the unknown authors

	unknown_authors = ("INSERT INTO unknown_cache "
		"SELECT 'author', "
		"r.projects_id, "
		"a.author_email, "
		"SUBSTRING_INDEX(a.author_email,'@',-1), "
		"SUM(a.added) "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"WHERE a.author_affiliation = '(Unknown)' "
		"AND p.recache = TRUE "
		"GROUP BY r.projects_id,a.author_email")

	cursor.execute(unknown_authors)
	db.commit()

	# Cache the unknown committers

	unknown_committers = ("INSERT INTO unknown_cache "
		"SELECT 'committer', "
		"r.projects_id, "
		"a.committer_email, "
		"SUBSTRING_INDEX(a.committer_email,'@',-1), "
		"SUM(a.added) "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"WHERE a.committer_affiliation = '(Unknown)' "
		"AND p.recache = TRUE "
		"GROUP BY r.projects_id,a.committer_email")

	cursor.execute(unknown_committers)
	db.commit()

	# Start caching by project

	log_activity('Verbose','Caching projects')

	cache_projects_by_week = ("INSERT INTO project_weekly_cache "
		"SELECT r.projects_id AS projects_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"WEEK(a.%s_date) AS week, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY week, "
		"year, "
		"affiliation, "
		"a.%s_email,"
		"projects_id"
		% (report_attribution,report_attribution,
		report_date,report_date,report_attribution))

	cursor.execute(cache_projects_by_week)
	db.commit()

	cache_projects_by_month = ("INSERT INTO project_monthly_cache "
		"SELECT r.projects_id AS projects_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"MONTH(a.%s_date) AS month, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY month, "
		"year, "
		"affiliation, "
		"a.%s_email,"
		"projects_id"
		% (report_attribution,report_attribution,
		report_date,report_date,report_attribution))

	cursor.execute(cache_projects_by_month)
	db.commit()

	cache_projects_by_year = ("INSERT INTO project_annual_cache "
		"SELECT r.projects_id AS projects_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY year, "
		"affiliation, "
		"a.%s_email,"
		"projects_id"
		% (report_attribution,report_attribution,
		report_date,report_attribution))

	cursor.execute(cache_projects_by_year)
	db.commit()

	# Start caching by repo

	log_activity('Verbose','Caching repos')

	cache_repos_by_week = ("INSERT INTO repo_weekly_cache "
		"SELECT a.repos_id AS repos_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"WEEK(a.%s_date) AS week, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY week, "
		"year, "
		"affiliation, "
		"a.%s_email,"
		"repos_id"
		% (report_attribution,report_attribution,
		report_date,report_date,report_attribution))

	cursor.execute(cache_repos_by_week)
	db.commit()

	cache_repos_by_month = ("INSERT INTO repo_monthly_cache "
		"SELECT a.repos_id AS repos_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"MONTH(a.%s_date) AS month, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY month, "
		"year, "
		"affiliation, "
		"a.%s_email,"
		"repos_id"
		% (report_attribution,report_attribution,
		report_date,report_date,report_attribution))

	cursor.execute(cache_repos_by_month)
	db.commit()

	cache_repos_by_year = ("INSERT INTO repo_annual_cache "
		"SELECT a.repos_id AS repos_id, "
		"a.%s_email AS email, "
		"a.%s_affiliation AS affiliation, "
		"YEAR(a.%s_date) AS year, "
		"SUM(a.added) AS added, "
		"SUM(a.removed) AS removed, "
		"SUM(a.whitespace) AS whitespace, "
		"COUNT(DISTINCT a.filename) AS files, "
		"COUNT(DISTINCT a.commit) AS patches "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"JOIN projects p ON p.id = r.projects_id "
		"LEFT JOIN exclude e ON "
			"(a.author_email = e.email "
				"AND (e.projects_id = r.projects_id "
					"OR e.projects_id = 0)) "
			"OR (a.author_email LIKE CONCAT('%%',e.domain) "
				"AND (e.projects_id = r.projects_id "
				"OR e.projects_id = 0)) "
		"WHERE e.email IS NULL "
		"AND e.domain IS NULL "
		"AND p.recache = TRUE "
		"GROUP BY year, "
		"affiliation, "
		"a.%s_email,"
		"repos_id"
		% (report_attribution,report_attribution,
		report_date,report_attribution))

	cursor.execute(cache_repos_by_year)
	db.commit()

	# Reset cache flags

	reset_recache = "UPDATE projects SET recache = FALSE"
	cursor.execute(reset_recache)
	db.commit()

	log_activity('Info','Caching unknown affiliations and web data for display (complete)')

### The real program starts here ###

# Set up the database

try:
	config = configparser.ConfigParser()
	config.read(os.path.join(os.path.dirname(__file__),'db.cfg'))

	# Read in the general connection info

	db_user = config['main_database']['user']
	db_pass = config['main_database']['pass']
	db_name = config['main_database']['name']
	db_host = config['main_database']['host']

	# Read in the people connection info

	db_user_people = config['people_database']['user']
	db_pass_people = config['people_database']['pass']
	db_name_people = config['people_database']['name']
	db_host_people = config['people_database']['host']

except:
	# If the config import fails, check if there's an older style db.py

	db_user,db_pass,db_name,db_host,db_user_people,db_pass_people,db_name_people,db_host_people = migrate_database_config()

# Open a general-purpose connection

db,cursor = database_connection(
	db_host,
	db_user,
	db_pass,
	db_name)

# Open a connection for the people database

db_people,cursor_people = database_connection(
	db_host_people,
	db_user_people,
	db_pass_people,
	db_name_people)

# Figure out how much we're going to log
log_level = get_setting('log_level')

# Check if the database is current and update it if necessary
try:
	current_db = int(get_setting('database_version'))
except:
	# Catch databases which existed before database versioning
	current_db = -1

if current_db < upstream_db:

	print(("Current database version: %s\nUpstream database version %s\n" %
		(current_db, upstream_db)))

	update_db(current_db);

# Figure out what we need to do
limited_run = 0
delete_marked_repos = 0
pull_repos = 0
clone_repos = 0
check_updates = 0
force_updates = 0
run_analysis = 0
force_analysis = 0
nuke_stored_affiliations = 0
fix_affiliations = 0
force_invalidate_caches = 0
rebuild_caches = 0
force_invalidate_caches = 0
create_xlsx_summary_files = 0
multithreaded = 1

opts,args = getopt.getopt(sys.argv[1:],'hdpcuUaAmnfIrx')
for opt in opts:
	if opt[0] == '-h':
		print("\nfacade-worker.py does everything by default except invalidating caches\n"
				"and forcing updates, unless invoked with one of the following options.\n"
				"In those cases, it will only do what you have selected.\n\n"
				"Options:\n"
				"	-d	Delete marked repos\n"
				"	-c	Run 'git clone' on new repos\n"
				"	-u	Check if any repos should be marked for updating\n"
				"	-U	Force all repos to be marked for updating\n"
				"	-p	Run 'git pull' on repos\n"
				"	-a	Analyze git repos\n"
				"	-A	Force all repos to be analyzed\n"
				"	-m	Disable multithreaded mode (but why?)\n"
				"	-n	Nuke stored affiliations (if mappings modified by hand)\n"
				"	-f	Fill empty affiliations\n"
				"	-I	Invalidate caches\n"
				"	-r	Rebuild unknown affiliation and web caches\n"
				"	-x	Create Excel summary files\n\n")
		sys.exit(0)

	elif opt[0] == '-d':
		delete_marked_repos = 1
		limited_run = 1
		log_activity('Info','Option set: delete marked repos.')

	elif opt[0] == '-c':
		clone_repos = 1
		limited_run = 1
		log_activity('Info','Option set: clone new repos.')

	elif opt[0] == '-u':
		check_updates = 1
		limited_run = 1
		log_activity('Info','Option set: checking for repo updates')

	elif opt[0] == '-U':
		force_updates = 1
		log_activity('Info','Option set: forcing repo updates')

	elif opt[0] == '-p':
		pull_repos = 1
		limited_run = 1
		log_activity('Info','Option set: update repos.')

	elif opt[0] == '-a':
		run_analysis = 1
		limited_run = 1
		log_activity('Info','Option set: running analysis.')

	elif opt[0] == '-A':
		force_analysis = 1
		run_analysis = 1
		limited_run = 1
		log_activity('Info','Option set: forcing analysis.')

	elif opt[0] == '-m':
		multithreaded = 0
		log_activity('Info','Option set: disabling multithreading.')

	elif opt[0] == '-n':
		nuke_stored_affiliations = 1
		limited_run = 1
		log_activity('Info','Option set: nuking all affiliations')

	elif opt[0] == '-f':
		fix_affiliations = 1
		limited_run = 1
		log_activity('Info','Option set: fixing affiliations.')

	elif opt[0] == '-I':
		force_invalidate_caches = 1
		limited_run = 1
		log_activity('Info','Option set: Invalidate caches.')

	elif opt[0] == '-r':
		rebuild_caches = 1
		limited_run = 1
		log_activity('Info','Option set: rebuilding caches.')

	elif opt[0] == '-x':
		create_xlsx_summary_files = 1
		limited_run = 1
		log_activity('Info','Option set: creating Excel summary files.')

# Get the location of the directory where git repos are stored
repo_base_directory = get_setting('repo_directory')

# Determine if it's safe to start the script
current_status = get_setting('utility_status')

if current_status != 'Idle':
	log_activity('Error','Something is already running, aborting maintenance '
		'and analysis.\nIt is unsafe to continue.')
	sys.exit(1)

if len(repo_base_directory) == 0:
	log_activity('Error','No base directory. It is unsafe to continue.')
	update_status('Failed: No base directory')
	sys.exit(1)

# Begin working

start_time = time.time()
log_activity('Quiet','Running facade-worker.py')

if not limited_run or (limited_run and delete_marked_repos):
	git_repo_cleanup()

if not limited_run or (limited_run and clone_repos):
	git_repo_initialize()

if not limited_run or (limited_run and check_updates):
	check_for_repo_updates()

if force_updates:
	force_repo_updates()

if not limited_run or (limited_run and pull_repos):
	git_repo_updates()

if force_analysis:
	force_repo_analysis()

if not limited_run or (limited_run and run_analysis):
	analysis()

if nuke_stored_affiliations:
	nuke_affiliations()

if not limited_run or (limited_run and fix_affiliations):
	fill_empty_affiliations()

if force_invalidate_caches:
	invalidate_caches()

if not limited_run or (limited_run and rebuild_caches):
	rebuild_unknown_affiliation_and_web_caches()

if not limited_run or (limited_run and create_xlsx_summary_files):

	log_activity('Info','Creating summary Excel files')

	from excel_generators import *

	log_activity('Info','Creating summary Excel files (complete)')

# All done

update_status('Idle')
log_activity('Quiet','facade-worker.py completed')

elapsed_time = time.time() - start_time

print('\nCompleted in %s\n' % datetime.timedelta(seconds=int(elapsed_time)))

cursor.close()
cursor_people.close()
db.close()
db_people.close()
