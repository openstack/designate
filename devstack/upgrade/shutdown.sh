#!/bin/bash

# ``shutdown-designate``

set -o errexit

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions

# We need base DevStack functions for this
source $BASE_DEVSTACK_DIR/functions
source $BASE_DEVSTACK_DIR/stackrc # needed for status directory

source $BASE_DEVSTACK_DIR/lib/tls
source ${GITDIR[designate]}/devstack/plugin.sh

set -o xtrace

stop_process designate-central
stop_process designate-api
stop_process designate-mdns
stop_process designate-agent
stop_process designate-sink
if is_service_enabled designate-worker; then
    stop_process designate-worker
    stop_process designate-producer
else
    stop_process designate-pool-manager
    stop_process designate-zone-manager
fi

# sanity check that service is actually down
ensure_services_stopped designate-api designate-central designate-mdns designate-agent designate-sink
if is_service_enabled designate-worker; then
    ensure_services_stopped designate-worker designate-producer
else
    ensure_services_stopped designate-pool-manager designate-zone-manager
fi
