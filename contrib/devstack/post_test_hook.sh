#!/bin/bash

set -ex

# Run the Designate DevStack exercises
$BASE/new/devstack/exercises/designate.sh

# Run the Designate Tempest tests
#sudo ./run_tempest_tests.sh
