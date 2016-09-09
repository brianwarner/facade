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
# to date.  It is intended to be run a few times per day, so that all repos are
# kept up to date should something unexpected happen (like a network failure)
# right before you try to run gitdm.

import sys
import MySQLdb
from database import db,cursor

import HTMLParser
html = HTMLParser.HTMLParser()

from subprocess import call
import time
import string
import random
import datetime
import csv
import hashlib
hasher = hashlib.md5()
import os

global log_level


def update_status(status):
	query = ("UPDATE settings SET value='%s' WHERE setting='utility_status'"
		% status)
	cursor.execute(query)
	db.commit()

def log_activity(level,activity):
	# Determine if something needs to be logged

	log_options = ('Error','Quiet','Info','Verbose')

	if log_options.index(level) <= log_options.index(log_level):
		query = ("INSERT INTO utility_log (level,status) VALUES ('%s','%s')"
			% (level,activity))
		cursor.execute(query)
		db.commit()

def get_setting(setting):
	query = ("SELECT value FROM settings WHERE setting='%s' ORDER BY "
		"last_modified DESC LIMIT 1" % setting)
	cursor.execute(query)
	return cursor.fetchone()["value"]

def git_repo_cleanup():
	# Clean up any git repos that are pending deletion

	update_status('Purging deleted repos')
	log_activity('Info','Repo maintenance: Processing deletions')

	repo_base_directory = get_setting('repo_directory')

	query = "SELECT id,projects_id,path,name FROM repos WHERE status='Delete'"
	cursor.execute(query)

	delete_repos = cursor.fetchall()

	for row in delete_repos:

		cmd = ("rm -rf %s%s/%s%s"
			% (repo_base_directory,row["projects_id"],row["path"],row["name"]))

		return_code = call(cmd,shell=True)

		query = "DELETE FROM repos WHERE id=%s" % row["id"]
		cursor.execute(query)
		db.commit()

		log_activity('Verbose','Repo maintenance: Deleted repo %s' % row["id"])

		cleanup = '%s/%s%s' % (row["projects_id"],row["path"],row["name"])

		# Attempt to cleanup any empty parent directories
		while (cleanup.find('/',0) > 0):
			cleanup = cleanup[:cleanup.rfind('/',0)]

			cmd = "rmdir %s%s" % (repo_base_directory,cleanup)
			call(cmd,shell=True)
			log_activity('Verbose','Repo maintenance: Attempted %s' % cmd)

	log_activity('Info','Repo maintenance: Processing deletions (complete)')

def git_repo_updates():
	# Now we need to update existing repos

	update_status('Updating repos')
	log_activity('Info','Repo maintenance: Updating existing repos')

	repo_base_directory = get_setting('repo_directory')

	query = ("SELECT id,projects_id,git,name,path FROM repos WHERE "
		"status='Active'");
	cursor.execute(query)

	existing_repos = cursor.fetchall()

	for row in existing_repos:

		cmd = ("git -C %s%s/%s%s pull"
			% (repo_base_directory,row["projects_id"],row["path"],row["name"]))
		return_code = call(cmd,shell=True)

		if return_code == 0:
			query = ("INSERT INTO repos_fetch_log (repos_id,status) values "
				"(%s,'Up-to-date')" % row["id"])
			cursor.execute(query)
			db.commit()
			log_activity('Verbose','Repo maintenance: Updated %s' % row["git"])
		else:
			query = ("INSERT INTO repos_fetch_log (repos_id,status) values "
				"(%s,'Failed (%s)')" % (row["id"],return_code))

			cursor.execute(query)
			db.commit()
			log_activity('Error','Repo maintenance: Could not update %s' % git)
	log_activity('Info','Repo maintenance: Updating existing repos (complete)')

def git_repo_initialize():
	# Select any new git repos so we can set up their locations and git clone)

	update_status('Fetching new repos')
	log_activity('Info','Repo maintenance: Fetching new repos')

	query = "SELECT id,projects_id,git FROM repos WHERE status LIKE 'New%'";
	cursor.execute(query)

	new_repos = cursor.fetchall()

	for row in new_repos:
		print row["git"]

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
		return_code = call('mkdir -p %s' % repo_path,shell=True)

		# Make sure it's ok to proceed
		if return_code != 0:
			print("COULD NOT CREATE REPO DIRECTORY")
			query = ("INSERT INTO repos_fetch_log (repos_id,status) VALUES "
				"(%s,'Failed (mkdir %s)')" % (row["id"],repo_path))
			print(query)
			cursor.execute(query)
			db.commit()
			update_status('Failed (mkdir %s)' % repo_path)
			log_activity('Error','Could not create repo directory: %s' %
				repo_path)
			sys.exit("Could not create git repo prerequisite directories. "
				" Do you have write access?")

		query = ("INSERT INTO repos_fetch_log (repos_id,status) VALUES (%s,"
			"'New (cloning)')" % row["id"])
		cursor.execute(query)
		db.commit()

		query = ("UPDATE repos SET status='New (Initializing)', path='%s', "
			"name='%s' WHERE id=%s"	% (repo_relative_path,repo_name,row["id"]))

		cursor.execute(query)
		db.commit()

		cmd = "git -C %s clone '%s' %s" % (repo_path,git,repo_name)

		return_code = call(cmd, shell=True)

		if (return_code == 0):
			# If cloning succeeded, repo is ready for gitdm
			query = ("UPDATE repos SET status='Active',path='%s', name='%s' "
				"WHERE id=%s" % (repo_relative_path,repo_name,row["id"]))

			cursor.execute(query)
			db.commit()

			query = ("INSERT INTO repos_fetch_log (repos_id,status) VALUES (%s,"
				"'Up-to-date')" % row["id"])

			cursor.execute(query)
			db.commit()
			log_activity('Info','Repo maintenance: Cloned %s' % git)

		else:
			# If cloning failed, log it and set the status back to new
			query = ("INSERT INTO repos_fetch_log (repos_id,status) VALUES (%s,"
				"'Failed (%s)')" % (row["id"],return_code))

			cursor.execute(query)
			db.commit()

			query = ("UPDATE repos SET status='New (failed)' WHERE id=%s"
				% row["id"])

			cursor.execute(query)
			db.commit()

			log_activity('Error','Repo maintenance: Could not clone %s' % git)

	log_activity('Info', 'Repo maintenance: Fetching new repos (complete)')

def gitdm_analysis():

	update_status('Running gitdm')
	log_activity('Info','gitdm: Running analysis')

	gitdm_loc = get_setting('gitdm')
	start_date = get_setting('start_date')
	end_date = get_setting('end_date')

	if end_date == 'yesterday':
		end_date = (datetime.date.today() -
			datetime.timedelta(days=1)).strftime("%Y-%m-%d")

	# Create temporary table with missing dates to find any backfills

	query = "CALL make_cal_table('%s','%s')" % (start_date, end_date);
	cursor.execute(query)
	db.commit()

	# Iterate over all repos and mark any dates that don't have a log entry as
	# "Pending" so we know which data needs to be calculated.

	query = "SELECT id FROM repos WHERE status='Active'";
	cursor.execute(query)
	repos = cursor.fetchall()

	for repo in repos:

		query = ("SELECT cal_table.date FROM cal_table LEFT JOIN "
				"(SELECT * FROM gitdm_master WHERE repos_id=%s) repo "
				"ON cal_table.date = repo.start_date "
				"WHERE repo.start_date IS NULL" % repo["id"])

		cursor.execute(query)
		missing_dates = cursor.fetchall()

		for date in missing_dates:

			query = ("INSERT INTO gitdm_master (repos_id,status,start_date) "
				"VALUES	(%s, 'Pending', '%s')" % (repo["id"],date["date"]))

			cursor.execute(query)
			db.commit()

	# Locate the repositories, get all of the "Pending" dates, and run gitdm

	query = "SELECT * FROM gitdm_master WHERE status='Pending'"
	cursor.execute(query)
	repos = cursor.fetchall()

	for repo in repos:
		# May want to update status to "working" in gitdm_master

		query = ("SELECT projects_id,path,name FROM repos WHERE id=%s"
			% repo["repos_id"])

		cursor.execute(query)
		repo_detail = cursor.fetchone()

		repo_loc = ('%s%s/%s%s/.git' % (repo_base_directory,
			repo_detail["projects_id"], repo_detail["path"],
			repo_detail["name"]))

		outfile = 'gitdm_results.tmp'

		end_date = str((datetime.datetime.strptime(repo["start_date"],'%Y-%m-%d')
			+ datetime.timedelta(days=1)).strftime('%Y-%m-%d'))

		gitdmcall = ('git --git-dir %s log -p -M --since=%s --before=%s --all '
			'| %s/gitdm -b %s -u -s -d -x %s' % (repo_loc, repo["start_date"],
			end_date, gitdm_loc, gitdm_loc, outfile))


		return_code = call(gitdmcall,shell=True)

		# Insert results into the gitdm_results table in the db.

		with open(outfile,"r") as file:
			reader = csv.reader(file,delimiter=',')

			# First we verify that the temp file matches what we expected

			header = next(reader)
			if ','.join(header) == 'Name,Email,Affliation,Date,Added,Removed,Changesets':

				for row in reader:
					name = row[0].replace("'","\\'")
					email = row[1].replace("'","\\'")
					affiliation = row[2].replace("'","\\'")
					added = row[4]
					removed = row[5]
					changesets = row[6]

					query = ("INSERT INTO gitdm_data (gitdm_master_id, name, "
							"email, affiliation, added, removed, changesets)"
						"VALUES (%s,'%s','%s','%s',%s,%s,%s)" % (repo["id"],
						name, email, affiliation, added, removed, changesets))

					cursor.execute(query)
					db.commit()

				query = ("UPDATE gitdm_master SET status='Complete' WHERE id=%s"
					% repo["id"])

				cursor.execute(query)
				db.commit()

				call('rm %s' % outfile,shell=True)

	log_activity('Info','Running gitdm analysis (complete)')

def purge_old_gitdm_data():
	# Trim data outside of the current start/end dates

	update_status('Trimming out-of-bounds data')
	log_activity('Info','Trimming out-of-bounds data')

	start_date = get_setting('start_date')
	end_date = get_setting('end_date')

	query = ("DELETE m,d FROM gitdm_master m "
		"LEFT JOIN gitdm_data d "
		"ON m.id=d.gitdm_master_id "
		"WHERE m.start_date < '%s' "
			"OR m.start_date > '%s'" % (start_date, end_date))

	cursor.execute(query)
	db.commit()

	log_activity('Info','Trimming out-of-bounds data (complete)')

def correct_modified_gitdm_affiliations():
	# Watch for changes in the gitdm config files that would change results

	update_status('Updating affiliations')
	log_activity('Info','Updating affiliations')

	gitdm_loc = get_setting('gitdm')

	for line in open('%sgitdm.config' % gitdm_loc):

		# Find all lines which are not commented and not empty
		if not line.strip().startswith('#') and not len(line.strip()) == 0:
			(configtype,configfile) = line.strip().split()

			# There are only certain configs that are relevant, we can ignore the rest
			if configtype == 'EmailAliases' or configtype == 'EmailMap':

				with open ('%s%s' % (gitdm_loc, configfile), 'rb') as file:
					hasher.update(file.read())

					# Determine if the file matches the current md5
					query = ("SELECT NULL FROM gitdm_configs "
						"WHERE configfile = '%s' "
						"AND md5sum = '%s' ORDER BY last_modified DESC"
						% (configfile,hasher.hexdigest()))

					cursor.execute(query)
					db.commit()

					if not cursor.rowcount:
						# No match found, process the file for differences

						mismatches = []
						cached_configfile = ('cached-configs/%s.cache'
							% configfile.replace('/','.'))

						# Only diff if file is already cached
						if os.path.isfile(cached_configfile):

							# Walk through file to figure out what is different
							for line_config in open(gitdm_loc + configfile):

								if not line_config.strip().startswith('#') and not len(line_config.strip()) == 0:

									line_match = False

									for line_cache in open(cached_configfile):

										if line_config == line_cache:
											line_match = True

									if not line_match:
										# Store mis-matches so we can process them.

										if line_config.find('#'):
											# Strip any comments in the line
											line_config = line_config[:line_config.find('#')]

										mismatches.append(line_config)

						else:

							# File isn't cached, so all of it must be stored

							for line_config in open('%s%s' % (gitdm_loc,configfile)):
								if not line_config.strip().startswith('#') and not len(line_config.strip()) == 0:
									# Store all entries in the file

									if line_config.find('#'):
										# Strip any comments in the line
										line_config = line_config[:line_config.find('#')]

									mismatches.append(line_config)

						# Now it's time to process the mismatches
						for mismatch in mismatches:

							if configtype == 'EmailAliases':

								# Grab the canonical email from the end of the string
								canonical = mismatch.split()[-1]

								# Grab everything up to the canonical email
								alias = mismatch[:mismatch.rfind(canonical)].strip()

								query = ("UPDATE gitdm_data SET email='%s' "
									"WHERE email='%s'"
									% (canonical.replace("'","\\'"),
									alias.replace("'","\\'")))

								cursor.execute(query)
								db.commit()

							if configtype == 'EmailMap':

								# Grab the domain or email from beginning of the string
								domain = mismatch.split()[0].replace("'","\\'")

								# Grab everything up to the affiliation
								affiliation = mismatch[len(domain):].strip().replace("'","\\'")
								query = ("UPDATE gitdm_data "
									"SET affiliation='%s' "
									"WHERE email LIKE '%%%s%%'"
									% (affiliation, domain))

								cursor.execute(query)
								db.commit()

						# Cache the file
						cmd = "cp %s%s %s" % (gitdm_loc, configfile,
							cached_configfile)

						return_code = call(cmd, shell=True)

						if return_code == 0:
							# Update hash so unchanged files can be ignored.
							hashstatus = "Complete"
						else:
							# Log as an error.
							hashstatus = "Incomplete"

						query = ("INSERT INTO gitdm_configs "
							"(configfile,configtype,md5sum,status) "
							"VALUES ('%s','%s','%s','%s')"
							% (configfile, configtype, hasher.hexdigest(),
							hashstatus))

						cursor.execute(query)
						db.commit()

	log_activity('Info','Updating affiliations (complete)')

def fix_funky_emails():
	# Some emails have two @, fix those

	update_status('Fixing funky emails')
	log_activity('Info','Fixing funky emails')

	query = "SELECT id,email FROM gitdm_data WHERE email LIKE '%@%@%'"
	cursor.execute(query)
	funky_emails = cursor.fetchall()

	for funky_email in funky_emails:

		# Trim everything to the right of the second @
		fixed_email = funky_email["email"][:funky_email["email"].rfind('@')]

		query = ("UPDATE gitdm_data "
			"SET email='%s' "
			"WHERE id='%s'" % (fixed_email, funky_email["id"]))

		cursor.execute(query)
		db.commit()

	log_activity('Info','Fixing funky emails (complete)')

def build_unknown_affiliation_cache():

	update_status('Caching unknown affiliations')
	log_activity('Info','Caching unknown affiliations')

	query = "DROP TABLE IF EXISTS unknown_cache"
	cursor.execute(query)
	unknowns = cursor.fetchall()

	query = ("CREATE TABLE unknown_cache "
		"(id INT AUTO_INCREMENT PRIMARY KEY, "
		"projects_id INT NOT NULL, "
		"email VARCHAR(64) NOT NULL, "
		"domain VARCHAR(64), "
		"added INT NOT NULL)")

	cursor.execute(query)
	db.commit()

	query = ("SELECT r.projects_id AS projects_id,d.email AS email,SUM(d.added) "
		"FROM repos r "
		"RIGHT JOIN gitdm_master m ON r.id = m.repos_id "
		"RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id "
		"WHERE d.affiliation = '(Unknown)' "
		"GROUP BY r.projects_id,d.email")

	cursor.execute(query)
	unknowns = cursor.fetchall()

	unknown_cache = {}

	for unknown in unknowns:

		# Isolate the domain name, and add the lines of code associated with it
		query = ("INSERT INTO unknown_cache (projects_id,email,domain,added) "
			"VALUES (%s,'%s','%s',%s)" % (unknown["projects_id"],
			unknown["email"], unknown["email"][unknown["email"].find('@') + 1:],
			unknown["SUM(d.added)"]))

		cursor.execute(query)
		db.commit()

	log_activity('Info','Caching unknown affiliations (complete)')


### The real program starts here ###

# Figure out how much we're going to log
log_level = get_setting('log_level')
log_activity('Quiet','facade-worker.py is about to start')

# Get the location of the directory where git repos are stored
repo_base_directory = get_setting('repo_directory')

# Determine if it's safe to start the script
current_status = get_setting('utility_status')

if current_status != 'Idle':
	log_activity('Error','Already running, aborting maintenance and analysis.')
	sys.exit("Something is already running.  It is unsafe to continue.")

if len(repo_base_directory) == 0:
	log_activity('Error','No base directory. It is unsafe to continue.')
	update_status('Failed: No base directory')
	log_activity('Error','No base directory defined.')
	sys.exit("No base directory. It is unsafe to continue.")

# Begin working
git_repo_cleanup()
git_repo_updates()
git_repo_initialize()
gitdm_analysis()
purge_old_gitdm_data()
correct_modified_gitdm_affiliations()
fix_funky_emails()
build_unknown_affiliation_cache()
# All done

update_status('Idle')
log_activity('Quiet','facade-worker.py completed')

cursor.close()
db.close()
