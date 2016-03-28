#!/bin/bash -e
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

DESIGNATE_CLI_DIR=${DESIGNATE_CLI_DIR:-"$BASE/new/python-designateclient"}
TEMPEST_DIR=${TEMPEST_DIR:-"$BASE/new/tempest"}
export TEMPEST_CONFIG=$TEMPEST_DIR/etc/tempest.conf

pushd $DESIGNATE_CLI_DIR

# we need the actual openstack executable which is not installed by tox
virtualenv "$DESIGNATE_CLI_DIR/.venv"
source "$DESIGNATE_CLI_DIR/.venv/bin/activate"
pip install python-openstackclient
pip install .

tox -e functional -- --concurrency 4
popd
