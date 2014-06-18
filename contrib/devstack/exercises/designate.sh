#!/usr/bin/env bash

# **designate.sh**

# Simple Tests to verify designate is running

echo "*********************************************************************"
echo "Begin DevStack Exercise: $0"
echo "*********************************************************************"

# This script exits on an error so that errors don't compound and you see
# only the first error that occurred.
set -o errexit

# Print the commands being run so that we can see the command that triggers
# an error.  It is also useful for following allowing as the install occurs.
set -o xtrace


# Settings
# ========

# Keep track of the current directory
EXERCISE_DIR=$(cd $(dirname "$0") && pwd)
TOP_DIR=$(cd $EXERCISE_DIR/..; pwd)

# Import common functions
source $TOP_DIR/functions

# Import configuration
source $TOP_DIR/openrc

# Import exercise configuration
source $TOP_DIR/exerciserc

# Skip if designate is not enabled
is_service_enabled designate || exit 55

# Various functions
# -----------------
function get_domain_id {
    local DOMAIN_NAME=$1
    local DOMAIN_ID=$(designate domain-list | egrep " $DOMAIN_NAME " | get_field 1)
    die_if_not_set $LINENO DOMAIN_ID "Failure retrieving DOMAIN_ID"
    echo "$DOMAIN_ID"
}

function get_record_id {
    local DOMAIN_ID=$1
    local RECORD_NAME=$2
    local RECORD_TYPE=$3
    local RECORD_ID=$(designate record-list $DOMAIN_ID | egrep " $RECORD_NAME " | egrep " $RECORD_TYPE " | get_field 1)
    die_if_not_set $LINENO RECORD_ID "Failure retrieving RECORD_ID"
    echo "$RECORD_ID"
}

# Testing Domains
# ===============

# List domains
designate domain-list

# Create random domain name
DOMAIN_NAME="exercise-$(openssl rand -hex 4).com."

# Create the domain
designate domain-create --name $DOMAIN_NAME --email devstack@example.org
DOMAIN_ID=$(get_domain_id $DOMAIN_NAME)

# Fetch the domain
designate domain-get $DOMAIN_ID

# List the nameservers hosting the domain
designate domain-servers-list $DOMAIN_ID

# Testing Records
# ===============

# Create random record name
A_RECORD_NAME="$(openssl rand -hex 4).${DOMAIN_NAME}"

# Create an A record
designate record-create $DOMAIN_ID --name $A_RECORD_NAME --type A --data 127.0.0.1
A_RECORD_ID=$(get_record_id $DOMAIN_ID $A_RECORD_NAME A)

# Fetch the record
designate record-get $DOMAIN_ID $A_RECORD_ID

# -----

# Create random record name
AAAA_RECORD_NAME="$(openssl rand -hex 4).${DOMAIN_NAME}"

# Create an AAAA record
designate record-create $DOMAIN_ID --name $AAAA_RECORD_NAME --type AAAA --data "2607:f0d0:1002:51::4"
AAAA_RECORD_ID=$(get_record_id $DOMAIN_ID $AAAA_RECORD_NAME AAAA)

# Fetch the record
designate record-get $DOMAIN_ID $AAAA_RECORD_ID

# -----

# Create a MX record
designate record-create $DOMAIN_ID --name $DOMAIN_NAME --type MX --priority 5 --data "mail.example.com."
MX_RECORD_ID=$(get_record_id $DOMAIN_ID $DOMAIN_NAME MX)

# Fetch the record
designate record-get $DOMAIN_ID $MX_RECORD_ID

# -----

# Create a SRV record
designate record-create $DOMAIN_ID --name _sip._tcp.$DOMAIN_NAME --type SRV --priority 10 --data "5 5060 sip.example.com."
SRV_RECORD_ID=$(get_record_id $DOMAIN_ID _sip._tcp.$DOMAIN_NAME SRV)

# Fetch the record
designate record-get $DOMAIN_ID $SRV_RECORD_ID

# -----

# Create random record name
CNAME_RECORD_NAME="$(openssl rand -hex 4).${DOMAIN_NAME}"

# Create a CNAME record
designate record-create $DOMAIN_ID --name $CNAME_RECORD_NAME --type CNAME --data $DOMAIN_NAME
CNAME_RECORD_ID=$(get_record_id $DOMAIN_ID $CNAME_RECORD_NAME CNAME)

# Fetch the record
designate record-get $DOMAIN_ID $CNAME_RECORD_ID

# -----

# List Records
designate record-list $DOMAIN_ID

# -----

# Delete a Record
designate record-delete $DOMAIN_ID $CNAME_RECORD_ID

# List Records
designate record-list $DOMAIN_ID

set +o xtrace
echo "*********************************************************************"
echo "SUCCESS: End DevStack Exercise: $0"
echo "*********************************************************************"
