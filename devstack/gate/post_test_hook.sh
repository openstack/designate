#!/bin/bash

set -ex

# Run the Designate DevStack exercises
$BASE/new/designate/devstack/exercise.sh

# Run the Designate Tempest tests
sudo ./run_tempest_tests.sh
