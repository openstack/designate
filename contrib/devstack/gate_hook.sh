#!/bin/bash

set -ex

pushd $BASE/new/devstack

export KEEP_LOCALRC=1
export ENABLED_SERVICES=designate,designate-api,designate-central,designate-sink,designate-mdns,designate-pool-manager

echo "DESIGNATE_SERVICE_PORT_DNS=5322" >> $BASE/new/devstack/localrc

DEVSTACK_GATE_DESIGNATE_DRIVER=${DEVSTACK_GATE_DESIGNATE_DRIVER:-powerdns}

if [ "$DEVSTACK_GATE_DESIGNATE_DRIVER" == "powerdns" ]; then
    echo "DESIGNATE_BACKEND_DRIVER=powerdns" >> $BASE/new/devstack/localrc

elif [ "$DEVSTACK_GATE_DESIGNATE_DRIVER" == "bind9" ]; then
    echo "DESIGNATE_BACKEND_DRIVER=bind9_pool" >> $BASE/new/devstack/localrc

fi

popd

# Run DevStack Gate
$BASE/new/devstack-gate/devstack-vm-gate.sh
