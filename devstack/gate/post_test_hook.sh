#!/bin/bash

set -ex

# Run the Designate DevStack exercises
$BASE/new/designate/devstack/exercise.sh

# Import functions needed for the below workaround
source $BASE/new/devstack/functions

# Workaround for Tempest architectural changes
# See bugs:
# 1) https://bugs.launchpad.net/manila/+bug/1531049
# 2) https://bugs.launchpad.net/tempest/+bug/1524717
TEMPEST_CONFIG=$BASE/new/tempest/etc/tempest.conf
ADMIN_TENANT_NAME=${ADMIN_TENANT_NAME:-"admin"}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-"secretadmin"}

sudo chown -R jenkins:stack $BASE/new/tempest
sudo chown -R jenkins:stack $BASE/data/tempest

iniset $TEMPEST_CONFIG auth admin_username ${ADMIN_USERNAME:-"admin"}
iniset $TEMPEST_CONFIG auth admin_password $ADMIN_PASSWORD
iniset $TEMPEST_CONFIG auth admin_tenant_name $ADMIN_TENANT_NAME
iniset $TEMPEST_CONFIG auth admin_domain_name ${ADMIN_DOMAIN_NAME:-"Default"}
iniset $TEMPEST_CONFIG identity username ${TEMPEST_USERNAME:-"demo"}
iniset $TEMPEST_CONFIG identity password $ADMIN_PASSWORD
iniset $TEMPEST_CONFIG identity tenant_name ${TEMPEST_TENANT_NAME:-"demo"}
iniset $TEMPEST_CONFIG identity alt_username ${ALT_USERNAME:-"alt_demo"}
iniset $TEMPEST_CONFIG identity alt_password $ADMIN_PASSWORD
iniset $TEMPEST_CONFIG identity alt_tenant_name ${ALT_TENANT_NAME:-"alt_demo"}
iniset $TEMPEST_CONFIG validation ip_version_for_ssh 4
iniset $TEMPEST_CONFIG validation ssh_timeout $BUILD_TIMEOUT
iniset $TEMPEST_CONFIG validation network_for_ssh ${PRIVATE_NETWORK_NAME:-"private"}

# Run the Designate Tempest tests
sudo ./run_tempest_tests.sh
