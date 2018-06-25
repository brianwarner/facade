#!/bin/bash

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

echo "
This script will install the necessary dependencies to run Facade in headless
mode. This means that it will not install Apache or the required PHP packages.
You must use the CLI to configure Facade and export analysis data, which is
available in cli/facade.py

You can always convert to a full installation by running the full script to fill
in any missing packages, should you change your mind later:
 $ ./install_deps-deb-full.sh

Installing any missing dependencies...
"

sudo apt-get install mysql-client mysql-server \
python3 python3-mysqldb python3-bcrypt python3-xlsxwriter python3-texttable

echo "
If everything went well, your next step is to run setup:
 $ ./setup.py
 "

