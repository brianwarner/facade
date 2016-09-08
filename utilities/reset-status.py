#!/usr/bin/python

# Copyright 2016 Brian Warner
#
# This file is part of Facade, and is made available under the terms of the GNU
# General Public License version 2.
# SPDX-License-Identifier:        GPL-2.0

# Reset a stuck status
#
# The facade-worker.py script will only run if the status in the db is idle. If
# it is killed halfway through, this can leave it in an erroneous state. This
# script resets it. Only run it if you know no analysis is actually running,
# otherwise you'll thrash your machine.

import MySQLdb
from database import db,cursor

query = "UPDATE settings SET value='Idle' WHERE setting='utility_status'"
cursor.execute(query)
db.commit()

query = ("INSERT INTO utility_log (level,status) VALUES "
	"('Error','facade-worker.py manually reset')")
cursor.execute(query)
db.commit()

cursor.close()
db.close()

