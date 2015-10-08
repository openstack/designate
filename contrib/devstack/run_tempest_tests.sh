#!/bin/bash

set -ex

cd /opt/stack/new/designate/devstack/gate
./run_tempest_tests.sh
