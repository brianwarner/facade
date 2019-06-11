#!/usr/bin/python3

import os
import glob

files = glob.glob('%s/generate*.py' % os.path.dirname(__file__))

__all__ = list()

for f in files:
	if os.path.isfile(f):
		__all__.append(os.path.basename(f)[:-3])

