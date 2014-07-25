#!/bin/bash

set -ex

# Install designate devstack integration
cp -R $BASE/new/designate/contrib/devstack/* $BASE/new/devstack

# Temp Hack to remove the localrc we copy over, will be fixed in
# the next review
rm $BASE/new/devstack/localrc
