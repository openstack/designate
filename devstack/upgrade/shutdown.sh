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
stop_process designate-pool-manager
stop_process designate-zone-manager
stop_process designate-mdns
stop_process designate-agent
stop_process designate-sink

# sanity check that service is actually down
ensure_services_stopped designate-api designate-central designate-pool-manager designate-zone-manager designate-mdns designate-agent designate-sink
