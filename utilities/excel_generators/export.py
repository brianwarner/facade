#!/usr/bin/python

## Copyright 2017 Brian Warner
#
# This file is part of Facade, and is made available under the terms of the GNU
# General Public License version 2.
#
# SPDX-License-Identifier:        GPL-2.0

# Create summary Excel file
#
# This script creates a formatted Excel file for easier use in reports. It can
# also be used as a template for generating other types of Excel files.

import sys
import MySQLdb
import imp
import time
import datetime

sys.path.append('../')

try:
	imp.find_module('db')
	from db import db,cursor
except:
	sys.exit("Can't find db.py. Have you created it?")

import xlsxwriter

def get_setting(setting):

# Get a setting from the database

	query = ("SELECT value FROM settings WHERE setting='%s' ORDER BY "
		"last_modified DESC LIMIT 1" % setting)
	cursor.execute(query)
	return cursor.fetchone()["value"]

### The real program starts here ###

# Modify as appropriate

filename = '../../files/facade_summary-projects_by_LoC_and_number_contributors_by_year.xlsx'
detail = 'LoC added (Unique emails)'

min_year = int(get_setting('start_date')[:4])
current_year = datetime.datetime.now().year

workbook = xlsxwriter.Workbook(filename)

bold = workbook.add_format({'bold': True})
italic = workbook.add_format({'italic': True})
bold_italic = workbook.add_format({'bold': True, 'italic': True})
numformat = workbook.add_format({'num_format': '#,##0'})

# Get the x axis

get_x_axis = "SELECT name,id FROM projects"

cursor.execute(get_x_axis)
x_axis = list(cursor)

for year in range(min_year, current_year+1):

	worksheet = workbook.add_worksheet(str(year))

	# Write some information about the analysis

	worksheet.write(1,1,'Report generated on %s by Facade' %
		time.strftime('%Y-%m-%d'),bold)
	worksheet.write(2,1,'https://github.com/brianwarner/facade')
	worksheet.write(3,1,'Format: %s' % detail)

	top_row = 5
	first_col = 1

	# Write the x axis headers

	col = first_col + 1

	for x in x_axis:

		worksheet.write(top_row,col,x['name'],bold_italic)

		col += 1

	# The following SQL statement defines the y axis. If you want to limit the y
	# axis by any criteria, this is the place to do it.

	get_y_axis = ("SELECT DISTINCT affiliation FROM project_annual_cache "
		"WHERE year = %s "
		"ORDER BY affiliation ASC"
		% year)

	cursor.execute(get_y_axis)
	y_axis = list(cursor)

	row = top_row + 1

	for y in y_axis:

		# Write the y axis items

		worksheet.write(row,first_col,y['affiliation'],bold)

		col = first_col + 1

		# Walk through the headers for each y axis item. If you want to modify
		# the data that is presented, this is the place to do it.

		for x in x_axis:

			get_stats = ("SELECT FORMAT(SUM(added),0) AS added, "
				"FORMAT(COUNT(email),0) AS emails "
				"FROM project_annual_cache "
				"WHERE affiliation = '%s' "
				"AND projects_id = %s "
				"AND year = %s"
				% (y['affiliation'].replace("'","\\'"),
				x['id'], year))

			cursor.execute(get_stats)
			stats = list(cursor)

			for stat in stats:

				if stat['added']:

					# This is where you define the format for each data point

					worksheet.write(row,col,'%s (%s)'
						%(stat['added'], stat['emails']))

			col += 1
		row += 1

workbook.close()

