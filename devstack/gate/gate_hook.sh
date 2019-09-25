#!/bin/bash

set -ex

pushd $BASE/new/devstack

DEVSTACK_GATE_DESIGNATE_DRIVER=${DEVSTACK_GATE_DESIGNATE_DRIVER:-pdns4}

export KEEP_LOCALRC=1
export ENABLED_SERVICES=designate,designate-api,designate-central,designate-sink,designate-mdns,designate-worker,designate-producer

echo "DESIGNATE_SERVICE_PORT_DNS=5322" >> $BASE/new/devstack/localrc
echo "DESIGNATE_BACKEND_DRIVER=$DEVSTACK_GATE_DESIGNATE_DRIVER" >> $BASE/new/devstack/localrc
echo "DESIGNATE_PERIODIC_RECOVERY_INTERVAL=20" >> $BASE/new/devstack/localrc
echo "DESIGNATE_PERIODIC_SYNC_INTERVAL=20" >> $BASE/new/devstack/localrc


# Pass through any DESIGNATE_ env vars to the localrc file
env | grep -E "^DESIGNATE_" >> $BASE/new/devstack/localrc || :

popd

# Run DevStack Gate
$BASE/new/devstack-gate/devstack-vm-gate.sh
