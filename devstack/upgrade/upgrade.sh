#!/usr/bin/env bash

# ``upgrade-designate``

echo "*********************************************************************"
echo "Begin $0"
echo "*********************************************************************"

# Clean up any resources that may be in use
cleanup() {
    set +o errexit

    echo "********************************************************************"
    echo "ERROR: Abort $0"
    echo "********************************************************************"

    # Kill ourselves to signal any calling process
    trap 2; kill -2 $$
}

trap cleanup SIGHUP SIGINT SIGTERM

# Keep track of the grenade directory
RUN_DIR=$(cd $(dirname "$0") && pwd)

# Source params
source $GRENADE_DIR/grenaderc

# Import common functions
source $GRENADE_DIR/functions

# Get the Apache functions
source ${TARGET_DEVSTACK_DIR}/lib/apache

# This script exits on an error so that errors don't compound and you see
# only the first error that occurred.
set -o errexit

# Upgrade designate
# ============

# Get functions from current DevStack
source $TARGET_DEVSTACK_DIR/stackrc
source $TARGET_DEVSTACK_DIR/lib/tls
source $(dirname $(dirname $BASH_SOURCE))/plugin.sh
source $(dirname $(dirname $BASH_SOURCE))/settings

# Print the commands being run so that we can see the command that triggers
# an error.  It is also useful for following allowing as the install occurs.
set -o xtrace

# Save current config files for posterity
[[ -d $SAVE_DIR/etc.designate ]] || cp -pr $DESIGNATE_CONF_DIR $SAVE_DIR/etc.designate

# Hack: uninstall link to removed dashboard panel in order to avoid horizon from failing
if [ -L $DEST/horizon/openstack_dashboard/local/enabled/_1720_project_dns_panel.py ]; then
    rm $DEST/horizon/openstack_dashboard/local/enabled/_1720_project_dns_panel.py
fi

# install_designate()
if is_ubuntu; then
    install_package libcap2-bin
elif is_fedora; then
    # bind-utils package provides `dig`
    install_package libcap bind-utils
fi

git_clone $DESIGNATE_REPO $DESIGNATE_DIR $DESIGNATE_BRANCH
setup_develop $DESIGNATE_DIR

install_designateclient

# The designateclient may have changed location
# (/opt/stack/new/python-designateclient) so we need to restart neutron
if is_service_enabled q-svc; then
    restart_service devstack@q-svc.service
fi

# calls upgrade-designate for specific release
upgrade_project designate $RUN_DIR $BASE_DEVSTACK_BRANCH $TARGET_DEVSTACK_BRANCH

# Migrate the database
$DESIGNATE_BIN_DIR/designate-manage --config-file $DESIGNATE_CONF \
                                    database sync || die $LINENO "DB sync error"

# Start designate
run_process designate-central "$DESIGNATE_BIN_DIR/designate-central --config-file $DESIGNATE_CONF"
run_process "designate-api" "$(which uwsgi) --procname-prefix designate-api --ini $DESIGNATE_UWSGI_CONF"
run_process designate-producer "$DESIGNATE_BIN_DIR/designate-producer --config-file $DESIGNATE_CONF"
run_process designate-worker "$DESIGNATE_BIN_DIR/designate-worker --config-file $DESIGNATE_CONF"
run_process designate-mdns "$DESIGNATE_BIN_DIR/designate-mdns --config-file $DESIGNATE_CONF"
run_process designate-sink "$DESIGNATE_BIN_DIR/designate-sink --config-file $DESIGNATE_CONF"
restart_apache_server

# Start proxies if enabled
if is_service_enabled designate-api && is_service_enabled tls-proxy; then
    start_tls_proxy '*' $DESIGNATE_SERVICE_PORT $DESIGNATE_SERVICE_HOST $DESIGNATE_SERVICE_PORT_INT &
fi

if ! timeout $SERVICE_TIMEOUT sh -c "while ! wget --no-proxy -q -O- $DESIGNATE_SERVICE_PROTOCOL://$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT/dns; do sleep 1; done"; then
    die $LINENO "Designate did not start"
fi

# Don't succeed unless the service come up
ensure_services_started designate-api designate-central designate-producer designate-worker designate-mdns designate-sink

set +o xtrace
echo "*********************************************************************"
echo "SUCCESS: End $0"
echo "*********************************************************************"
