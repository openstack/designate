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
stop_process designate-sink
stop_process designate-worker
stop_process designate-producer


# sanity check that service is actually down
ensure_services_stopped designate-api designate-central designate-mdns designate-sink designate-worker designate-producer

