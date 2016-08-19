#!/usr/bin/python

# Copyright 2016 Brian Warner
#
# This file is part of Facade, and is made available under the terms of the GNU General Public License version 2.
# SPDX-License-Identifier:        GPL-2.0

# Git repo maintenance
#
# This script is responsible for cloning new repos and keeping existing
# repos up to date.  It is intended to be run a few times per day,
# so that all repos are kept up to date should something unexpected
# happen (like a network failure) right before you try to run gitdm.

import sys
import MySQLdb
from database import db_setup,open_cursor
(db,cursor) = db_setup()

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

# Determine if it's safe to start the script
query = "SELECT value FROM settings WHERE setting='utility_status' ORDER BY last_modified DESC LIMIT 1"
cursor.execute(query)
current_status = cursor.fetchone()["value"]

if (current_status != 'Idle'):
	query = "INSERT INTO utility_log (level,status) VALUES ('Error','Something is already running, aborting maintenance and analysis.')"
	cursor.execute(query)
	db.commit()
	sys.exit("Something is already running.  Halting until it finishes.")

# Figure out how much we're going to log
query = "SELECT value FROM settings WHERE setting='log_level' ORDER BY last_modified DESC LIMIT 1"
cursor.execute(query)
log_level = cursor.fetchone()["value"]

# Get the location of the directory where git repos are stored; abort if not set
query = "SELECT value FROM settings WHERE setting='repo_directory' ORDER BY last_modified DESC LIMIT 1"
cursor.execute(query)
repo_base_directory = cursor.fetchone()["value"]

if (len(repo_base_directory) == 0):
	sys.exit("There is no base directory. It is unsafe to continue.")

### BEGIN REPO MAINTENANCE ###

# Clean up any git repos that are pending deletion

query = "UPDATE settings SET value='Purging deleted repos' WHERE setting='utility_status'"
cursor.execute(query)
db.commit()

if (log_level == 'Info'):
	query = "INSERT INTO utility_log (level,status) VALUES ('Info',	'Repo maintenance: Processing deletions')"
	cursor.execute(query)
	db.commit()

query = "SELECT id,projects_id,path,name FROM repos WHERE status='Delete'"
cursor.execute(query)

delete_repos = cursor.fetchall()

for row in delete_repos:
	return_code = call("rm -rf "+repo_base_directory+str(row["projects_id"])+'/'+row["path"]+row["name"],shell=True)

	query = "DELETE FROM repos WHERE id="+str(row["id"])
	cursor.execute(query)
	db.commit()

	cleanup = str(row["projects_id"])+'/'+row["path"]+row["name"]

	# Attempt to cleanup any empty parent directories
	while (cleanup.find('/',0) > 0):
		cleanup = cleanup[:cleanup.rfind('/',0)]
		call("rmdir "+repo_base_directory+cleanup,shell=True)

# Now we need to update existing repos

query = "UPDATE settings SET value='Updating repos' WHERE setting='utility_status'"
cursor.execute(query)
db.commit()

if (log_level == 'Info'):
	query = "INSERT INTO utility_log (level,status) VALUES ('Info',	'Repo maintenance: Updating existing repos')"
	cursor.execute(query)
	db.commit()

query = "SELECT id,projects_id,git,name,path FROM repos WHERE status='Active'";
cursor.execute(query)

existing_repos = cursor.fetchall()

for row in existing_repos:
	return_code = call("git -C "+repo_base_directory+str(row["projects_id"])+'/'+row["path"]+row["name"]+" pull",shell=True)

	if (return_code == 0):
		query = "INSERT INTO repos_fetch_log (repos_id,status) values ("+str(row["id"])+",'Up-to-date')"
		cursor.execute(query)
		db.commit()
	else:
		query = "INSERT INTO repos_fetch_log (repos_id,status) values ("+str(row["id"])+",'Failed ("+str(return_code)+")')"
		cursor.execute(query)
		db.commit()

# Select any new git repos so we can initialize them (set up their locations on the filesystem and git clone)

query = "UPDATE settings SET value='Fetching new repos' WHERE setting='utility_status'"
cursor.execute(query)
db.commit()

if (log_level == 'Info'):
	query = "INSERT INTO utility_log (level,status) VALUES ('Info',	'Repo maintenance: Fetching new repos')"
	cursor.execute(query)
	db.commit()

query = "SELECT id,projects_id,git FROM repos WHERE status LIKE 'New%'";
cursor.execute(query)

new_repos = cursor.fetchall()

for row in new_repos:
	print row["git"]

	git = html.unescape(row["git"])

	# Strip protocol from remote URL, if it exists, so we can set a unique path on the filesystem
	# Storing this will allow us to find it for updates, and move the repos to a different place if needed
	if (git.find('://',0) > 0):
		repo_relative_path = git[git.find('://',0)+3:][:git[git.find('://',0)+3:].rfind('/',0)+1]
	else:
		repo_relative_path = git[:git.rfind('/',0)+1]

	# Prepend the base directory and project ID to get the full path to the directory where we'll clone the repo
	repo_path = repo_base_directory+str(row["projects_id"])+'/'+repo_relative_path

	# Get the name of repo
	repo_name = git[git.rfind('/',0)+1:]
	if (repo_name.find('.git',0) > -1):
		repo_name = repo_name[:repo_name.find('.git',0)]

	# Check if there will be a storage path collision
	query = "SELECT NULL FROM repos WHERE CONCAT(projects_id,'/',path,name) ='" + str(row["projects_id"]) + '/' + repo_relative_path + repo_name + "'"
	cursor.execute(query)
	db.commit()

	# If there is a collision, attempt to append a slug to repo_name to yield a unique path
	if (cursor.rowcount):

		slug = 1
		is_collision = True
		while (is_collision):

			if (os.path.isdir(repo_path + repo_name + '-' + str(slug))):
				slug += 1
			else:
				is_collision = False

		repo_name = repo_name + '-' + str(slug)

	# Create the prerequisite directories
	return_code = call('mkdir -p '+repo_path,shell=True)

	# Make sure it's ok to proceed
	if (return_code != 0):
		print("COULD NOT CREATE REPO DIRECTORY")
		query = "INSERT INTO repos_fetch_log (repos_id,status) VALUES (" + str(row["id"]) + ",'Failed (mkdir)')"
		print(query)
		cursor.execute(query)
		db.commit()
		sys.exit("Could not create git repo prerequisite directories. Do you have write access?")

	query = "INSERT INTO repos_fetch_log (repos_id,status) VALUES (" + str(row["id"]) + ",'New (cloning)')"
	cursor.execute(query)
	db.commit()

	query = "UPDATE repos SET status='New (Initializing)',path='" + repo_relative_path + "',name='" + repo_name + "' WHERE id=" + str(row["id"])
	cursor.execute(query)
	db.commit()


	return_code = call("git -C "+repo_path+" clone '"+git+"' " + repo_name, shell=True)

	if (return_code == 0):
		# If cloning succeeded, repo is ready for gitdm
		query = "UPDATE repos SET status='Active',path='" + repo_relative_path + "',name='" + repo_name + "' WHERE id=" + str(row["id"])
		cursor.execute(query)
		db.commit()

		query = "INSERT INTO repos_fetch_log (repos_id,status) VALUES (" + str(row["id"]) + ",'Up-to-date')"
		cursor.execute(query)
		db.commit()
	else:
		# If cloning failed, log it and set the status back to new
		query = "INSERT INTO repos_fetch_log (repos_id,status) VALUES (" + str(row["id"]) + ",'Failed (" + str(return_code) + ")')"
		cursor.execute(query)
		db.commit()

		query = "UPDATE repos SET status='New (failed)' WHERE id=" + str(row["id"])
		cursor.execute(query)
		db.commit()

### END REPO MAINTENANCE ###

### BEGIN GITDM ###

query = "UPDATE settings SET value='Running gitdm' WHERE setting='utility_status'"
cursor.execute(query)
db.commit()

if (log_level == 'Info'):
	query = "INSERT INTO utility_log (level,status) VALUES ('Info',	'Running gitdm')"
	cursor.execute(query)
	db.commit()

def gitdm(db,cursor,repo_loc,first,gitdm_loc):

	outfile_name = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))

	last = str((datetime.datetime.strptime(first,'%Y-%m-%d') + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))

	gitdmcall = 'git --git-dir '+repo_loc+' log --pretty=fuller -p -M --since='+first+' --before='+last+' --all | '+gitdm_loc+'/gitdm -b '+gitdm_loc+' -u -s -d -x '+outfile_name+'.tmp'

	return_code = call(gitdmcall,shell=True)

	return (outfile_name+'.tmp')

query = "SELECT value FROM settings WHERE setting='gitdm' ORDER BY last_modified DESC LIMIT 1"
cursor.execute(query)
gitdm_loc = cursor.fetchone()["value"]


# First we need to determine which dates need to be analyzed (if any)
query = "SELECT value FROM settings WHERE setting='start_date' ORDER BY last_modified DESC LIMIT 1"
cursor.execute(query)
start_date = cursor.fetchone()["value"]

query = "SELECT value FROM settings WHERE setting='end_date' ORDER BY last_modified DESC LIMIT 1"
cursor.execute(query)
end_date = cursor.fetchone()["value"]

if (end_date == 'yesterday'):
	end_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# Create a temporary table with all dates that should have data
# in order to determine if any need to be backfilled

query = "CALL make_cal_table('"+start_date+"','"+end_date+"')";
cursor.execute(query)
db.commit()

# Iterate over all repos and mark any dates that don't have a log
# entry as "Pending" so we know which data needs to be calculated.

query = "SELECT id FROM repos WHERE status='Active'";
cursor.execute(query)
repos = cursor.fetchall()

for repo in repos:

	query = """SELECT cal_table.date FROM cal_table LEFT JOIN
			(SELECT * FROM gitdm_master WHERE repos_id="""+str(repo["id"])+""") repo
			ON cal_table.date = repo.start_date
			WHERE repo.start_date IS NULL"""

	cursor.execute(query)
	missing_dates = cursor.fetchall()

	for date in missing_dates:

		query = """INSERT INTO gitdm_master (repos_id,status,start_date) VALUES
			("""+str(repo["id"])+""",
			'Pending',
			'"""+str(date["date"])+"""')"""

		cursor.execute(query)
		db.commit()

# Locate the repositories, get all of the "Pending" dates, and run gitdm

query = "SELECT * FROM gitdm_master WHERE status='Pending'"
cursor.execute(query)
repos = cursor.fetchall()

for repo in repos:
	# May want to update status to "working" in gitdm_master

	query = "SELECT projects_id,path,name FROM repos WHERE id="+str(repo["repos_id"])
	cursor.execute(query)
	repo_detail = cursor.fetchone()

	outfile = gitdm(db,cursor,repo_base_directory+str(repo_detail["projects_id"])+'/'+repo_detail["path"]+repo_detail["name"]+'/.git',repo["start_date"],gitdm_loc)

	# Now we need to shuffle this stuff into the gitdm_results table in the db.

	with open(outfile,"r") as file:
		reader = csv.reader(file,delimiter=',')

		# First we verify that the temp file matches what we expected

		header = next(reader)
		if (','.join(header) == 'Name,Email,Affliation,Date,Added,Removed,Changesets'):

			for row in reader:
				name = row[0].replace("'","\\'")
				email = row[1].replace("'","\\'")
				affiliation = row[2].replace("'","\\'")
				added = row[4]
				removed = row[5]
				changesets = row[6]

				query = """INSERT INTO gitdm_data (gitdm_master_id,name,email,affiliation,added,removed,changesets)
					VALUES ("""+str(repo["id"])+""",
					'"""+name+"""',
					'"""+email+"""',
					'"""+affiliation+"""',
					"""+str(added)+""",
					"""+str(removed)+""",
					"""+str(changesets)+""")"""

				cursor.execute(query)
				db.commit()

			query = """UPDATE gitdm_master SET status='Complete' WHERE id="""+str(repo["id"])
			cursor.execute(query)
			db.commit()

			call('rm '+outfile,shell=True)

### END GITDM ***

### BEGIN DUMPING OLD DATA IF START DATE CHANGED ###

query = "DELETE m,d FROM gitdm_master m LEFT JOIN gitdm_data d ON m.id=d.gitdm_master_id WHERE m.start_date < '" + start_date + "' OR m.start_date > '" + end_date + "'"
cursor.execute(query)
db.commit()

### END DUMPING OLD DATA IF START DATE CHANGED ###

### BEGIN AFFILIATION CORRECTIONS ###
for line in open(gitdm_loc + 'gitdm.config'):

	# Find all lines which are not commented and not empty
	if not (line.strip().startswith('#') or len(line.strip()) == 0):
		(configtype,configfile) = line.strip().split()

		# There are only certain configs that are relevant, we can ignore the rest
		if ((configtype == 'EmailAliases') or (configtype == 'EmailMap')):

			with open (gitdm_loc + configfile, 'rb') as file:
				hasher.update(file.read())

				# Determine if the last entry for this file matches the current md5
				query = "SELECT NULL FROM gitdm_configs WHERE configfile = '" + configfile + "' AND md5sum = '" + hasher.hexdigest() + "' ORDER BY last_modified DESC";

				cursor.execute(query)
				db.commit()

				if not (cursor.rowcount):
					# No match was found, so we need to process the new file for differences

					mismatches = []
					cached_configfile = 'cached-configs/' + configfile.replace('/','.') + '.cache'

					# First, let's find out if the file is even cached, so we can save some work.

					if os.path.isfile(cached_configfile):

						# File is cached, so walk through the config file to figure out what is different
						for line_config in open(gitdm_loc + configfile):

							if not (line_config.strip().startswith('#') or len(line_config.strip()) == 0):

								line_match = False

								for line_cache in open(cached_configfile):

									if (line_config == line_cache):
										line_match = True

								if not (line_match):
									# Store the mis-matches so we can process them.

									if (line_config.find('#')):
										# Strip any comments in the line
										line_config = line_config[:line_config.find('#')]

									mismatches.append(line_config)

					else:

						# File isn't cached, so all of it must be stored (without comments) for processing

						for line_config in open(gitdm_loc + configfile):
							if not (line_config.strip().startswith('#') or len(line_config.strip()) == 0):
								# Store all entries in the file so we can process them

								if (line_config.find('#')):
									# Strip any comments in the line
									line_config = line_config[:line_config.find('#')]

								mismatches.append(line_config)


					# Now it's time to process the mismatches
					for mismatch in mismatches:

						if (configtype == 'EmailAliases'):

							# Grab the canonical email from the end of the string
							canonical = mismatch.split()[-1]

							# Grab everything up to the canonical email, since entries could be space or tab delimited
							alias = mismatch[:mismatch.rfind(canonical)].strip()

							query = "UPDATE gitdm_data SET email='" + canonical.replace("'","\\'") + "' WHERE email='" + alias.replace("'","\\'") + "'"
							cursor.execute(query)
							db.commit()

						if (configtype == 'EmailMap'):

							# Grab the domain (or it could be a complete email) from the beginning of the string
							domain = mismatch.split()[0].replace("'","\\'")

							# Grab everything up to the affiliation, since entries could be space or tab delimited
							affiliation = mismatch[len(domain):].strip().replace("'","\\'")
							query = "UPDATE gitdm_data SET affiliation='" + affiliation + "' WHERE email LIKE '%" + domain + "%'" # Using double quotes because of apostrophes in affiliate names.
							cursor.execute(query)
							db.commit()

					# Cache the file
					return_code = call("cp " + gitdm_loc + configfile + "  " + cached_configfile, shell=True)

					if (return_code == 0):
						# Update database with new md5 hash so unchanged files can be ignored.
						query = "INSERT INTO gitdm_configs (configfile,configtype,md5sum,status) VALUES ('" + configfile + "','" + configtype + "','" + hasher.hexdigest() + "','Complete')"
						cursor.execute(query)
						db.commit()

					else:
						# Log as an error.
						query = "INSERT INTO gitdm_configs (configfile,configtype,md5sum,status) VALUES ('" + configfile + "','" + configtype + "','" + hasher.hexdigest() + "','Incomplete')"
						cursor.execute(query)
						db.commit()

### END AFFILITION CORRECTIONS ###

### BEGIN FIX FUNKY EMAILS ###

query = "SELECT id,email FROM gitdm_data WHERE email LIKE '%@%@%'"
cursor.execute(query)
funky_emails = cursor.fetchall()

for funky_email in funky_emails:

	# Trim everything to the right of the second @
	fixed_email = funky_email["email"][:funky_email["email"].rfind('@')]

	query = "UPDATE gitdm_data SET email='" + fixed_email + "' WHERE id='" + str(funky_email["id"]) + "'"
	cursor.execute(query)
	db.commit()

### END FIX FUNKY EMAILS ###

### BEGIN BUILDING UNKNOWN AFFILIATION CACHE ###

query = "DROP TABLE IF EXISTS unknown_cache"
cursor.execute(query)
unknowns = cursor.fetchall()

query = "CREATE TABLE unknown_cache (id INT AUTO_INCREMENT PRIMARY KEY, projects_id INT NOT NULL, email VARCHAR(64) NOT NULL, domain VARCHAR(64), added INT NOT NULL)"
cursor.execute(query)
db.commit()

query = "SELECT r.projects_id AS projects_id, d.email AS email, SUM(d.added) FROM repos r RIGHT JOIN gitdm_master m ON r.id = m.repos_id RIGHT JOIN gitdm_data d ON m.id = d.gitdm_master_id WHERE d.affiliation = '(Unknown)' GROUP BY r.projects_id,d.email"
cursor.execute(query)
unknowns = cursor.fetchall()

unknown_cache = {}

for unknown in unknowns:

	# Isolate the domain name, and add the lines of code associated with it
	query = "INSERT INTO unknown_cache (projects_id,email,domain,added) VALUES (" + str(unknown["projects_id"]) + ",'" + unknown["email"] + "','" + unknown["email"][unknown["email"].find('@') + 1:] + "'," + str(unknown["SUM(d.added)"]) + ")"
	cursor.execute(query)
	db.commit()

### END BUILDING UNKNOWN AFFILIATION CACHE ###

query = "UPDATE settings SET value='Idle' WHERE setting='utility_status'"
cursor.execute(query)
db.commit()

if (log_level == 'Info'):
	query = "INSERT INTO utility_log (level,status) VALUES ('Info',	'Script complete')"
	cursor.execute(query)
	db.commit()

cursor.close()
db.close()
