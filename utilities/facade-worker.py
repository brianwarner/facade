#!/usr/bin/python

# Copyright 2016 Brian Warner
#
# This file is part of Facade, and is made available under the terms of the GNU
# General Public License version 2.
#
# SPDX-License-Identifier:        GPL-2.0

# Git repo maintenance
#
# This script is responsible for cloning new repos and keeping existing repos up
# to date. It can be run as often as you want (and will detect when it's
# already running, so as not to spawn parallel processes), but once or twice per
# day should be more than sufficient. Each time it runs, it updates the repo
# and checks for any parents of HEAD that aren't already accounted for in the
# repos. It also rebuilds cache data for display.
#
# If for whatever reason you manually update the affiliations table in the
# database, be sure to run with the -n flag to "nuke" all existing affiliation
# data. It will be rebuilt the next time facade-worker.py runs.

import sys
import MySQLdb
import imp

try:
	imp.find_module('db')
	from db import db,cursor
except:
	sys.exit("Can't find db.py. Have you created it?")

import HTMLParser
html = HTMLParser.HTMLParser()

import subprocess
import os
import getopt

global log_level

#### Helpers ####

def get_setting(setting):

# Get a setting from the database

	query = ("SELECT value FROM settings WHERE setting='%s' ORDER BY "
		"last_modified DESC LIMIT 1" % setting)
	cursor.execute(query)
	return cursor.fetchone()["value"]

def update_status(status):

# Update the status displayed in the UI

	query = ("UPDATE settings SET value='%s' WHERE setting='utility_status'"
		% status)
	cursor.execute(query)
	db.commit()

def log_activity(level,status):

# Log an activity based upon urgency and user's preference

	log_options = ('Error','Quiet','Info','Verbose')

	if log_options.index(level) <= log_options.index(log_level):
		query = ("INSERT INTO utility_log (level,status) VALUES ('%s','%s')"
			% (level,status))
		cursor.execute(query)
		db.commit()
		sys.stderr.write("* %s\n" % status)

def update_repo_log(repos_id,status):

# Log a repo's fetch status

	log_message = ("INSERT INTO repos_fetch_log (repos_id,status) "
		"VALUES (%s,'%s')" % (repos_id,status))

	cursor.execute(log_message)
	db.commit()

def update_analysis_log(repos_id,status):

# Log a repo's analysis status

	log_message = ("INSERT INTO analysis_log (repos_id,status) "
		"VALUES (%s,'%s')" % (repos_id,status))

	cursor.execute(log_message)
	db.commit()
def check_swapped_emails(name,email):

# Sometimes people mix up their name and email in their git settings

	if name.find('@') >=0 and email.find('@') == -1:
		return email,name
	else:
		return name,email

def strip_extra_amp(email):

# Some repos have multiple ampersands, which really messes up domain pattern
# matching. This extra info is not used, so we discard it.

	if email.count('@') > 1:
		return email[:email.find('@',email.find('@')+1)]
	else:
		return email

def discover_alias(email):

# Match aliases with their canonical email

	alias = "SELECT canonical FROM aliases WHERE alias='%s'" % email

	cursor.execute(alias)
	db.commit()

	if cursor.rowcount:
		return cursor.fetchone()["canonical"]
	else:
		return email

def discover_affiliation(email,date):

# Attempt to match email with who they were working for when the patch was
# authored or committed

	# First, see if there's an exact match
	match = ("SELECT affiliation FROM affiliations "
		"WHERE domain='%s' AND start_date < '%s' "
		"ORDER BY start_date DESC LIMIT 1" % (email,date))

	cursor.execute(match)
	db.commit()

	if cursor.rowcount:
		return cursor.fetchone()["affiliation"]

	# If we couldn't find an obvious match, try to match a pattern
	if email.find('@') >= 0:
		domain = email[email.find('@')+1:]
	else:
		# If it's not a properly formatted email, give up
		return '(Unknown)'

	# Now we go for a domain-level match
	match = ("SELECT affiliation FROM affiliations "
		"WHERE domain='%s' AND start_date < '%s' "
		"ORDER BY start_date ASC LIMIT 1" % (domain,date))

	cursor.execute(match)
	db.commit()

	if cursor.rowcount:
		return cursor.fetchone()["affiliation"]
	else:
		return '(Unknown)'

def store_working_commit(repo_id,commit):

# Store the working commit.

	store_commit = ("UPDATE repos "
		"SET working_commit = '%s' "
		"WHERE id = %s"
		% (commit,repo_id))

	cursor.execute(store_commit)
	db.commit()

def trim_commit(repo_id,commit):

# Quickly remove a given commit

	remove_commit = ("DELETE FROM analysis_data "
		"WHERE repos_id=%s AND commit='%s'" %
		(repo_id,commit))

	cursor.execute(remove_commit)
	db.commit()

def analyze_commit(repo_id,repo_loc,commit):

# This function analyzes a given commit, counting the additions, removals, and
# whitespace changes. It collects all of the metadata about the commit, and
# stashes it in the database.

	header = True
	filename = ''
	filename = ''
	added = 0
	removed = 0
	whitespace = 0

	git_log = subprocess.Popen(["git --git-dir %s log -p -M %s -n1 "
		"--pretty=format:'" 
		"author_name: %%an%%nauthor_email: %%ae%%nauthor_date:%%ai%%n"
		"committer_name: %%cn%%ncommitter_email: %%ce%%ncommitter_date: %%ci%%n"
		"parents: %%p%%nEndPatch' "
		% (repo_loc,commit)], stdout=subprocess.PIPE, shell=True)

	# Stash the commit we're going to analyze so we can back it out if something
	# goes wrong later.

	store_working_commit(repo_id,commit)

	for line in git_log.stdout.read().split(os.linesep):
		if len(line) > 0:

			if line.find('author_name:') == 0:
				author_name = line[13:].replace("'","\\'")
				continue

			if line.find('author_email:') == 0:
				author_email = line[14:].replace("'","\\'")
				continue

			if line.find('author_date:') == 0:
 				author_date = line[12:22]
				continue

			if line.find('committer_name:') == 0:
				committer_name = line[16:].replace("'","\\'")
				continue

			if line.find('committer_email:') == 0:
				committer_email = line[17:].replace("'","\\'")
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

			if line.find('--- ') == 0:
				if filename == '(Deleted) ':
					filename = filename + line[6:]
				continue

			if line.find('+++ ') == 0:
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

def store_commit(repos_id,commit,filename,
	author_name,author_email,author_date,
	committer_name,committer_email,committer_date,
	added,removed, whitespace):

# Fix some common issues in git commit logs and store data

	# Sometimes git is misconfigured and name/email get swapped
	author_name, author_email = check_swapped_emails(author_name,author_email)
	committer_name,committer_email = check_swapped_emails(committer_name,committer_email)

	# Some systems append extra info after a second @
	author_email = strip_extra_amp(author_email)
	committer_email = strip_extra_amp(committer_email)

	# Check if there's a known alias for this email
	author_email = discover_alias(author_email)
	committer_email = discover_alias(committer_email)

	store = ("INSERT INTO analysis_data (repos_id,commit,filename,"
		"author_name,author_email,author_date,"
		"committer_name,committer_email,committer_date,"
		"added,removed,whitespace) VALUES ("
		"%s,'%s','%s','%s','%s','%s','%s','%s','%s',%s,%s,%s)"
		% (repos_id,commit,filename,
		author_name,author_email,author_date,
		committer_name,committer_email,committer_date,
		added,removed,whitespace))

	cursor.execute(store)
	db.commit()

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

		cmd = ("rm -rf %s%s/%s%s"
			% (repo_base_directory,row['projects_id'],row['path'],row['name']))

		return_code = subprocess.Popen([cmd],shell=True).wait()

		query = "DELETE FROM repos WHERE id=%s" % row['id']
		cursor.execute(query)
		db.commit()

		log_activity('Verbose','Deleted repo %s' % row['id'])

		cleanup = '%s/%s%s' % (row['projects_id'],row['path'],row['name'])

		# Attempt to cleanup any empty parent directories
		while (cleanup.find('/',0) > 0):
			cleanup = cleanup[:cleanup.rfind('/',0)]

			cmd = "rmdir %s%s" % (repo_base_directory,cleanup)
			subprocess.Popen([cmd],shell=True).wait()
			log_activity('Verbose','Attempted %s' % cmd)

		update_repo_log(row['id'],'Deleted')

	log_activity('Info','Processing deletions (complete)')

def git_repo_updates():

# Update existing repos

	update_status('Updating repos')
	log_activity('Info','Updating existing repos')

	repo_base_directory = get_setting('repo_directory')

	query = ("SELECT id,projects_id,git,name,path FROM repos WHERE "
		"status='Active'");
	cursor.execute(query)

	existing_repos = list(cursor)

	for row in existing_repos:

		log_activity('Verbose','Attempting to update %s' % row['git'])
		update_repo_log(row['id'],'Updating')

		cmd = ("git -C %s%s/%s%s pull"
			% (repo_base_directory,row['projects_id'],row['path'],row['name']))

		return_code = subprocess.Popen([cmd],shell=True).wait()

		if return_code == 0:
			update_repo_log(row['id'],'Up-to-date')
			log_activity('Verbose','Updated %s' % row["git"])
		else:
			update_repo_log(row['id'],'Failed (%s)' % return_code)
			log_activity('Error','Could not update %s' % row["git"])

	log_activity('Info','Updating existing repos (complete)')

def git_repo_initialize():

# Select any new git repos so we can set up their locations and git clone

	update_status('Fetching new repos')
	log_activity('Info','Fetching new repos')

	query = "SELECT id,projects_id,git FROM repos WHERE status LIKE 'New%'";
	cursor.execute(query)

	new_repos = list(cursor)

	for row in new_repos:
		print row["git"]
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
		query = ("SELECT NULL FROM repos WHERE CONCAT(projects_id,'/',path,name) "
			"='%s/%s%s'" % (row["projects_id"],repo_relative_path,repo_name))
		cursor.execute(query)
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

			update_repo_log(row['id'],'Failed (mkdir %s)' % repo_path)
			update_status('Failed (mkdir %s)' % repo_path)
			log_activity('Error','Could not create repo directory: %s' %
				repo_path)

			sys.exit("Could not create git repo's prerequisite directories. "
				" Do you have write access?")

		update_repo_log(row['id'],'New (cloning)')

		query = ("UPDATE repos SET status='New (Initializing)', path='%s', "
			"name='%s' WHERE id=%s"	% (repo_relative_path,repo_name,row["id"]))

		cursor.execute(query)
		db.commit()

		log_activity('Verbose','Cloning: %s' % git)

		cmd = "git -C %s clone '%s' %s" % (repo_path,git,repo_name)
		return_code = subprocess.Popen([cmd], shell=True).wait()

		if (return_code == 0):
			# If cloning succeeded, repo is ready for analysis
			query = ("UPDATE repos SET status='Active',path='%s', name='%s' "
				"WHERE id=%s" % (repo_relative_path,repo_name,row["id"]))

			cursor.execute(query)
			db.commit()

			update_repo_log(row['id'],'Up-to-date')
			log_activity('Info','Cloned %s' % git)

		else:
			# If cloning failed, log it and set the status back to new
			update_repo_log(row['id'],'Failed (%s)' % return_code)

			query = ("UPDATE repos SET status='New (failed)' WHERE id=%s"
				% row["id"])

			cursor.execute(query)
			db.commit()

			log_activity('Error','Could not clone %s' % git)

	log_activity('Info', 'Fetching new repos (complete)')

def analysis():

# Run the analysis by looping over all active repos. For each repo, we retrieve
# the list of commits which lead to HEAD. If any are missing from the database,
# they are filled in. Then we check to see if any commits in the database are
# not in the list of parents, and prune them out.
#
# We also keep track of the last commit to be processed, so that if the analysis
# is interrupted (possibly leading to partial data in the database for the
# commit being analyzed at the time) we can recover.

	update_status('Running analysis')
	log_activity('Info','Beginning analysis')

	start_date = get_setting('start_date')

	repo_list = "SELECT id FROM repos WHERE status='Active'"
	cursor.execute(repo_list)
	repos = list(cursor)

	for repo in repos:

		update_analysis_log(repo['id'],'Beginning analysis')

		# First we check to see if the previous analysis didn't complete

		get_status = ("SELECT working_commit FROM repos WHERE id=%s" %
			repo['id'])

		cursor.execute(get_status)
		working_commit = cursor.fetchone()['working_commit']

		# If there's a commit still there, the previous run was interrupted and
		# the commit data may be incomplete. It should be trimmed, just in case.

		if working_commit:
			trim_commit(repo['id'],working_commit)
			store_working_commit(repo['id'],'')

		# Start the main analysis

		update_analysis_log(repo['id'],'Collecting data')

		query = ("SELECT projects_id,path,name FROM repos WHERE id=%s"
			% repo['id'])

		cursor.execute(query)
		repo_detail = cursor.fetchone()

		repo_loc = ('%s%s/%s%s/.git' % (repo_base_directory,
			repo_detail["projects_id"], repo_detail["path"],
			repo_detail["name"]))

		# Grab the parents of HEAD

		parents = subprocess.Popen(["git --git-dir %s log --ignore-missing "
			"--pretty=format:'%%H' --since=%s" % (repo_loc,start_date)],
			stdout=subprocess.PIPE, shell=True)

		parent_commits = set(parents.stdout.read().split(os.linesep))

		# Grab the existing commits from the database

		existing_commits = set()

		find_existing = ("SELECT DISTINCT commit FROM analysis_data WHERE repos_id=%s" %
			repo['id'])

		cursor.execute(find_existing)

		for commit in list(cursor):
			existing_commits.add(commit['commit'])

		# Find missing commits and add them

		missing_commits = parent_commits - existing_commits

		for commit in missing_commits:

			analyze_commit(repo['id'],repo_loc,commit)

			store_working_commit(repo['id'],'')

		update_analysis_log(repo['id'],'Data collection complete')

		update_analysis_log(repo['id'],'Beginning to trim commits')

		# Find commits which are out of the analysis range

		trimmed_commits = existing_commits - parent_commits

		for commit in trimmed_commits:

			trim_commit(repo['id'],commit)

		update_analysis_log(repo['id'],'Commit trimming complete')

	update_analysis_log(repo['id'],'Analysis complete')
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

	update_status('Filling empty affiliations')
	log_activity('Info','Filling empty affiliations')

	find_null_authors = ("SELECT author_email,author_date "
		"FROM analysis_data "
		"WHERE author_affiliation IS NULL")

	cursor.execute(find_null_authors)

	authors = list(cursor)

	for author in authors:
		affiliation = discover_affiliation(author['author_email'],author['author_date'])

		update = ("UPDATE analysis_data SET author_affiliation = '%s' "
			"WHERE author_email = '%s' AND author_date = '%s'"
			% (affiliation,author['author_email'],author['author_date']))

		cursor.execute(update)
		db.commit()

	find_null_committers = ("SELECT committer_email,committer_date "
		"FROM analysis_data "
		"WHERE committer_affiliation IS NULL")

	cursor.execute(find_null_committers)
	committers = list(cursor)

	for committer in committers:
		affiliation = discover_affiliation(committer['committer_email'],committer['committer_date'])

		update = ("UPDATE analysis_data SET committer_affiliation = '%s' "
			"WHERE committer_email = '%s' AND committer_date = '%s'"
			% (affiliation,committer['committer_email'],committer['committer_date']))

		cursor.execute(update)
		db.commit()

	log_activity('Info','Filling empty affiliations (complete)')

def rebuild_unknown_affiliation_and_web_caches():

# When there's a lot of analysis data, calculating display data on the fly gets
# pretty expensive. Instead, we crunch the data based upon the user's preferred
# statistics (author or committer) and store them. We also store all records
# with an (Unknown) affiliation for display to the user.

	update_status('Caching data for display')
	log_activity('Info','Caching unknown affiliations and web data for display (complete)')

	# Create a temporary table for each cache, so we can swap in place.

	query = "CREATE TABLE IF NOT EXISTS uc LIKE unknown_cache"

	cursor.execute(query)
	db.commit()

	query = "CREATE TABLE IF NOT EXISTS pmc LIKE project_monthly_cache";

	cursor.execute(query)
	db.commit()

	query = "CREATE TABLE IF NOT EXISTS pac LIKE project_annual_cache";

	cursor.execute(query)
	db.commit()

	query = "CREATE TABLE IF NOT EXISTS rmc LIKE repo_monthly_cache";

	cursor.execute(query)
	db.commit()

	query = "CREATE TABLE IF NOT EXISTS rac LIKE repo_annual_cache";

	cursor.execute(query)
	db.commit()

	# Swap in place, just in case someone's using the web UI at this moment.

	query = ("RENAME TABLE unknown_cache TO uc_old, "
		"uc TO unknown_cache, "
		"project_monthly_cache TO pmc_old, "
		"pmc TO project_monthly_cache, "
		"project_annual_cache TO pac_old, "
		"pac TO project_annual_cache, "
		"repo_monthly_cache TO rmc_old, "
		"rmc TO repo_monthly_cache, "
		"repo_annual_cache TO rac_old, "
		"rac TO repo_annual_cache")

	cursor.execute(query)
	db.commit()

	# Get rid of the old tables.

	query = ("DROP TABLE uc_old, "
		"pmc_old, "
		"pac_old, "
		"rmc_old, "
		"rac_old")

	cursor.execute(query)
	db.commit()

	report_date = get_setting('report_date')
	report_attribution = get_setting('report_attribution')

	# Cache unknowns

	unknown_authors = ("SELECT r.projects_id AS projects_id, "
		"a.author_email AS email, "
		"SUM(a.added) AS added "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"WHERE a.author_affiliation = '(Unknown)' "
		"GROUP BY r.projects_id,a.author_email")

	cursor.execute(unknown_authors)
	unknowns = list(cursor)

	for unknown in unknowns:

		# Isolate the domain name, and add the lines of code associated with it
		query = ("INSERT INTO unknown_cache (type,projects_id,email,domain,added) "
			"VALUES ('author',%s,'%s','%s',%s)" % (unknown["projects_id"],
			unknown["email"].replace("'","\\'"),
			unknown["email"][unknown["email"].find('@') + 1:].replace("'","\\'"),
			unknown["added"]))

		cursor.execute(query)
		db.commit()

	unknown_committers = ("SELECT r.projects_id AS projects_id, "
		"a.committer_email AS email, "
		"SUM(a.added) AS added "
		"FROM analysis_data a "
		"JOIN repos r ON r.id = a.repos_id "
		"WHERE a.committer_affiliation = '(Unknown)' "
		"GROUP BY r.projects_id,a.committer_email")

	cursor.execute(unknown_committers)
	unknowns = list(cursor)

	for unknown in unknowns:

		# Isolate the domain name, and add the lines of code associated with it
		query = ("INSERT INTO unknown_cache (type,projects_id,email,domain,added) "
			"VALUES ('committer',%s,'%s','%s',%s)" % (unknown["projects_id"],
			unknown["email"].replace("'","\\'"),
			unknown["email"][unknown["email"].find('@') + 1:].replace("'","\\'"),
			unknown["added"]))

		cursor.execute(query)
		db.commit()

	# Start caching by project

	query = "SELECT id FROM projects"

	cursor.execute(query)
	projects = list(cursor)

	for project in projects:

		# Cache monthly data by project

		get_emails = ("SELECT DISTINCT a.%s_email AS email "
			"FROM analysis_data a "
			"JOIN repos r ON r.id = a.repos_id "
			"LEFT JOIN exclude e ON "
				"(a.author_email = e.email "
					"AND (r.projects_id = e.projects_id "
						"OR e.projects_id = 0)) "
				"OR (a.author_email LIKE CONCAT('%%',e.domain) "
					"AND (r.projects_id = e.projects_id "
					"OR e.projects_id = 0)) "
			"WHERE r.projects_id=%s "
			"AND e.email IS NULL "
			"AND e.domain IS NULL"
			% (report_attribution,project['id']))

		cursor.execute(get_emails)
		non_excluded_emails = list(cursor)

		for email in non_excluded_emails:

			# Cache monthly by project

			get_stats = ("INSERT INTO project_monthly_cache "
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
				"WHERE a.%s_email='%s' "
				"AND r.projects_id = %s "
				"GROUP BY month, "
				"year, "
				"affiliation, "
				"email" 
				% (report_attribution,report_attribution,
				report_date,report_date,report_attribution,
				email['email'],project['id']))

			cursor.execute(get_stats)
			db.commit()
	
			# Cache annually by project

			get_stats = ("INSERT INTO project_annual_cache "
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
				"WHERE a.%s_email='%s' "
				"AND r.projects_id = %s "
				"GROUP BY year, "
				"affiliation, "
				"email" 
				% (report_attribution,report_attribution,
				report_date,report_attribution,
				email['email'],project['id']))

			cursor.execute(get_stats)
			db.commit()

	# Start caching by repo

	query = "SELECT id FROM repos"

	cursor.execute(query)
	repos = list(cursor)

	for repo in repos:

		# Cache monthly data by project

		get_emails = ("SELECT DISTINCT a.author_email AS email "
			"FROM analysis_data a "
			"JOIN repos r ON r.id = a.repos_id "
			"LEFT JOIN exclude e ON "
				"(a.author_email = e.email "
					"AND (r.projects_id = e.projects_id "
						"OR e.projects_id = 0)) "
				"OR (a.author_email LIKE CONCAT('%%',e.domain) "
					"AND (r.projects_id = e.projects_id "
					"OR e.projects_id = 0)) "
			"WHERE r.id=%s "
			"AND e.email IS NULL "
			"AND e.domain IS NULL"
			% repo['id'])

		cursor.execute(get_emails)
		non_excluded_emails = list(cursor)

		for email in non_excluded_emails:

			# Cache monthly by repo

			get_stats = ("INSERT INTO repo_monthly_cache "
				"SELECT repos_id, "
				"%s_email AS email, "
				"%s_affiliation AS affiliation, "
				"MONTH(%s_date) AS month, "
				"YEAR(%s_date) AS year, "
				"SUM(added) AS added, "
				"SUM(removed) AS removed, "
				"SUM(whitespace) AS whitespace, "
				"COUNT(DISTINCT filename) AS files, "
				"COUNT(DISTINCT commit) AS patches "
				"FROM analysis_data "
				"WHERE %s_email='%s' "
				"AND repos_id = %s "
				"GROUP BY month, "
				"year, "
				"affiliation, "
				"email" 
				% (report_attribution,report_attribution,
				report_date,report_date,report_attribution,
				email['email'],repo['id']))

			cursor.execute(get_stats)
			db.commit()
	
			# Cache annually by repo

			get_stats = ("INSERT INTO repo_annual_cache "
				"SELECT repos_id, "
				"%s_email AS email, "
				"%s_affiliation AS affiliation, "
				"YEAR(%s_date) AS year, "
				"SUM(added) AS added, "
				"SUM(removed) AS removed, "
				"SUM(whitespace) AS whitespace, "
				"COUNT(DISTINCT filename) AS files, "
				"COUNT(DISTINCT commit) AS patches "
				"FROM analysis_data "
				"WHERE %s_email='%s' "
				"AND repos_id = %s "
				"GROUP BY year, "
				"affiliation, "
				"email" % (report_attribution,report_attribution,
				report_date,report_attribution,
				email['email'],repo['id']))

			cursor.execute(get_stats)
			db.commit()

	log_activity('Info','Caching unknown affiliations and web data for display (complete)')
### The real program starts here ###

# Figure out how much we're going to log
log_level = get_setting('log_level')

# Figure out what we need to do
limited_run = 0
delete_marked_repos = 0
pull_repos = 0
clone_repos = 0
run_analysis = 0
nuke_stored_affiliations = 0
fix_affiliations = 0 #
rebuild_caches = 0

opts,args = getopt.getopt(sys.argv[1:],'hdpcanfr')
for opt in opts:
	if opt[0] == '-h':
		print("\nfacade-worker.py does everything by default, unless invoked\n"
				"with one of these options. In that case, it will only do what\n"
				"you have selected.\n\n"
				"Options:\n"
				"	-d	Delete marked repos\n"
				"	-p	Run 'git pull' on repos\n"
				"	-c	Run 'git clone' on new repos\n"
				"	-a	Analyze git repos\n"
				"	-n	Nuke stored affiliations (if mappings modified by hand)\n"
				"	-f	Fix affiliations when config files change\n"
				"	-r	Rebuild unknown affiliation and web caches\n\n")
		sys.exit(0)

	elif opt[0] == '-d':
		delete_marked_repos = 1
		limited_run = 1
		log_activity('Info','Option set: delete marked repos.')

	elif opt[0] == '-p':
		pull_repos = 1
		limited_run = 1
		log_activity('Info','Option set: update repos.')

	elif opt[0] == '-c':
		clone_repos = 1
		limited_run = 1
		log_activity('Info','Option set: clone new repos.')

	elif opt[0] == '-a':
		run_analysis = 1
		limited_run = 1
		log_activity('Info','Option set: running analysis.')

	elif opt[0] == '-n':
		nuke_stored_affiliations = 1
		limited_run = 1
		log_activity('Info','Option set: nuking all affiliations')

	elif opt[0] == '-f':
		fix_affiliations = 1
		limited_run = 1
		log_activity('Info','Option set: fixing affiliations.')

	elif opt[0] == '-r':
		rebuild_caches = 1
		limited_run = 1
		log_activity('Info','Option set: rebuilding caches.')

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
log_activity('Quiet','Running facade-worker.py')
if not limited_run or (limited_run and delete_marked_repos):
	git_repo_cleanup()

if not limited_run or (limited_run and pull_repos):
	git_repo_updates()

if not limited_run or (limited_run and clone_repos):
	git_repo_initialize()

if not limited_run or (limited_run and run_analysis):
	analysis()

if nuke_stored_affiliations:
	nuke_affiliations()

if not limited_run or (limited_run and fix_affiliations):
	fill_empty_affiliations()

if not limited_run or (limited_run and rebuild_caches):
	rebuild_unknown_affiliation_and_web_caches()

# All done

update_status('Idle')
log_activity('Quiet','facade-worker.py completed')

cursor.close()
db.close()
