#!/usr/bin/python3

# Copyright 2016-2018 Brian Warner
#
# SPDX-License-Identifier:  Apache-2.0

# Facade CLI
#
# This script enables basic management of Facade without needing to install or
# use the web UI.  It includes a number of helper functions which can be
# imported by other programs.
#
# add_project(name,description,website,db,cursor)
# delete_project(project_id,db,cursor)
#
# add_repo(project_id,git_repo,db,cursor)
# delete_repo(git_repo,db,cursor)
#
# add_alias(alias,canonical,db,cursor)
# delete_alias(alias_id,db,cursor)
#
# add_affiliation(domain,affiliation,db,cursor,start_date = '')
# delete_affiliation(affiliation_id,db,cursor)
#
# get_setting(setting,db,cursor)
# set_setting(setting,value,db,cursor)
#
# add_tag(email,start_date,end_date,tag,db,cursor)
# delete_tag(tag_id,db,cursor)
#

import sys
import os
import configparser
import MySQLdb
import datetime
import time
import textwrap
import texttable
import re
import xlsxwriter
import csv

### Importable repo helper functions ###

def add_repo(project_id,git_repo,db,cursor):

	# Adds a new repo to a specific project
	#
	# project_id: Integer corresponding to an ID in the 'projects' table
	# git_repo: A string containing the full URI to a git repo
	# db: A database connection object
	# cursor: A database cursor

	add_repo = ("INSERT INTO repos (projects_id,git,status) VALUES "
		"(%s,%s,'New')")
	cursor.execute(add_repo,(project_id,git_repo))
	db.commit()

def delete_repo(git_repo,db,cursor):

	# Removes an uninitizliaed git repo, or marks it for deletion if it has
	# already been cloned
	#
	# git_repo: Integer corresponding to an ID in the 'repos' table
	# db: A database connection object
	# cursor: A database cursor

	get_status = "SELECT status FROM repos WHERE id = %s"
	cursor.execute(get_status,(git_repo, ))
	status = cursor.fetchone()

	if status == 'New':

		# Nothing was cloned, so delete it immediately

		delete_repo = "DELETE FROM repos WHERE id = %s"

	else:

		# Something may have been cloned, let facade-worker.py clean it

		delete_repo = ("UPDATE repos SET status = 'Delete' WHERE id = %s")

	cursor.execute(delete_repo,(git_repo, ))
	db.commit()

### Importable project helper functions ###

def add_project(name,description,website,db,cursor):

	# Adds a new project
	#
	# name: String containing project's name
	# description: String describing project (can be blank)
	# website: String with project's website (can be blank)
	# db: A database connection object
	# cursor: A database cursor

	add = ("INSERT INTO projects (name,description,website) "
		"VALUES (%s,%s,%s)")
	cursor.execute(add,(name,description,website))
	db.commit()

def delete_project(project_id,db,cursor):

	# Marks a project for deletion next time facade-worker.py runs. Performs
	# some cleanup in preparation.
	#
	# project_id: Integer corresponding to an ID in the 'projects' table
	# db: A database connection object
	# cursor: A database cursor

	# Begin cleaning up repos associated with the project

	get_repos = "SELECT id FROM repos WHERE projects_id = %s"
	cursor.execute(get_repos,(project_id, ))

	repos = list(cursor)

	for repo in repos:

		delete_repo(repo['id'],db,cursor)

	# Remove entries from the exclude table

	delete_exclude = "DELETE FROM exclude WHERE projects_id = %s"
	cursor.execute(delete_exclude,(project_id, ))
	db.commit()

	# facade-worker.py will clean up the rest

	set_project_delete = ("UPDATE projects SET name = '(Queued for removal)' "
		"WHERE id = %s")
	cursor.execute(set_project_delete,(project_id, ))
	db.commit()

### Importable alias and affiliation functions ###

def add_alias(alias,canonical,db,cursor):

	# Add an alias, or activate it if it's already known. Duplicates will be
	# ignored.
	#
	# alias: String containing the email to be aliased
	# canonical: String containing the canonical email
	# db: A database connection object
	# cursor: A database cursor

	add_alias = ("INSERT INTO aliases (alias,canonical) "
		"VALUES (%s,%s) "
		"ON DUPLICATE KEY UPDATE active = TRUE")

	cursor.execute(add_alias,(alias,canonical))
	db.commit()

def delete_alias(alias_id,db,cursor):

	# Set an alias to inactive (it will be treated as deleted).
	#
	# alias_id: Integer corresponding to an ID in the aliases table.
	# db: A database connection object
	# cursor: A database cursor

	set_alias_inactive = ("UPDATE aliases SET active = FALSE WHERE id=%s")

	cursor.execute(set_alias_inactive, (alias_id, ))
	db.commit()

def add_affiliation(domain,affiliation,db,cursor,start_date = ''):

	# Add an affiliation with an optional start_date.
	#
	# domain: String containing a domain or email address
	# affiliation: String containing the affiliation information
	# db: A database connection object
	# cursor: A database cursor
	# start_date: A string in YYYY-MM-DD indicating when affiliation began

	if start_date:
		add_an_affiliation = ("INSERT INTO affiliations "
			"(domain, affiliation, start_date) VALUES "
			"(%s,%s,%s) ON DUPLICATE KEY UPDATE active = TRUE")

		cursor.execute(add_an_affiliation, (domain, affiliation, start_date))

	else:
		add_an_affiliation = ("INSERT INTO affiliations "
			"(domain, affiliation) VALUES "
			"(%s,%s) ON DUPLICATE KEY UPDATE active = TRUE")

		cursor.execute(add_an_affiliation, (domain, affiliation))

	db.commit()

def delete_affiliation(affiliation_id,db,cursor):

	# Set an affiliation to inactive (it will be treated as deleted)
	#
	# affiliation_id: Integer corresponding to an ID in the affiliations table
	# db: A database connection object
	# cursor: A database cursor

	set_affiliation_inactive = ("UPDATE affiliations SET active = FALSE "
		"WHERE id=%s")

	cursor.execute(set_affiliation_inactive, (affiliation_id, ))
	db.commit()

### Importable tag functions ###

def add_tag(email,start_date,end_date,tag,db,cursor):

	# Add a tag
	#
	# email: Email address to be tagged
	# start_date: A string in YYYY-MM-DD indicating when the tagging should begin
	# end_date: A string in YYYY-MM-DD indicating when tagging should end. Empty if no end date.
	# tag: A string with the tag name
	# db: A database connection object
	# cursor: A database cursor

	if end_date:
		add_tag = ("INSERT IGNORE INTO special_tags "
			"(email,start_date,end_date,tag) VALUES (%s,%s,%s,%s)")

		cursor.execute(add_tag, (email,start_date,end_date,tag))
		db.commit()

	else:
		add_tag = ("INSERT IGNORE INTO special_tags "
			"(email,start_date,tag) VALUES (%s,%s,%s)")

		cursor.execute(add_tag, (email,start_date,tag))
		db.commit()

def delete_tag(tag_id,db,cursor):

	# Delete a tag
	#
	# tag_id: Integer corresponding to an ID in the special_tags table
	# db: A database connection object
	# cursor: A database cursor

	delete_tag = ("DELETE FROM special_tags WHERE id = %s")

	cursor.execute(delete_tag, (tag_id, ))
	db.commit()

### Importable general helper functions ###

def get_setting(setting,db,cursor):

	# Helper to quickly return a setting
	#
	# setting: String corresponding to a 'setting' in the settings table
	# db: A database connection object
	# cursor: A database cursor

	fetch = ("SELECT value FROM settings WHERE setting = %s "
		"ORDER BY last_modified DESC LIMIT 1")

	cursor.execute(fetch,(setting, ))

	return cursor.fetchone()['value']

def set_setting(setting,value,db,cursor):

	# Helper to quickly set a setting
	#
	# setting: String corresponding to a 'setting' in the settings table
	# value: String corresponding to the new value of the setting
	# db: A database connection object
	# cursor: A database cursor

	insert = "INSERT INTO settings (setting,value) VALUES (%s,%s)"

	cursor.execute(insert,(setting,value))
	db.commit()

#-----------------------------------------------------------------------------#
#            Below this point, everything is specific to facade.py            #
#-----------------------------------------------------------------------------#

### General helper functions ###

### Main functions ###

def _manage_projects():

	# Find out if there are any projects to display

	action = ''

	while action != 'r':

		get_projects = ("SELECT id,name,description,website FROM projects "
			"WHERE name != '(Queued for removal)'")
		cursor.execute(get_projects)

		existing_projects = list(cursor)

		print("\n--------\nPROJECTS\n--------\n")

		# If there are projects already defined, display them

		if (existing_projects):

			project_table = texttable.Texttable()
			project_table.set_cols_align(['l','l'])
			project_table.set_cols_width([35,57])

			for project in existing_projects:

				overview = project['name']

				if project['website']:
					overview = ("%s\n\n%s" %
					(project['name'],project['website']))

				else:
					overview = project['name']

				project_table.add_row(["%s" % overview, project['description']])

			print(project_table.draw() + "\n")

			project_table.reset()

		print(" (A)dd - Add a new project")

		if existing_projects:
			print(" (M)anage - Manage a project's repositories\n"
					" (E)dit - Edit a project's description\n"
					" (D)elete - Delete a project and its data")

		print(" (R)eturn - Return to the main menu\n")

		action = input("What would you like to do? ").strip().lower()

		if action == 'a':

			# Add a project

			name = ''
			description = ''
			website = ''
			confirm = ''

			print("\n.............\nADD A PROJECT\n.............\n")

			# Name is mandatory

			while name == '':
				name = input("Project name: ").strip()

			# Description and website are optional

			description = input("Description (optional): ").strip()
			website = input("Website (optional): ").strip()

			add_project(name,description,website,db,cursor)

		elif action == 'e' and existing_projects:

			# Edit a project

			project_id = ''
			project_numbers = ['c']
			done = ''

			print("\n................\nModify a project\n................\n")

			# Proceed only if there is a project to modify
			if not existing_projects:
				return

			project_table = texttable.Texttable()
			project_table.set_cols_align(['l','l'])
			project_table.set_cols_width([5,87])
			project_table.header(['ID','Name'])

			for project in existing_projects:

				project_table.add_row([project['id'], project['name']])
				project_numbers.append(str(project['id']))

			print(project_table.draw() + "\n")

			project_table.reset()

			# Collect the project ID to modify

			while project_id not in project_numbers:

				project_id = input("Project ID to modify (c to cancel): ").lower().strip()

				if project_id == 'c':

					print("\nCancelled\n")
					break

				if project_id not in project_numbers:

					print("Invalid selection\n")

			while not done:

				# Print out the currently stored values

				get_project = "SELECT name,description,website FROM projects WHERE id = %s"
				cursor.execute(get_project,(project_id, ))

				modify_project = cursor.fetchone()

				modify_table = texttable.Texttable()
				modify_table.set_cols_align(['l','l'])
				modify_table.set_cols_width([12,80])
				modify_table.add_rows([
					['','Project settings'],
					['Name',modify_project['name']],
					['Website',modify_project['website']],
					['Description',modify_project['description']]])

				print("\n" + modify_table.draw() + "\n")

				modify_table.reset()

				print(" (N)ame - Modify the name\n"
					" (W)ebsite - Modify the website\n"
					" (D)escription - Modify the description\n"
					" (R)eturn - Return to the projects menu\n")

				new_value = ''
				confirmed = ''

				edit_field = ''

				while edit_field != 'r':

					edit_field = input("\nWhat would you like to do? ").lower().strip()

					if edit_field == 'n':

						# Update the name

						while new_value == '':

							new_value = input('Set name to: (c to cancel) ').strip()

						if new_value != 'c':

							update_value = "UPDATE projects SET name = %s WHERE id = %s"
							cursor.execute(update_value,(new_value,project_id))

						else:

							print("Modification cancelled\n")

					elif edit_field == 'w':

						# Update the website (blank allowed)

						new_value = input('Set website: (blank for none, c to cancel) ').strip()

						if new_value != 'c':

							update_value = "UPDATE projects SET website = %s WHERE id = %s"
							cursor.execute(update_value,(new_value,project_id))

						else:

							print("Modification cancelled\n")

					elif edit_field == 'd':

						# Update the description (blank allowed)

						new_value = input("Set description: (blank for none, c to cancel) ").strip()

						if new_value != 'c':

							update_value = "UPDATE projects SET description = %s WHERE id = %s"
							cursor.execute(update_value,(new_value,project_id))

						else:

							print("Modification cancelled\n")

					else:

						print("Invalid selection\n")

		elif action == 'm' and existing_projects:

			print("\n........................\nMODIFY A PROJECT'S "
				"REPOS\n........................\n")

			# Proceed only if there are projects to edit

			if not existing_projects:
				return

			project_table = texttable.Texttable()
			project_table.set_cols_align(['l','l'])
			project_table.set_cols_width([5,87])
			project_table.header(['ID','Name'])

			project_numbers = ['c']

			for project in existing_projects:

				project_table.add_row([project['id'], project['name']])
				project_numbers.append(str(project['id']))

			print(project_table.draw() + "\n")

			project_table.reset()

			# Collect the project ID to modify

			project_id = ''

			while project_id not in project_numbers:

				project_id = input("Project ID to modify (c to cancel): ").lower().strip()

				if project_id == 'c':

					print("\nCancelled")
					return

				if project_id not in project_numbers:

					print("\nInvalid selection\n")

			edit_field = ''

			while edit_field != 'r':

				# Print out the current repositories

				_list_repo_status(project_id)

				print("\n (A)dd - Add a new repo\n"
					" (D)elete - Delete a repo\n"
					" (R)eturn - Return to the projects menu\n")

				# Figure out what the user wants to do

				git_repo = ''

				edit_field = input("What would you like to do? ").lower().strip()

				if edit_field == 'a':

					# Add a new repo

					while not git_repo:
						git_repo = input('Git url (c to cancel): ').strip()

					if git_repo != 'c':

						add_repo(project_id,git_repo,db,cursor)

					else:
						print("No repo added")

				elif edit_field == 'd':

					_list_repo_status(project_id,True)

					# Delete a repo

					while not git_repo:
						git_repo = input('ID to delete (c to cancel): ').strip()

					if git_repo != 'c':
						delete_repo(git_repo,db,cursor)

		elif action == 'd' and existing_projects:

			# Delete a project

			project_id = ''
			confirm = ''
			project_numbers = ['c']

			# Proceed only if there are projects to delete

			if not existing_projects:
				return

			print("\n................\nDELETE A PROJECT\n................\n")

			project_table = texttable.Texttable()
			project_table.set_cols_align(['l','l'])
			project_table.set_cols_width([5,87])
			project_table.header(['ID','Name'])

			for project in existing_projects:

				project_table.add_row([project['id'], project['name']])
				project_numbers.append(str(project['id']))

			print(project_table.draw() + "\n")

			project_table.reset()

			# Collect the project ID to delete

			while project_id not in project_numbers:

				project_id = input("Project ID to delete (c to cancel): ").lower().strip()

				if project_id == 'c':

					print("Exiting without doing anything.\n")
					return

				if project_id not in project_numbers:

					print("Invalid selection\n")

			# Confirm the delete, since this can be a big deal

			get_name = "SELECT name FROM projects WHERE id = %s"
			cursor.execute(get_name,(project_id, ))
			name = cursor.fetchone()

			while confirm not in ['y','n']:
				confirm = input("\nDo you really want to delete '%s', its repos, and "
						"all analysis data? (y/n) " % name['name']).lower().strip()

			if confirm == 'n':
				print("Exiting without doing anything.\n")
				return

			delete_project(project_id,db,cursor)

		else:
			print("Invalid selection\n")
			continue

def _list_repo_status(request_id=0,show_id=0):

	# List repo statuses. Used by both the Repo main menu item as well as repo
	# display for specific projects.

	request_clause = ''

	# Narrow down the query to a specific project

	if request_id:
		request_clause = "AND id = %s" % request_id

	get_projects = ("SELECT id,name FROM projects "
		"WHERE name != '(Queued for removal)' %s"
		% request_clause)

	cursor.execute(get_projects)
	projects = list(cursor)

	# Print out the repos for each project

	for project in projects:

		project_table = texttable.Texttable()

		alignment = ['l','c','c']
		width = [67,10,12]
		header = [project['name'],'Last pull','Analysis']

		if show_id:
			alignment.insert(0,'c')
			width = [5,62,10,12]
			header.insert(0,'ID')

		project_table.set_cols_align(alignment)
		project_table.set_cols_width(width)
		project_table.header(header)

		# Select project-specific repo data

		get_repos = ("SELECT id,git FROM repos WHERE projects_id=%s "
			"AND status != 'Delete'")
		cursor.execute(get_repos,(project['id'], ))

		repos = list(cursor)

		for repo in repos:

			repo_line = [repo['git']]

			# Normally when viewing a repo, it's unnecessary to show the repo's
			# ID.  However, if you're editing a repo you need to see it, so
			# show_id toggles whether or not the ID is displayed.  This is only
			# ever used in conjunction with request_id.

			if show_id:
				repo_line.insert(0,repo['id'])

			get_fetch_status = ("SELECT date FROM repos_fetch_log "
				"WHERE repos_id = %s "
				"AND status='Up-to-date' "
				"ORDER BY date DESC LIMIT 1")
			cursor.execute(get_fetch_status,(repo['id'], ))

			fetch_status = list(cursor)

			# If there's no fetch status, the repo must be new

			if fetch_status:
				repo_line.append(fetch_status.pop()['date'].strftime('%Y-%m-%d'))
			else:
				repo_line.append('New')

			get_analysis_status = ("SELECT status FROM analysis_log "
				"WHERE repos_id = %s ORDER BY date_attempted DESC LIMIT 1")
			cursor.execute(get_analysis_status,(repo['id'], ))

			analysis_status = list(cursor)

			# If there's no analysis status, the data must be unanalyzed

			if analysis_status:
				repo_line.append(analysis_status.pop()['status'])
			else:
				repo_line.append('New')

			project_table.add_row(repo_line)

		print("\n" + project_table.draw())

def _list_aliases(search_term = ''):

	# List aliases in a table, and provide ability to search for them

	start_row = 0
	more_data = True
	search_term_clause = ''

	if search_term:

		# This has some ridiculous escaping for mysql's wildcard
		# character to survive string replacement.

		search_term_clause = ("AND (canonical LIKE '%%%%%s%%%%' OR "
			"alias LIKE '%%%%%s%%%%')" % (search_term, search_term))

	while more_data:

		# Use string replacement to sub in the search term clause, eating
		# one set of %% in the clause.

		get_num_aliases = ("SELECT NULL FROM aliases WHERE active = TRUE %s"
			% search_term_clause)

		cursor.execute(get_num_aliases)
		num_aliases = cursor.rowcount

		if num_aliases == 0:
			print("\nNo aliases found")
			break

		aliases_table = texttable.Texttable()

		aliases_table.set_cols_align(['l','l','l'])
		aliases_table.set_cols_width([7,41,41])
		aliases_table.header(['ID','Canonical','Alias'])

		alias_numbers = []

		# Don't use string replacement to sub in the search term clause,
		# because we need to preserve the last %% in the clause. Maybe there's a
		# better way to do this?

		get_aliases = ("SELECT id,canonical,alias FROM aliases WHERE "
			"active = TRUE " + search_term_clause + " LIMIT %s,%s")

		cursor.execute(get_aliases, (start_row,page_size))

		result_size = cursor.rowcount

		if result_size < page_size:
			more_data = False

		aliases = list(cursor)

		for alias in aliases:

			aliases_table.add_row([alias['id'],
				alias['canonical'],
				alias['alias']])

			alias_numbers.append(str(alias['id']))

		print("\n" + aliases_table.draw() + "\n")

		print ("Aliases found: %s" % num_aliases)

		if num_aliases > 0:
			print("Showing results %s to %s.\n" %
					(start_row+1, start_row+result_size))

		aliases_table.reset()

		# Determine if we need pagination

		next_is_valid = False

		if num_aliases > start_row+result_size:
			print(" (N)ext - Show next page of results")
			next_is_valid = True

		previous_is_valid = False

		if start_row > 0:
			print(" (P)revious - Show previous page of results")
			previous_is_valid = True

		if result_size > 0:
			print(" (<ID>) - Delete alias with <ID>")

		print(" (R)eturn - Return to the previous menu\n")

		list_alias_action = ''

		while list_alias_action != 'r':

			list_alias_action = input("What would you like to do? ").strip().lower()

			if list_alias_action == 'n' and next_is_valid:
				start_row = start_row+page_size
				break

			if list_alias_action == 'p' and previous_is_valid:
				start_row = max(0,start_row-page_size)
				more_data = True
				break

			if list_alias_action in alias_numbers:

				get_delete = ("SELECT canonical,alias FROM aliases WHERE id=%s")

				cursor.execute(get_delete, (list_alias_action, ))

				delete = cursor.fetchone()

				print("\nYou are about to delete the following alias:\n\n"
					" Canonical:  %s\n"
					" Alias:      %s\n" %
					(delete['canonical'],delete['alias']))

				confirm_delete = ''

				while confirm_delete not in ['y','n']:
					confirm_delete = input("Are you sure? (y/n) ").strip().lower()

				if confirm_delete == 'y':
					delete_alias(list_alias_action,db,cursor)

				if result_size == 1 and start_row > 0:
					# If the result is the last one on the last page, fall
					# back to a previous page

					start_row = start_row-page_size
					more_data = True

				break

		if list_alias_action == 'r':
			break

def _list_affiliations(mapping, search_term = ''):

	# List affiliations by domain or by email, with optional search

	start_row = 0
	more_data = True
	mapping_clause = ''
	mapping_title = "Domain / email"
	search_term_clause = ''

	if mapping == 'domains':
		mapping_clause = "AND domain NOT LIKE '%%@%%' "
		mapping_title = "Domain"

	elif mapping == 'emails':
		mapping_clause = "AND domain LIKE '%%@%%' "
		mapping_title = "Email"

	if search_term:
		# This has some ridiculous escaping for mysql's wildcard
		# character to survive string replacement.

		search_term_clause = ("AND (domain LIKE '%%%%%s%%%%' OR "
			"affiliation LIKE '%%%%%s%%%%')" % (search_term, search_term))

	while more_data:

		# Use string replacement to sub in the search term clause, eating
		# one set of %% in the clause.

		get_num_affiliations = ("SELECT NULL FROM affiliations WHERE active = TRUE %s%s"
			% (mapping_clause, search_term_clause))

		cursor.execute(get_num_affiliations)
		num_affiliations = cursor.rowcount

		if num_affiliations == 0:
			print("\nNo affiliations found")
			break

		affiliations_table = texttable.Texttable()

		affiliations_table.set_cols_align(['l','l','l','l'])
		affiliations_table.set_cols_width([5,35,35,11])
		affiliations_table.header(['ID',mapping_title,'Affiliation','Starting on'])

		affiliation_numbers = []

		# Don't use string replacement to sub in the search term clause,
		# because we need to preserve the last %% in the clause.

		get_affiliations = ("SELECT id,domain,affiliation,start_date FROM affiliations WHERE "
			"active = TRUE " + search_term_clause + mapping_clause + " LIMIT %s,%s")

		cursor.execute(get_affiliations, (start_row,page_size))

		result_size = cursor.rowcount

		# Only show more results if there are more results

		if result_size < page_size:
			more_data = False

		affiliations = list(cursor)

		for affiliation in affiliations:

			affiliations_table.add_row([affiliation['id'],
				affiliation['domain'],
				affiliation['affiliation'],
				affiliation['start_date']])

			affiliation_numbers.append(str(affiliation['id']))

		print("\n" + affiliations_table.draw() + "\n")

		affiliations_table.reset()

		if mapping == 'domains':
			print("Showing domains only\n")

		elif mapping == 'emails':
			print("Showing emails only\n")

		else:
			print("Showing both domains and emails\n")

		print ("Affiliations found: %s" % num_affiliations)

		if num_affiliations > 0:
			print("Showing results %s to %s.\n" %
					(start_row+1, start_row+result_size))

		affiliations_table.reset()

		next_is_valid = False

		# Determine if we need pagination

		if num_affiliations > start_row+result_size:
			print(" (N)ext - Show next page of results")
			next_is_valid = True

		previous_is_valid = False

		if start_row > 0:
			print(" (P)revious - Show previous page of results")
			previous_is_valid = True

		if result_size > 0:
			print(" (<ID>) - Delete affiliation with <ID>")

		print(" (R)eturn - Return to the previous menu\n")

		list_affiliation_action = ''

		while list_affiliation_action != 'r':

			list_affiliation_action = input("What would you like to do? ").strip().lower()

			if list_affiliation_action == 'n' and next_is_valid:

				# Show the next page of data

				start_row = start_row+page_size
				break

			elif list_affiliation_action == 'p' and previous_is_valid:

				# Show the previous page, reset more_data

				start_row = max(0,start_row-page_size)
				more_data = True
				break

			elif list_affiliation_action in affiliation_numbers:

				# Get useful info for confirming the delete.

				get_delete = ("SELECT domain,affiliation,start_date FROM affiliations WHERE id=%s")

				cursor.execute(get_delete, (list_affiliation_action, ))

				delete = cursor.fetchone()

				print("\nYou are about to delete the following affiliation:\n\n"
					" %s: %s\n"
					" Affiliation: %s" %
					(mapping_title, delete['domain'], delete['affiliation']))

				if delete['start_date'] != '1970-01-01':
					print(" Start date: %s" % delete['start_date'])

				confirm_delete = ''

				while confirm_delete not in ['y','n']:
					confirm_delete = input("\nAre you sure? (y/n) ").strip().lower()

				if confirm_delete == 'y':
					delete_affiliation(list_affiliation_action,db,cursor)

				if result_size == 1 and start_row > 0:

					# If the result is the last one on the last page, fall
					# back to a previous page

					start_row = start_row-page_size
					more_data = True

				break

		if list_affiliation_action == 'r':
			break

def _list_unknowns(project = ''):

	# List emails with an unknown affiliation, optionally by project

	start_row = 0
	more_data = True
	report_attribution = 'author' # author or committer
	affiliation_type = 'domain' # email or domain
	project_clause = ''

	# If a project was set, limit the results

	if project:
		project_clause = ' AND projects_id = %s ' % project

	while more_data:

		# Figure out how many results we're dealing with

		get_num_unknowns = ("SELECT DISTINCT(" + affiliation_type + ") "
			"FROM unknown_cache WHERE type = %s" + project_clause)

		cursor.execute(get_num_unknowns, (report_attribution, ))
		num_unknowns = cursor.rowcount

		if num_unknowns == 0:
			print("\nNo unknown affiliations found")
			break

		unknown_table = texttable.Texttable()

		unknown_table.set_cols_align(['l','l','l'])
		unknown_table.set_cols_width([5,73,11])
		unknown_table.header(['ID',affiliation_type.capitalize() + 's by ' +
			report_attribution,'Lines added'])

		unknown_emails = []

		get_unknowns = ("SELECT " + affiliation_type + " AS affiliation_type, "
			"SUM(added) as added "
			"FROM unknown_cache WHERE type = %s " + project_clause +
			"GROUP BY affiliation_type ORDER BY added DESC "
			"LIMIT %s,%s")

		cursor.execute(get_unknowns, (report_attribution, start_row, page_size))

		unknowns = list(cursor)
		result_size = cursor.rowcount

		# The unknown_cache table doesn't have IDs, so we have to track them in
		# two arrays.  There is probably a better way to do this, but this can
		# be done later.

		unknown_id = 1
		unknown_ids = []
		unknown_cache = []

		for unknown in unknowns:

			unknown_table.add_row([unknown_id,unknown['affiliation_type'],unknown['added']])
			unknown_ids.append(str(unknown_id))
			unknown_cache.append(unknown['affiliation_type'])
			unknown_id += 1

		print("\n" + unknown_table.draw() + "\n")

		unknown_table.reset()

		# Enable pagination

		next_is_valid = False

		if num_unknowns > start_row+result_size:
			print(" (N)ext - Show next page of results")
			next_is_valid = True

		previous_is_valid = False

		if start_row > 0:
			print(" (P)revious - Show previous page of results")
			previous_is_valid = True

		# Enable user to toggle email/domain and author/committer

		if affiliation_type == 'email':
			print(" (D)omains - Show domains instead of email")
		else:
			print(" (E)mails - Show emails instead of domains")

		if report_attribution == 'author':
			print(" (C)ommitters - Show committer stats instead of author stats")
		else:
			print(" (A)uthors - Show author stats instead of committer stats")

		if result_size > 0:
			print(" (<ID>) - Add an alias or affiliation for <ID>")

		print(" (R)eturn - Return to the previous menu\n")

		list_unknowns_action = ''

		while list_unknowns_action != 'r':

			list_unknowns_action = input("What would you like to do? ").strip().lower()

			if list_unknowns_action == 'n' and next_is_valid:
				start_row = start_row+page_size
				break

			elif list_unknowns_action == 'p' and previous_is_valid:
				start_row = max(0,start_row-page_size)
				more_data = True
				break

			elif list_unknowns_action == 'd':
				affiliation_type = 'domain'
				break

			elif list_unknowns_action == 'e':
				affiliation_type = 'email'
				break

			elif list_unknowns_action == 'c':
				report_attribution = 'committer'
				break

			elif list_unknowns_action == 'a':
				report_attribution = 'author'
				break

			elif list_unknowns_action in unknown_ids:

				# The user chose a valid Unknown ID

				edit_unknown = ''

				while edit_unknown != 'c':

					print(" A(l)ias - Associate %s with a canonical email\n"
						" A(f)filiation - Add an affiliation for %s\n"
						" (C)ancel\n" % (unknown_cache[int(list_unknowns_action)-1],
							unknown_cache[int(list_unknowns_action)-1]))

					edit_unknown = input("What would you like to do? ").strip().lower()

					if edit_unknown == 'l':

						canonical = ''

						while canonical == '':

							canonical = input("Canonical email for %s: " %
								unknown_cache[int(list_unknowns_action)-1])

						print("\nYou are adding the following alias\n"
							" '%s' will be treated as identical to '%s'\n" %
							(unknown_cache[int(list_unknowns_action)-1], canonical))


						confirm_add_alias = ''

						while confirm_add_alias not in ['y','n']:
							confirm_add_alias = input("Proceed? (y/n) ").strip().lower()

						if confirm_add_alias == 'y':
							add_alias(unknown_cache[int(list_unknowns_action)-1],canonical,db,cursor)

						break

					elif edit_unknown == 'f':

						affiliation = ''

						while affiliation == '':
							affiliation = input(" Affiliation: ").strip().lower()

						start_date = input(" Start date (optional): ").strip().lower()

						get_matches = ("SELECT domain,affiliation,start_date FROM "
							"affiliations WHERE "
								"domain LIKE %s OR "
								"affiliation LIKE %s "
								"ORDER BY affiliation ASC")

						print(get_matches)
						cursor.execute(get_matches,
								('%'+unknown_cache[int(list_unknowns_action)-1]+'%',
									'%'+affiliation+'%'))

						matches = list(cursor)

						if cursor.rowcount > 0:

							match_table = texttable.Texttable()

							match_table.set_cols_align(['l','l','l'])
							match_table.set_cols_width([38,38,11])
							match_table.header(['Domain / Email','Affiliation','Starting on'])

							print("\nThe following similar affiliations were found:\n")

							for match in matches:
								match_table.add_row([match['domain'],match['affiliation'],match['start_date']])

							print(match_table.draw() + "\n")

							match_table.reset()

							confirm_add_affiliation = ''

							while confirm_add_affiliation not in ['y','n']:
								confirm_add_affiliation = input("Continue to add "
								"this affiliation? (y/n) ").strip().lower()

						else:
							confirm_add_affiliation = 'y'

						if confirm_add_affiliation == 'y':
							if start_date:
								add_affiliation(unknown_cache[int(list_unknowns_action)-1],affiliation,db,cursor,start_date)

							else:
								add_affiliation(unknown_cache[int(list_unknowns_action)-1],affiliation,db,cursor)

							break

						break
				break

		if list_unknowns_action == 'r':
			break

def _aliases_and_affiliations():

	# Add, modify, and remove aliases and affiliations.

	action = ''

	while action != 'r':

		print("\n------------------------\nALIASES AND "
			"AFFILIATIONS\n------------------------\n\n"
			" A(l)iases - View and edit aliases\n"
			" A(f)filiations - View and edit affiliations\n"
			" (U)nknown - List emails and domains with unknown affiliations\n"
			" (R)eturn - Return to the main menu\n")

		action = input("What would you like to do? ").strip().lower()


		if action == 'l':

			alias_action = ''

			while alias_action != 'r':

				print("\n.......\nALIASES\n.......\n\n"
					" (L)ist - List or remove aliases\n"
					" (S)earch - Search for an alias\n"
					" (A)dd - Add an alias\n"
					" (R)eturn - Return to the previous menu\n")


				alias_action = input("What would you like to do? ").strip().lower()

				if alias_action == 'l':

					_list_aliases()

				elif alias_action == 's':

					term = input("\nSearch term: ").strip()

					if term:
						_list_aliases(term)

				elif alias_action == 'a':

					# Add an alias

					canonical = ''

					while canonical == '':
						canonical = input("\n Canonical email: ").strip().lower()

					alias = ''

					while alias == '':
						alias = input(" Alias email: ").strip().lower()

					print("\nYou are adding the following alias\n"
						" '%s' will be treated as identical to '%s'\n" % (alias,canonical))

					confirm_add_alias = ''

					while confirm_add_alias not in ['y','n']:
						confirm_add_alias = input("Proceed? (y/n) ").strip().lower()

					if confirm_add_alias == 'y':
						add_alias(alias,canonical,db,cursor)

		elif action == 'f':

			affiliation_action = ''

			while affiliation_action != 'r':

				print("\n............\nAFFILIATIONS\n............\n\n"
					" (L)ist - List or remove affiliations\n"
					" (S)earch - Search for an affiliation\n"
					" (A)dd - Add an affiliation\n"
					" (R)eturn - Return to the previous menu\n")

				affiliation_action = input("What would you like to do? ").strip().lower()

				if affiliation_action == 'l':

					print("\n (D)omains - Show only domain-to-affiliation mappings\n"
						" (E)mails - Show only email-to-affiliation mappings\n"
						" (B)oth - Show both domain- and email-to-affiliation mappings\n")

					display_action = input("Type of affiliations: ").strip().lower()

					if display_action == 'd':

						_list_affiliations('domains')

					elif display_action == 'e':

						_list_affiliations('emails')

					elif display_action == 'b':

						_list_affiliations('both')

				elif affiliation_action == 's':

					print("\n (D)omains - Search only domain-to-affiliation mappings\n"
						" (E)mails - Search only email-to-affiliation mappings\n"
						" (B)oth - Search both domain- and email-to-affiliation mappings\n")

					display_action = input("Type of affiliations: ").strip().lower()

					if display_action in ['d','e','b']:
						term = input("\nSearch term: ").strip()

					if display_action == 'd':

						_list_affiliations('domains', term)

					elif display_action == 'e':

						_list_affiliations('emails', term)

					elif display_action == 'b':

						_list_affiliations('both', term)

				elif affiliation_action == 'a':

					# Add an affiliation

					domain = ''

					while domain == '':
						domain = input(" Domain / email: ").strip().lower()

					affiliation = ''

					while affiliation == '':
						affiliation = input(" Affiliation: ").strip().lower()

					start_date = input(" Start date (optional): ").strip().lower()

					get_matches = ("SELECT domain,affiliation,start_date FROM "
						"affiliations WHERE "
							"domain LIKE %s OR "
							"affiliation LIKE %s "
							"ORDER BY affiliation ASC")

					cursor.execute(get_matches, ('%'+domain+'%', '%'+affiliation+'%'))
					matches = list(cursor)

					if cursor.rowcount > 0:

						match_table = texttable.Texttable()

						match_table.set_cols_align(['l','l','l'])
						match_table.set_cols_width([38,38,11])
						match_table.header(['Domain / Email','Affiliation','Starting on'])

						print("\nThe following similar affiliations were found:\n")

						for match in matches:
							match_table.add_row([match['domain'],match['affiliation'],match['start_date']])

						print(match_table.draw() + "\n")
						match_table.reset()

						confirm_add_affiliation = ''

						while confirm_add_affiliation not in ['y','n']:
							confirm_add_affiliation = input("Continue to add this affiliation? (y/n) ").strip().lower()

					else:
						confirm_add_affiliation = 'y'

					if confirm_add_affiliation == 'y':
						if start_date:
							add_affiliation(domain,affiliation,db,cursor,start_date)

						else:
							add_affiliation(domain,affiliation,db,cursor)

		elif action == 'u':

			# List and attempt to classify unknown contributors

			unknown_action = ''

			while unknown_action != 'r':

				print("\n--------------------\nUNKNOWN "
				"CONTRIBUTORS\n--------------------\n\n"
				" (A)ll - List all unknown contributors from all projects")

				get_projects = "SELECT id,name FROM projects"

				cursor.execute(get_projects)
				projects = list(cursor)

				project_numbers = []

				for project in projects:

					print(" (%s) - List all unknown contributors from project: %s"
						% (project['id'],project['name']))

					project_numbers.append(str(project['id']))

				print(" (R)eturn - Return to the previous menu\n")

				unknown_action = input("What would you like to do? ").strip().lower()

				if unknown_action == 'a':
					_list_unknowns()

				elif unknown_action in project_numbers:
					_list_unknowns(unknown_action)

def _list_tagged_emails():

	# List and edit tagged emails

	start_row = 0
	more_data = True
	show_email = ''
	show_tag = ''

	while more_data:

		if show_email:

			# Show all tags associated with an email

			get_num_emails = ("SELECT NULL FROM special_tags WHERE email = %s")

			cursor.execute(get_num_emails, (show_email, ))
			num_emails = cursor.rowcount

		elif show_tag:

			# Show all emails associated with a tag

			get_num_emails = ("SELECT NULL FROM special_tags WHERE tag = %s")

			cursor.execute(get_num_emails, (show_tag, ))
			num_emails = cursor.rowcount

		else:

			# Show all emails and tags

			get_num_emails = ("SELECT NULL FROM special_tags")

			cursor.execute(get_num_emails)
			num_emails = cursor.rowcount

		if num_emails == 0:
			print("\nNo tags found")
			break

		tags_table = texttable.Texttable()

		tags_table.set_cols_align(['l','l','l','l','l'])
		tags_table.set_cols_width([5,21,35,11,11])
		tags_table.header(['ID','Tag','Email','Starting on','Ending on'])

		tag_numbers = []

		if show_email:

			# Show all tags associated with an email

			get_emails = ("SELECT id,email,start_date,end_date,tag FROM "
					"special_tags WHERE email = %s "
					"ORDER BY tag, email LIMIT %s,%s")

			cursor.execute(get_emails, (show_email,start_row,page_size))

		elif show_tag:

			# Show all emails associated with a tag

			get_emails = ("SELECT id,email,start_date,end_date,tag FROM "
					"special_tags WHERE tag = %s "
					"ORDER BY tag, email LIMIT %s,%s")

			cursor.execute(get_emails, (show_tag,start_row,page_size))

		else:

			# Show all emails and tags

			get_emails = ("SELECT id,email,start_date,end_date,tag FROM "
					"special_tags ORDER BY tag, email LIMIT %s,%s")

			cursor.execute(get_emails, (start_row,page_size))

		result_size = cursor.rowcount

		if result_size < page_size:
			more_data = False

		emails = list(cursor)

		for email in emails:

			tags_table.add_row([email['id'],
				email['tag'],
				email['email'],
				email['start_date'],
				email['end_date']])

			tag_numbers.append(str(email['id']))

		print("\n" + tags_table.draw() + "\n")

		tags_table.reset()

		print ("Tagged emails found: %s" % num_emails)

		if num_emails > 0:
			print("Showing results %s to %s.\n" %
					(start_row+1, start_row+result_size))

		# Enable pagination

		next_is_valid = False

		if num_emails > start_row+result_size:
			print(" (N)ext - Show next page of results")
			next_is_valid = True

		previous_is_valid = False

		if start_row > 0:
			print(" (P)revious - Show previous page of results")
			previous_is_valid = True

		if result_size > 0:

			if show_email or show_tag:
				print(" (C)lear - Clear selection")

			else:
				print(" (E)mail - Limit results to a single email\n"
					" (T)ag - Limit results to a single tag")

			print(" (<ID>) - Delete tagged emails with <ID>")

		print(" (R)eturn - Return to the previous menu\n")

		list_tags_action = ''

		while list_tags_action != 'r':

			list_tags_action = input("What would you like to do? ").strip().lower()

			if list_tags_action == 'n' and next_is_valid:
				start_row = start_row+page_size
				break

			elif list_tags_action == 'p' and previous_is_valid:
				start_row = max(0,start_row-page_size)
				more_data = True
				break

			elif list_tags_action == 'e':

				show_email = input('Which email? (c to cancel) ').strip().lower()

				if show_email == 'c':
					show_email = ''
				break

			elif list_tags_action == 't':

				# Show tags only, so they can be edited

				get_tags = ("SELECT DISTINCT(tag) FROM special_tags")

				cursor.execute(get_tags)
				tag_list = list(cursor)

				tag_select_table = texttable.Texttable()

				tag_select_table.set_cols_align(['l'])
				tag_select_table.set_cols_width([95])
				tag_select_table.header(['Tag'])

				tag_names = []

				for tag in tag_list:
					tag_select_table.add_row([tag['tag']])
					tag_names.append(str(tag['tag']).strip())

				print("\n" + tag_select_table.draw() + "\n")

				tag_select_table.reset()

				show_tag = input('Which tag? (c to cancel) ').strip()

				if show_tag not in tag_names or show_tag == 'c':
					show_tag = ''

				break

			elif list_tags_action == 'c':

				# Clear any filters

				show_email = show_tag = ''

				break

			elif list_tags_action in tag_numbers:

				# Delete tagged emails

				get_delete = ("SELECT email,start_date,end_date,tag FROM special_tags "
					"WHERE id = %s")

				cursor.execute(get_delete, (list_tags_action, ))

				delete = cursor.fetchone()

				print("\nYou are about to delete the following tagged email:\n\n"
					" Email: %s\n"
					" Start date: %s\n"
					" End date: %s\n"
					" Tag: %s\n" %
					(delete['email'], delete['start_date'], delete['end_date'],
						delete['tag']))

				confirm_delete = ''

				while confirm_delete not in ['y','n']:
					confirm_delete = input("\nAre you sure? (y/n) ").strip().lower()

				if confirm_delete == 'y':
					delete_tag(list_tags_action,db,cursor)

				if result_size == 1 and start_row > 0:

					# If the result is the last one on the last page, fall
					# back to a previous page

					start_row = start_row-page_size
					more_data = True

				break

		if list_tags_action == 'r':
			break

def _tags():

	# Create and manage tags

	tags_action = ''

	while tags_action != 'r':

		print("\n----\nTAGS\n----\n\n"
			" (E)mails - List and modify tagged emails\n"
			" (T)ags - Rename tags\n"
			" (A)dd - Add a new tagged email\n"
			" (R)eturn - Return to the previous menu\n")

		tags_action = input("What would you like to do? ").strip().lower()

		if tags_action == 'e':

			_list_tagged_emails()

		elif tags_action == 't':

			print("\n...........\nRENAME TAGS\n...........\n")

			get_tags = ("SELECT DISTINCT(tag) AS tag, count(email) AS email FROM special_tags "
				"GROUP BY tag ORDER BY tag")

			cursor.execute(get_tags)
			tags = list(cursor)

			tag_id = 1
			tag_ids = []
			tag_cache = []

			tags_table = texttable.Texttable()

			tags_table.set_cols_align(['l','l','l'])
			tags_table.set_cols_width([5,41,43])
			tags_table.header(['ID','Tag','Number of Emails'])

			for tag in tags:

				tags_table.add_row([tag_id,tag['tag'],tag['email']])
				tag_ids.append(str(tag_id))
				tag_cache.append(tag['tag'])
				tag_id += 1

			print(tags_table.draw() + "\n\n"
				" (<ID>) - Rename tag with <ID>\n"
				" (R)eturn - Return to the previous menu\n")

			tags_table.reset()

			rename_tag_action = input("What would you like to do? ").strip().lower()

			if rename_tag_action in tag_ids:

				print("\nYou are renaming this tag: %s\n"
					"If it matches an existing tag, they will be merged.\n"
					% tag_cache[int(rename_tag_action)-1])

				new_tag = ''

				while new_tag == '':
					new_tag = input("New tag name: (c to cancel) ").strip()

				update_tag = ("UPDATE IGNORE special_tags SET tag = %s "
					"WHERE tag = %s")

				cursor.execute(update_tag,
					(new_tag, tag_cache[int(rename_tag_action)-1]))
				db.commit()

				print("Renaming \"%s\" -> \"%s\""
					% (tag_cache[int(rename_tag_action)-1], new_tag))

		elif tags_action == 'a':

			print("\n..................\nADD A TAGGED "
			"EMAIL\n..................\n\n"
			"Tags are created automatically\n")

			email = ''

			while email == '':
				email = input(" Email: ").strip().lower()

			tag = ''

			while tag == '':
				tag = input(" Tag: ").strip()

			start_date = ''

			while start_date == '':
				start_date = input(" Start tagging on this date: (YYYY-MM-DD) ").strip()

			if not (len(start_date) == 10 and
				re.match('([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))',start_date)):

				print("\nInvalid date\n")
				continue

			end_date = input(" Stop tagging on this date (optional): (YYYY-MM-DD) ").strip()

			if not (len(end_date) == 0 or (len(end_date) == 10 and
				re.match('([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))',end_date))):

				print("\nInvalid date\n")
				continue

			add_tag(email,start_date,end_date,tag,db,cursor)

def _export():

	# Export the raw analysis data to an Excel file.

	outfile = ''
	filters = []

	print("Export the raw analysis data as an Excel file.\n")

	# First we need a filename

	while outfile == '':
		outfile = os.path.expanduser(input('Filename or (c)ancel: ')).strip()

	if outfile == 'c':
		return

	if outfile.endswith('/') or len(outfile) == 0:
		print("\nINVALID: No filename given.\n")
		return

	if not outfile.endswith('.xlsx'):
		outfile += '.xlsx'

	# Next check if we should limit the results by date. This is useful when the
	# output would overrun the maximum length of an Excel file.

	start_date = input("Include contributions after: (YYYY-MM-DD or blank for all): ").strip()
	start_clause = ''

	if (len(start_date) == 10 and
		re.match('([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))',start_date)):

		report_date = get_setting('report_date',db,cursor)
		start_clause = (" AND %s_date > '%s' " %
			(get_setting('report_date',db,cursor), start_date))

		filters.append('Start date: %s' % start_date)

	# Next see if we need to limit to a list of affiliations

	affiliations_list = input("Include affiliations: (separated by ';' or blank for all) ").strip()
	affiliations_clause = ''

	if affiliations_list:
		affiliations = affiliations_list.split(';')
		report_attribution = get_setting('report_attribution',db,cursor)

		for affiliation in affiliations:

			if affiliation.strip():

				if not affiliations_clause:

					affiliations_clause = (" AND (%s_affiliation = '%s'"
						% (report_attribution, affiliation.strip()))

					filters.append('Affiliations: %s' % affiliation.strip())

				else:
					affiliations_clause += (" OR %s_affiliation = '%s'"
						% (report_attribution, affiliation.strip()))

					filters[-1] += ', %s' % affiliation.strip()

	if affiliations_clause:
		affiliations_clause += (') ')

	# Determine if export should be limited to certain projects

	project_action = ''
	project_clause = ''

	while project_action not in ['y','n']:

		project_action = input("Limit to certain projects: (y/n) ").strip().lower()

	if project_action == 'y':

		get_projects = ("SELECT id,name FROM projects "
			"WHERE name != '(Queued for removal)'")

		cursor.execute(get_projects)
		projects = list(cursor)

		if cursor.rowcount > 0:

			project_ids = []

			project_table = texttable.Texttable()

			project_table.set_cols_align(['l','l'])
			project_table.set_cols_width([5,85])
			project_table.header(['ID','Project'])

			for project in projects:
				project_table.add_row([project['id'],project['name']])
				project_ids.append(str(project['id']))

			print("\n" + project_table.draw() + "\n")
			project_table.reset()

		selected_ids = input("Include IDs: (separated by ',' or blank for all) ").strip()

		if selected_ids:

			for selected_id in selected_ids.split(','):

				if selected_id.strip() in project_ids:

					if not project_clause:
						project_clause = " AND (p.id = %s" % selected_id.strip()

						get_name = "SELECT name FROM projects WHERE id = %s"
						cursor.execute(get_name, (selected_id.strip(), ))

						filters.append('Projects: %s' % cursor.fetchone()['name'])

					else:
						project_clause += " OR p.id = %s" % selected_id.strip()

						get_name = "SELECT name FROM projects WHERE id = %s"
						cursor.execute(get_name, (selected_id.strip(), ))

						filters[-1] += ', %s' % cursor.fetchone()['name']

		if project_clause:
			project_clause += ')'

	workbook = xlsxwriter.Workbook(outfile)
	bold = workbook.add_format({'bold': True})

	# Add some identifying information

	worksheet = workbook.add_worksheet()

	worksheet.write(0,20,'Report generated on %s by Facade' %
		datetime.date.today().strftime('%Y-%m-%d'),bold)
	worksheet.write(1,20,'https://github.com/brianwarner/facade')

	if filters:
		filter_detail = '; '.join(filters)

	else:
		filter_detail = 'All projects, all dates'

	worksheet.write(2,20, filter_detail)

	# Set the headers

	headers = (['Project Name',
		'Repo Path',
		'Repo Name',
		'Author Date',
		'Author Name',
		'Author Raw Email',
		'Author Email',
		'Author Affiliation',
		'Committer Date',
		'Committer Name',
		'Committer Raw Email',
		'Committer Email',
		'Committer Affiliation',
		'LoC Added',
		'LoC Removed',
		'Whitespace Changes',
		'Commit',
		'Filename'])

	for col in range (0,18):

		worksheet.write(0,col,headers[col],bold)

	# Begin in the row below the headers

	row = 1

	get_projects = "SELECT id FROM projects"
	cursor.execute(get_projects)

	projects = list(cursor)

	for project in projects:

		# Write each project sequentially, and limit query size

		min_record = 0
		num_records = 50000
		more_data = True

		while (more_data):

			get_results = ("SELECT p.name AS 'Project Name', "
				"r.path AS 'Repo Path', "
				"r.name AS 'Repo Name', "
				"a.author_date AS 'Author Date', "
				"a.author_name AS 'Author Name', "
				"a.author_raw_email AS 'Author Raw Email', "
				"a.author_email AS 'Author Email', "
				"a.author_affiliation AS 'Author Affiliation', "
				"a.committer_date AS 'Committer Date', "
				"a.committer_name AS 'Committer Name', "
				"a.committer_raw_email AS 'Committer Raw Email', "
				"a.committer_email AS 'Committer Email', "
				"a.committer_affiliation AS 'Committer Affiliation', "
				"a.added AS 'LoC Added', "
				"a.removed AS 'LoC Removed', "
				"a.whitespace AS 'Whitespace Changes', "
				"a.commit AS 'Commit', "
				"a.filename AS 'Filename' "
				"FROM projects p "
				"RIGHT JOIN repos r ON p.id = r.projects_id "
				"RIGHT JOIN analysis_data a ON r.id = a.repos_id "
				"LEFT JOIN exclude e ON (a.author_email = e.email "
					"AND (r.projects_id = e.projects_id "
						"OR e.projects_id = 0)) "
					"OR (a.author_email LIKE CONCAT('%%',e.domain) "
						"AND (r.projects_id = e.projects_id "
							"OR e.projects_id = 0)) "
				"WHERE p.name != '(Queued for removal)' AND "
				"r.projects_id = %s "
				"AND e.email IS NULL "
				"AND e.domain IS NULL "
				+ start_clause + affiliations_clause + project_clause +
				"ORDER BY a.committer_date ASC "
				"LIMIT %s,%s")

			cursor.execute(get_results, (project['id'],
				min_record, num_records))

			results = list(cursor)

			for result in results:

				# This looks clunky, but it's a way to guarantee the proper
				# data is always written in the proper order. Open to better
				# ideas, too...

				worksheet.write(row,0,result['Project Name'])
				worksheet.write(row,1,result['Repo Path'])
				worksheet.write(row,2,result['Repo Name'])
				worksheet.write(row,3,result['Author Date'])
				worksheet.write(row,4,result['Author Name'])
				worksheet.write(row,5,result['Author Raw Email'])
				worksheet.write(row,6,result['Author Email'])
				worksheet.write(row,7,result['Author Affiliation'])
				worksheet.write(row,8,result['Committer Date'])
				worksheet.write(row,9,result['Committer Name'])
				worksheet.write(row,10,result['Committer Raw Email'])
				worksheet.write(row,11,result['Committer Email'])
				worksheet.write(row,12,result['Committer Affiliation'])
				worksheet.write(row,13,result['LoC Added'])
				worksheet.write(row,14,result['LoC Removed'])
				worksheet.write(row,15,result['Whitespace Changes'])
				worksheet.write(row,16,result['Commit'])
				worksheet.write(row,17,result['Filename'])

				row += 1


			if cursor.rowcount < num_records:
				more_data = False

			min_record = min_record + num_records

	workbook.close()

	if row > 1048575:

		print('\nWARNING: Exceeded maximum size for an Excel sheet. You probably\n'
			'need to export individual projects, use a more recent start date,\n'
			'limit the number of affiliations, or only export certain projects.\n')

def _configuration():

	# List all of the configurations

	settings_table = texttable.Texttable()
	settings_table.set_cols_align(['l','l','l'])
	settings_table.set_cols_width([2,40,47])

	print("\n--------\nCONFIGURATION\n--------\n")

	action = ''
	while action != 'r':

		# The overall status

		get_last_update = ("SELECT last_modified FROM settings "
			"WHERE setting='utility_status'")
		cursor.execute(get_last_update)
		utility_date = cursor.fetchone()['last_modified'].strftime("%B %d, %Y at %H:%m")
		utility_status = ("%s since %s" %
			(get_setting('utility_status',db,cursor), utility_date))

		settings_table.add_rows([
			['','Facade status',''],
			['','Current status of facade.worker.py',utility_status]])
		print("\n" + settings_table.draw() + "\n")

		settings_table.reset()

		# Data collection and display

		settings_table.add_rows([
			['ID','Data collection and display',''],
			['d1','Analyze patches committed after this date',
				get_setting('start_date',db,cursor)],
			['d2','Use this email when generating cached reports that are '
				'displayed on the website',
				get_setting('report_attribution',db,cursor)],
			['d3','Use this date when generating cached reports that are '
				'displayed on the website',get_setting('report_date',db,cursor)]])

		print("\n" + settings_table.draw() + "\n")

		settings_table.reset()

		# System variables

		settings_table.add_rows([
			['ID','System',''],
			['s1','Location of git repos (must be writable by user account doing the '
				'analysis)', get_setting('repo_directory',db,cursor)],
			['s2','Hours between attempted updated',
				get_setting('update_frequency',db,cursor)],
			['s3','Log level', get_setting('log_level',db,cursor)],
			['','Database version', get_setting('database_version',db,cursor)]])

		print("\n" + settings_table.draw() + "\n")

		settings_table.reset()

		# Google Analytics

		settings_table.add_rows([
			['ID','Google Analytics',''],
			['g1','Google Analytics tracking ID', get_setting('google_analytics',db,cursor)]])

		print("\n" + settings_table.draw() + "\n")

		settings_table.reset()

		print(" (<ID>) - Edit the <ID> setting\n"
			" (I)mport - Import Facade configurations\n"
			" (E)xport - Export Facade configurations\n"
			" (R)eturn - Return to the previous menu\n")
		action = input("What would you like to do? ").strip().lower()

		value = ''

		if action == 'd1':

			while value != 'r':

				print("Analyze patches committed after this date:\n")
				value = input("YYYY-MM-DD or (r)eturn: ").strip().lower()

				if (len(value) == 10 and
					re.match('([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))',value)):

					set_setting('start_date',value,db,cursor)
					break

				else:
					print("\nInvalid date\n")

		elif action == 'd2':

			while value != 'r':

				print("Use this email when generating cached reports that "
						"are displayed on the website:")
				value = input("(a)uthor, (c)ommitter, (r)eturn: ").strip().lower()

				if value == 'a':

					set_setting('report_attribution','author',db,cursor)
					break

				elif value == 'c':

					set_setting('report_attribution','committer',db,cursor)
					break

				else:
					print("\nInvalid selection\n")

		elif action == 'd3':

			while value != 'r':

				print("Use this date when generating cached reports that "
						"are displayed on the website:")
				value = input("(a)uthor, (c)ommitter, (r)eturn: ").strip().lower()

				if value == 'a':

					set_setting('report_date','author',db,cursor)
					break

				elif value == 'c':

					set_setting('report_date','committer',db,cursor)
					break

				else:
					print("\nInvalid selection\n")

		elif action == 's1':

			while value != 'r':

				print("\nLocation of git repos (must be writable by "
					"user account doing the analysis):")
				value = input("Absolute path or (r)eturn: ").strip()

				if value == '/':
					print("\nYou have selected the root filesystem. You can "
						"REALLY mess up your system this way.")

					confirm = ''

					while confirm not in ['y','n']:
						confirm = input("Are you sure? (y/n): ").strip().lower()

					if confirm == 'y':

						set_setting('repo_directory','/',db,cursor)
						break

				elif not value.startswith('/'):
					print("\nYou are using a relative path. This is not safe.")

				else:
					if not value.endswith('/'):
						value = value + '/'

					set_setting('repo_directory',value,db,cursor)
					break

		elif action == 's2':

			while value != 'r':

				print("\nHours between attempted updates:")
				value = input("4, 12, 24, or (r)eturn: ")

				if value in ['4','12','24']:

					set_setting('update_frequency',value,db,cursor)
					break

		elif action == 's3':

			while value != 'r':

				print("\nLog level:")
				value = input("(e)rror, (q)uiet, (i)nfo, (v)erbose, (d)ebug, or (r)eturn: ")

				if value == 'e':

					set_setting('log_level','Error',db,cursor)
					break

				elif value == 'q':

					set_setting('log_level','Quiet',db,cursor)
					break

				elif value == 'i':

					set_setting('log_level','Info',db,cursor)
					break

				elif value == 'v':

					set_setting('log_level','Verbose',db,cursor)
					break

				elif value == 'd':

					set_setting('log_level','Debug',db,cursor)
					break

		elif action == 'g1':

			while value != 'r':

				print("\nGoogle Analytics tracking ID:\n")
				value = input("ID from Google Analytics, or (r)eturn: ")

				if value == 'r':
					break

				elif len(value) > 0:

					set_setting('google_analytics',value,db,cursor)
					break

		elif action == 'i':

			import_action = ''

			while import_action != 'r':

				print("\n......\nIMPORT\n......\n\n"
					" (P)roject - Import project definitions\n"
					" R(e)po - Import repo definitions\n"
					" A(l)iases - Import aliases\n"
					" A(f)filiations - Import affiliations\n"
					" (T)ags - Import tags\n"
					" (S)ettings - Import Facade settings\n"
					" (R)eturn - Return to the previous menu\n")

				import_action = input("What would you like to do? ").strip().lower()

				if import_action == 'p':

					# Set a variable that is false until CSV headers are verified
					safe = False

					csv_file = os.path.expanduser(input("Path to projects CSV: ").strip())

					if not os.path.isfile(csv_file):

						print("\nFile not found.")
						continue

					with open(csv_file) as import_file:

						csv_reader = csv.reader(import_file)

						for line in csv_reader:

							# When the proper headers are there, start reading

							if (line[0].find('Project ID') in [0,1,2] and
								line[1].find('Name') in [0,1] and
								line[2].find('Description') in [0,1] and
								line[3].find('Website') in [0,1]):

								print("\nThis will clear any existing projects.\n")

								confirm = ''

								while confirm not in ['y','n']:
									confirm = input("Proceed? (y/n) ").strip().lower()

								if confirm == 'y':
									safe = True

									clear_projects = ("DELETE FROM projects")

									cursor.execute(clear_projects)
									db.commit()
									continue

								else:
									print("\nImport cancelled.")
									continue

							if safe:

								add_project = ("INSERT INTO projects "
									"(id,name,description,website) VALUES "
									"(%s,%s,%s,%s)")

								cursor.execute(add_project,(line[0], line[1],
									line[2], line[3]))
								db.commit()

					if not safe:

						print("\nIt appears the import has failed.\n")

				elif import_action == 'e':

					safe = False
					reset_repos = False

					csv_file = os.path.expanduser(input("Path to repos CSV: ").strip())

					if not os.path.isfile(csv_file):

						print("\nFile not found.")
						continue

					with open(csv_file) as import_file:

						csv_reader = csv.reader(import_file)

						for line in csv_reader:

							# When the proper headers are there, start reading

							if (line[0].find('Repo ID') in [0,1,2] and
								line[1].find('Projects ID') in [0,1] and
								line[2].find('Git') in [0,1] and
								line[3].find('Path') in [0,1] and
								line[4].find('Name') in [0,1] and
								line[5].find('Status') in [0,1]):

								print("\nThis will clear any existing repos.\n")

								confirm = ''

								while confirm not in ['y','n']:
									confirm = input("Proceed? (y/n) ").strip().lower()

								if confirm == 'y':
									safe = True

									clear_repos = ("DELETE FROM repos")

									cursor.execute(clear_repos)
									db.commit()

									reclone = ''

									while reclone not in ['y','n']:
										reclone = input("\nRe-clone all repos? (y/n) ").strip().lower()

									if reclone == 'y':
										reset_repos = True

									continue

								else:
									print("\nImport cancelled.")
									continue

							if safe:

								if reset_repos:

									add_repo = ("INSERT INTO repos "
										"(id,projects_id,git,status) VALUES "
										"(%s,%s,%s,'New')")

									cursor.execute(add_repo,(line[0], line[1],
										line[2]))
									db.commit()

								else:

									add_repo = ("INSERT INTO repos "
										"(id,projects_id,git,path,name,status) VALUES "
										"(%s,%s,%s,%s,%s,%s)")

									cursor.execute(add_repo,(line[0], line[1],
										line[2], line[3], line[4], line[5]))
									db.commit()

					if not safe:

						print("\nIt appears the import has failed.\n")

				elif import_action == 'l':

					safe = False

					csv_file = os.path.expanduser(input("Path to aliases CSV: ").strip())

					if not os.path.isfile(csv_file):

						print("\nFile not found.")
						continue

					with open(csv_file) as import_file:

						csv_reader = csv.reader(import_file)

						for line in csv_reader:

							# When the proper headers are there, start reading

							if (line[0].find('Canonical email') in [0,1,2] and
								line[1].find('Alias') in [0,1]):

								safe = True
								continue

							if safe:

								add_alias = ("INSERT INTO aliases "
									"(canonical,alias) VALUES "
									"(%s,%s) "
									"ON DUPLICATE KEY UPDATE active = TRUE")

								cursor.execute(add_alias,(line[0], line[1]))
								db.commit()

					if not safe:

						print("\nIt appears the import has failed.\n")

				elif import_action == 'f':

					safe = False

					csv_file = os.path.expanduser(input("Path to affiliations CSV: ").strip())

					if not os.path.isfile(csv_file):

						print("\nFile not found.")
						continue

					with open(csv_file) as import_file:

						csv_reader = csv.reader(import_file)

						for line in csv_reader:

							# When the proper headers are there, start reading

							if (line[0].find('Domain') in [0,1,2] and
								line[1].find('Affiliation') in [0,1] and
								line[2].find('Beginning on') in [0,1]):

								safe = True
								continue

							if safe:

								add_affiliation = ("INSERT INTO affiliations "
									"(domain,affiliation,start_date) VALUES "
									"(%s,%s,%s) "
									"ON DUPLICATE KEY UPDATE active = TRUE")

								cursor.execute(add_affiliation,(line[0], line[1],
									line[2]))
								db.commit()

					if not safe:

						print("\nIt appears the import has failed.\n")

				elif import_action == 't':

					safe = False

					csv_file = os.path.expanduser(input("Path to tags CSV: ").strip())

					if not os.path.isfile(csv_file):

						print("\nFile not found.")
						continue

					with open(csv_file) as import_file:

						csv_reader = csv.reader(import_file)

						for line in csv_reader:

							# When the proper headers are there, start reading

							if (line[0].find('Email') in [0,1,2] and
								line[1].find('Beginning on') in [0,1] and
								line[2].find('Ending on') in [0,1] and
								line[3].find('Tag') in [0,1]):

								safe = True
								continue

							if safe:

								if len(line[2]) > 0:
									add_tag = ("INSERT INTO special_tags "
										"(email,start_date,end_date,tag) VALUES "
										"(%s,%s,%s,%s) "
										"ON DUPLICATE KEY UPDATE email=email")

									cursor.execute(add_tag,(line[0], line[1],
										line[2], line[3]))
									db.commit()

								else:
									add_tag = ("INSERT INTO special_tags "
										"(email,start_date,tag) VALUES "
										"(%s,%s,%s) "
										"ON DUPLICATE KEY UPDATE email=email")

									cursor.execute(add_tag,(line[0], line[1],
										line[3]))
									db.commit()

					if not safe:

						print("\nIt appears the import has failed.\n")

				elif import_action == 's':

					safe = False

					csv_file = os.path.expanduser(input("Path to settings CSV: ").strip())

					if not os.path.isfile(csv_file):

						print("\nFile not found.")
						continue

					with open(csv_file) as import_file:

						csv_reader = csv.reader(import_file)

						for line in csv_reader:

							# When the proper headers are there, start reading

							if (line[0].find('Setting') in [0,1,2] and
								line[1].find('Value') in [0,1]):

								safe = True
								continue

							if safe:

								add_setting = ("INSERT INTO settings "
									"(setting,value) VALUES (%s,%s)")

								cursor.execute(add_setting,(line[0], line[1]))
								db.commit()

								# Add a pause, because the timestamp is used to
								# determine which setting is the most recent.
								# This ensures we don't get multiple settings
								# with the same timestamp, if the server doing
								# the insertion is faster than the timestamp
								# granularity.

								time.sleep(0.001)

						print("\nSettings file imported.")

					if not safe:

						print("\nIt appears the import has failed.\n")

		elif action == 'e':

			today = datetime.datetime.today().strftime('%Y-%m-%d')

			export_action = ''

			while export_action != 'r':

				print("\n......\nEXPORT\n......\n\n"
					" (P)roject - Export project definitions\n"
					" R(e)po - Export repo definitions\n"
					" A(l)iases - Export aliases\n"
					" A(f)filiations - Export affiliations\n"
					" (T)ags - Export tags\n"
					" (S)ettings - Export Facade settings\n"
					" (R)eturn - Return to the previous menu\n")

				export_action = input("What would you like to do? ").strip().lower()

				if export_action == 'p':

					get_projects = ("SELECT id,name,description,website FROM projects")

					cursor.execute(get_projects)
					projects = list(cursor)

					if os.path.isfile(os.path.expanduser('~/facade_projects_%s.csv' % today)):

						print("\nThe file '~/facade_projects_%s.csv' already exists.\n"
							% today)

						overwrite = ''

						while overwrite not in ['y','n']:
							overwrite = input("Overwrite? (y/n) ").strip().lower()

						if overwrite != 'y':
							break

					with open(os.path.expanduser('~/facade_projects_%s.csv' % today),
							'w', newline='', encoding='utf-8') as csv_file:

						csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

						# Write the UTF8 BOM and headers

						csv_file.write('\ufeff')

						csv_writer.writerow(['Project ID','Name','Description','Website'])

						for project in projects:
							csv_writer.writerow([project['id'], project['name'],
								project['description'],project['website']])

						print("\nExported to ~/facade_projects_%s.csv" % today)

				if export_action == 'e':

					get_repos = ("SELECT id,projects_id,git,path,name,status FROM repos")

					cursor.execute(get_repos)
					repos = list(cursor)

					if os.path.isfile(os.path.expanduser('~/facade_repos_%s.csv' % today)):

						print("\nThe file '~/facade_repos_%s.csv' already exists.\n"
							% today)

						overwrite = ''

						while overwrite not in ['y','n']:
							overwrite = input("Overwrite? (y/n) ").strip().lower()

						if overwrite != 'y':
							break

					with open(os.path.expanduser('~/facade_repos_%s.csv' % today),
							'w', newline='', encoding='utf-8') as csv_file:

						csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

						# Write the UTF8 BOM and headers

						csv_file.write('\ufeff')

						csv_writer.writerow(['Repo ID','Projects ID','Git','Path','Name','Status'])

						for repo in repos:
							csv_writer.writerow([repo['id'], repo['projects_id'],
								repo['git'],repo['path'],repo['name'],repo['status']])

						print("\nExported to ~/facade_repos_%s.csv" % today)

				if export_action == 'l':

					get_aliases = ("SELECT canonical,alias FROM aliases WHERE active = TRUE")

					cursor.execute(get_aliases)
					aliases = list(cursor)

					if os.path.isfile(os.path.expanduser('~/facade_aliases_%s.csv' % today)):

						print("\nThe file '~/facade_aliases_%s.csv' already exists.\n"
							% today)

						overwrite = ''

						while overwrite not in ['y','n']:
							overwrite = input("Overwrite? (y/n) ").strip().lower()

						if overwrite != 'y':
							break

					with open(os.path.expanduser('~/facade_aliases_%s.csv' % today),
							'w', newline='', encoding='utf-8') as csv_file:

						csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

						# Write the UTF8 BOM and headers

						csv_file.write('\ufeff')

						csv_writer.writerow(['Canonical email','Alias'])

						for alias in aliases:
							csv_writer.writerow([alias['canonical'], alias['alias']])

						print("\nExported to ~/facade_aliases_%s.csv" % today)

				if export_action == 'f':

					get_affiliations = ("SELECT domain,affiliation,start_date "
						"FROM affiliations WHERE active = TRUE")

					cursor.execute(get_affiliations)
					affiliations = list(cursor)

					if os.path.isfile(os.path.expanduser('~/facade_affiliations_%s.csv' % today)):

						print("\nThe file '~/facade_affiliations_%s.csv' already exists.\n"
							% today)

						overwrite = ''

						while overwrite not in ['y','n']:
							overwrite = input("Overwrite? (y/n) ").strip().lower()

						if overwrite != 'y':
							break

					with open(os.path.expanduser('~/facade_affiliations_%s.csv' % today),
							'w', newline='', encoding='utf-8') as csv_file:

						csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

						# Write the UTF8 BOM and headers

						csv_file.write('\ufeff')

						csv_writer.writerow(['Domain','Affiliation','Beginning on'])

						for affiliation in affiliations:
							csv_writer.writerow([affiliation['domain'],
								affiliation['affiliation'], affiliation['start_date']])

						print("\nExported to ~/facade_affiliations_%s.csv" % today)

				if export_action == 't':

					get_tags = ("SELECT email,start_date,end_date,tag FROM special_tags")

					cursor.execute(get_tags)
					tags = list(cursor)

					if os.path.isfile(os.path.expanduser('~/facade_tags_%s.csv' % today)):

						print("\nThe file '~/facade_tags_%s.csv' already exists.\n"
							% today)

						overwrite = ''

						while overwrite not in ['y','n']:
							overwrite = input("Overwrite? (y/n) ").strip().lower()

						if overwrite != 'y':
							break

					with open(os.path.expanduser('~/facade_tags_%s.csv' % today),
							'w', newline='', encoding='utf-8') as csv_file:

						csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

						# Write the UTF8 BOM and headers

						csv_file.write('\ufeff')

						csv_writer.writerow(['Email','Beginning on','Ending on','Tag'])

						for tag in tags:
							csv_writer.writerow([tag['email'], tag['start_date'],
								tag['end_date'], tag['tag']])

						print("\nExported to ~/facade_tags_%s.csv" % today)

				if export_action == 's':

					get_settings = ("SELECT setting,value FROM settings "
							"ORDER BY id ASC")

					cursor.execute(get_settings)
					settings = list(cursor)

					if os.path.isfile(os.path.expanduser('~/facade_settings_%s.csv' % today)):

						print("\nThe file '~/facade_settings_%s.csv' already exists.\n"
							% today)

						overwrite = ''

						while overwrite not in ['y','n']:
							overwrite = input("Overwrite? (y/n) ").strip().lower()

						if overwrite != 'y':
							break

					with open(os.path.expanduser('~/facade_settings_%s.csv' % today),
							'w', newline='', encoding='utf-8') as csv_file:

						csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)

						# Write the UTF8 BOM and headers

						csv_file.write('\ufeff')

						csv_writer.writerow(['Setting','Value'])

						for setting in settings:
							csv_writer.writerow([setting['setting'], setting['value']])

						print("\nExported to ~/facade_settings_%s.csv" % today)


### The real program starts here ###

if __name__ == '__main__':

	try:
		config = configparser.ConfigParser()
		config.read('../utilities/db.cfg')

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
		print("Could not read database configuration. Have you run setup.py?")
		sys.exit(1)

	try:
		db = MySQLdb.connect(
			host = db_host,
			user = db_user,
			passwd = db_pass,
			db = db_name,
			charset = 'utf8mb4')

		cursor = db.cursor(MySQLdb.cursors.DictCursor)

		db_people = MySQLdb.connect(
			host = db_host_people,
			user = db_user_people,
			passwd = db_pass_people,
			db = db_name_people,
			charset = 'utf8mb4')

		cursor_people = db_people.cursor(MySQLdb.cursors.DictCursor)

	except:
		print("Could not connect to database.")
		sys.exit(1)

	# Set some global variables

	page_size = 25

	# Beginning of the interactive part

	welcome_table = texttable.Texttable()
	welcome_table.set_cols_align(['c'])
	welcome_table.set_cols_width([95])
	welcome_table.header(['Welcome to the Facade CLI'])
	welcome_table.add_row([("This tool allows you to add and remove projects "
	"and repositories, and enables you to modify Facade's configuration.  It "
	"can be used in addition to or as a replacement for the web UI.")])

	# Begin constructing the summary statistics

	get_report_attribution = ("SELECT value FROM settings "
		"WHERE setting = 'report_attribution' "
		"ORDER BY last_modified DESC LIMIT 1")

	cursor.execute(get_report_attribution)
	report_attribution = cursor.fetchone()['value']

	# Lines of code, and whether it's plural

	get_loc = "SELECT SUM(added) AS added FROM analysis_data"

	cursor.execute(get_loc)
	loc = cursor.fetchone()['added']
	loc_plural = 's'

	if loc:
		if loc == 1:
			loc_plural = ''
	else:
		loc = 0

	# Number of devs, and whether it's plural

	get_devs = "SELECT COUNT(%s_email) AS emails FROM analysis_data" % report_attribution

	cursor.execute(get_devs)
	devs = cursor.fetchone()['emails']
	devs_plural = 's'

	if devs:
		if devs == 1:
			devs_plural = ''
	else:
		devs = 0

	# Number of orgs, and whether it's plural

	get_orgs = "SELECT COUNT(%s_affiliation) AS orgs FROM analysis_data" % report_attribution

	cursor.execute(get_orgs)
	orgs = cursor.fetchone()['orgs']
	orgs_plural = 's'

	if orgs:
		if orgs == 1:
			orgs_plural = ''
	else:
		orgs = 0

	# Number of repos, and whether it's plural

	get_repos = "SELECT COUNT(id) as repos FROM repos"

	cursor.execute(get_repos)
	repos = cursor.fetchone()['repos']
	repos_plural = 's'

	if repos:
		if repos == 1:
			repos_plural = ''
	else:
		repos = 0

	# Number of projects, and whether it's plural

	get_projects = "SELECT COUNT(id) as projects FROM projects"

	cursor.execute(get_projects)
	projects = cursor.fetchone()['projects']
	projects_plural = 's'

	if projects:
		if projects == 1:
			projects_plural = ''
	else:
		projects = 0

	# The amount of time for the analysis

	get_start_date = ("SELECT value FROM settings "
		"WHERE setting = 'start_date' "
		"ORDER BY last_modified DESC LIMIT 1")

	cursor.execute(get_start_date)
	start_date = cursor.fetchone()['value']

	welcome_table.add_row([(
		"You are currently tracking %s line%s of code,\n"
		"committed by %s developer%s,\n"
		"from %s known organization%s,\n"
		"working in %s repo%s,\n"
		"on %s project%s,\n"
		"since %s."
		%	(loc,loc_plural,
			devs,devs_plural,
			orgs,orgs_plural,
			repos,repos_plural,
			projects,projects_plural,
			start_date))])
	print("\n" + welcome_table.draw())

	action = ''

	while action != 'q':

		print("\n=========\nMAIN MENU\n=========\n\n"
			" (P)rojects - Add, remove, or modify projects and their repositories.\n"
			" (R)epositories - View the status of tracked repositories.\n"
			" (A)liases and affiliations - Add, remove, or modify contributor information.\n"
			" (T)ags - Add and remove tags to help further organize contributors.\n"
			" (E)xport - Get the results as an Excel file.\n"
			" (C)onfiguration - Edit the global configuration.\n"
			" (Q)uit - Exit Facade CLI.\n")

		action = input("What would you like to do? ").strip().lower()

		if action == 'p':
			_manage_projects()

		elif action == 'r':
			_list_repo_status()

		elif action == 'a':
			_aliases_and_affiliations()

		elif action == 't':
			_tags()

		elif action == 'e':
			_export()

		elif action == 'c':
			_configuration()

		elif action == 'q':
			continue

		else:
			print("Invalid selection\n")
			continue

	farewell_table = texttable.Texttable()
	farewell_table.set_cols_align(['c'])
	farewell_table.set_cols_width([95])
	farewell_table.header(['Thank you for using Facade'])
	farewell_table.add_row([("Brian Warner (c)\n"
		"https://github.com/brianwarner/facade")])
	print("\n" + farewell_table.draw() + "\n")

