#!/bin/bash

set -ex

export KEEP_LOCALRC=1
export ENABLED_SERVICES=designate,designate-api,designate-central,designate-sink,designate-mdns

# Prepare some localrc values
pushd $BASE/new/devstack
echo "DESIGNATE_SERVICE_PORT_DNS=5322" >> $BASE/new/devstack/localrc
popd

# Run DevStack Gate
$BASE/new/devstack-gate/devstack-vm-gate.sh
