#!/usr/bin/python3

# Copyright 2017-2018 Brian Warner
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

# Create summary Excel file
#
# This script creates a formatted Excel file for easier use in reports. It can
# also be used as a template for generating other types of Excel files. Main
# places to be modified when creating a derivative script are marked with #-->

import sys
import MySQLdb
import imp
import time
import datetime
import xlsxwriter
import os

dirname = os.path.dirname
filepath = os.path.abspath(__file__)
sys.path.append(dirname(dirname(filepath)))

try:
	imp.find_module('db')
	from db import db,cursor
except:
	sys.exit("Can't find db.py. Have you created it?")

def get_setting(setting):

# Get a setting from the database

	query = ("SELECT value FROM settings WHERE setting='%s' ORDER BY "
		"last_modified DESC LIMIT 1" % setting)
	cursor.execute(query)
	return cursor.fetchone()["value"]

### The real program starts here ###

#--> Set your filename

filename = 'facade_summary-projects_by_LoC_and_number_contributors_by_year.xlsx'

#--> Set the description of the data

detail = 'LoC added (Unique emails)'

#--> Change this to modify the names of each worksheet

sheets = reversed(list(range(int(get_setting('start_date')[:4]),
	datetime.datetime.now().year + 1)))

#--> Change this to modify the x axis

get_x_axis = "SELECT name,id FROM projects"

cursor.execute(get_x_axis)
x_axis = list(cursor)

facade_dir = dirname(dirname(dirname(filepath)))
outfile = os.path.join(facade_dir,'files',filename)

workbook = xlsxwriter.Workbook(outfile)

bold = workbook.add_format({'bold': True})
italic = workbook.add_format({'italic': True})
bold_italic = workbook.add_format({'bold': True, 'italic': True})
numformat = workbook.add_format({'num_format': '#,##0'})

for sheet in sheets:

	worksheet = workbook.add_worksheet(str(sheet))

	worksheet.write(1,1,'Report generated on %s by Facade' %
		time.strftime('%Y-%m-%d'),bold)
	worksheet.write(2,1,'https://github.com/brianwarner/facade')
	worksheet.write(3,1,'Format: %s' % detail)

	top_row = 5
	first_col = 1

	col = first_col + 1

	for x in x_axis:

		#--> Change the value of x[''] to match SELECT statment

		worksheet.write(top_row,col,x['name'],bold_italic)

		col += 1

	#--> Change this to modify the y axis

	get_y_axis = ("SELECT DISTINCT affiliation FROM project_annual_cache "
		"WHERE year = %s "
		"ORDER BY affiliation ASC"
		% sheet)

	cursor.execute(get_y_axis)
	y_axis = list(cursor)

	row = top_row + 1

	for y in y_axis:

		#--> Change the value of y[''] to match SELECT statement

		worksheet.write(row,first_col,y['affiliation'],bold)

		col = first_col + 1

		for x in x_axis:

			#--> Change this to modify the data

			get_stats = ("SELECT FORMAT(SUM(added),0) AS added, "
				"FORMAT(COUNT(email),0) AS emails "
				"FROM project_annual_cache "
				"WHERE affiliation = '%s' "
				"AND projects_id = %s "
				"AND year = %s"
				% (y['affiliation'].replace("'","\\'"),
				x['id'], sheet))

			cursor.execute(get_stats)
			stats = list(cursor)

			for stat in stats:

				#--> Change this to define the format for each data point

				if stat['added']:
					worksheet.write(row,col,'%s (%s)'
						% (stat['added'], stat['emails']))

			col += 1
		row += 1

workbook.close()

