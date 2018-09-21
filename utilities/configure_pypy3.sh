#!/bin/bash

# Copyright 2018 Brian Warner
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

function usage {

	printf "\n*** Note: This is an optional step to boost performance. ***

This script helps you configure pypy3, which can greatly improve execution
times over the standard Python3 interpreter. Each Python distribution installs
its pip and its own modules when using pip, so this script will only affect
pypy3. This means you need to pay attention to *which* pip3 you are invoking,
as you probably also have one on your system which is specific to python3. As
such, simply running pip3 probably won't help you much. This script will do its
best to make sure you're installing modules where pypy3 can use them.\n\n"
}

function no_pypy {

printf "*** WARNING: Can't find pypy3 ***

Some distros provide pypy3, some do not.  If it isn't available in your package
repos, you can download a portable pypy3 binary from:

  https://github.com/squeaky-pl/portable-pypy#portable-pypy-distribution-for-linux

Setting up the portable binary is pretty easy:
  1) Decompress the archive
  2) Rename it something sane (e.g. 'pypy3')
  3) Put it somewhere global (e.g. '/opt/pypy3')
  4) Add it to your execution path:

     sudo ln -s /opt/pypy3/bin/pypy3 /usr/local/bin/pypy3

Once you have successfully installed pypy3, you should rerun this script.\n\n"
}

# The real script starts here

usage

if [ -z `which pypy3` ]; then
	no_pypy
	exit
fi

PYPY_PATH=$(dirname $(realpath $(which pypy3)))

$PYPY_PATH/pypy3 -m ensurepip
$PYPY_PATH/pip3 install pymysql bcrypt xlsxwriter texttable

