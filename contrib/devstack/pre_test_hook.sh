#!/bin/bash

set -ex

DESIGNATE_BASE=/opt/stack/new/designate
DEVSTACK_BASE=/opt/stack/new/devstack

# Install designate devstack integration
cp -R $DESIGNATE_BASE/contrib/devstack/* $DEVSTACK_BASE/
