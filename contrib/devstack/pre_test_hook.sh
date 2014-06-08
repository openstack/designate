#!/bin/bash

set -ex

# Install designate devstack integration
DESIGNATE_BASE=/opt/stack/new/designate
DEVSTACK_BASE=/opt/stack/new/devstack
cp -R $DESIGNATE_BASE/contrib/devstack/* $DEVSTACK_BASE/
