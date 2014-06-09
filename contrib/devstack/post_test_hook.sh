#!/bin/bash

set -ex

DESIGNATE_BASE=/opt/stack/new/designate
DEVSTACK_BASE=/opt/stack/new/devstack

# Run the Designate DevStack exercises
cd $DEVSTACK_BASE
./exercises/designate.sh
