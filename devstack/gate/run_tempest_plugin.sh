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

# TODO(kiall): One old style tests are no longer used, we should switch from
# this pattern for executing the tests to a true tempest gate job.

# How many seconds to wait for the API to be responding before giving up
API_RESPONDING_TIMEOUT=20

if ! timeout ${API_RESPONDING_TIMEOUT} sh -c "while ! curl -s http://127.0.0.1:9001/ 2>/dev/null | grep -q 'v1' ; do sleep 1; done"; then
    echo "The Designate API failed to respond within ${API_RESPONDING_TIMEOUT} seconds"
    exit 1
fi

echo "Successfully contacted the Designate API"

# Where Tempest code lives
TEMPEST_DIR=${TEMPEST_DIR:-"$BASE/new/tempest"}

pushd $TEMPEST_DIR
tox -e all-plugin -- designate
popd
