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


# Keep track of the current directory
EXERCISE_DIR=$(cd $(dirname "$0") && pwd)
TOP_DIR=$(cd $EXERCISE_DIR/..; pwd)

# Import common functions
source $TOP_DIR/functions

# Import configuration
source $TOP_DIR/openrc admin admin

# Import exercise configuration
source $TOP_DIR/exerciserc

# Skip if designate is not enabled
is_service_enabled designate || exit 55

# Skip if the DynECT or Akamai backend is in use
[ "$DESIGNATE_BACKEND_DRIVER" != "dynect" ] || exit 55
[ "$DESIGNATE_BACKEND_DRIVER" != "akamai" ] || exit 55

# Import designate library
source $TOP_DIR/lib/designate

# Settings
# ========

# used with dig to look up in DNS
DIG_TIMEOUT=30

# used with dig to look up in DNS
DIG_FLAGS="-p $DESIGNATE_SERVICE_PORT_DNS @$DESIGNATE_SERVICE_HOST"

# used with dig to do an AXFR against MDNS
DIG_AXFR_FLAGS="-p $DESIGNATE_SERVICE_PORT_MDNS @$DESIGNATE_SERVICE_HOST AXFR +tcp +nocmd"

# NUMBER_OF_RECORDS keeps track of the records we need to get for AXFR
# We start with 1 to account for the additional SOA at the end
NUMBER_OF_RECORDS=1

# Functions
# =========

function ensure_record_present {
    local record_name=$1
    local record_type=$2
    local record_value=$3

    if [ "$DESIGNATE_BACKEND_DRIVER" = "fake" ] ; then
        # if the backend is fake, there will be no actual DNS records
        return 0
    fi

    if ! timeout $DIG_TIMEOUT sh -c "while ! dig +short $DIG_FLAGS $record_name $record_type | grep \"$record_value\"; do sleep 1; done"; then
        die $LINENO "Error: record $record_name ($record_type) not found in DNS"
    fi

    # Display for debugging
    dig $DIG_FLAGS $record_name $record_type

    return 0
}

function ensure_record_absent {
    local record_name=$1
    local record_type=$2
    local record_value=$3

    if [ "$DESIGNATE_BACKEND_DRIVER" = "fake" ] ; then
        # if the backend is fake, there will be no actual DNS records
        return 0
    fi

    if ! timeout $DIG_TIMEOUT sh -c "while dig +short $DIG_FLAGS $record_name $record_type | grep \"$record_value\"; do sleep 1; done"; then
        # Display for debugging
        dig $DIG_FLAGS $record_name $record_type

        die $LINENO "Error: record $record_name ($record_type) found in DNS, should be absent"
    fi

    return 0
}

# do an AXFR request to MDNS
# if it does not match the expected value, give an error
function verify_axfr_in_mdns {
    # Display for debugging
    dig $DIG_AXFR_FLAGS "$1"
    if dig $DIG_AXFR_FLAGS "$1"; then
        if [ -n "$2" ] ; then
            local axfr_records=$(dig $DIG_AXFR_FLAGS "$1" | grep "$1" | wc -l)
            if [ "$axfr_records" = "$2" ] ; then
                return 0
            else
                die $LINENO "Error: AXFR to MDNS did not return the expected number of records"
            fi
        fi
        return 0
    else
        die $LINENO "Error: AXFR to MDNS did not return a correct response"
    fi
}

# get the domain id (uuid) given the domain name
# if REQUIRED is set, die with an error if name not found
function get_domain_id {
    local domain_name=$1
    local required=$2
    local domain_id=$(designate domain-list | egrep " $domain_name " | get_field 1)
    if [ "$required" = "1" ] ; then
        die_if_not_set $LINENO domain_id "Failure retrieving DOMAIN_ID"
    fi
    echo "$domain_id"
}


# get the domain_name given the id
function get_domain_name {
    designate domain-list | grep "$1" | get_field 2
}

# if the given domain does not exist, it will be created
# the domain_id of the domain will be returned
function get_or_create_domain_id {
    local domainid=$(get_domain_id "$1")
    if [[ -z "$domainid" ]]; then
        designate domain-create --name $1 --email admin@devstack.org --ttl 86400 --description "domain $1" 1>&2
        domainid=$(designate domain-list | grep "$1" | get_field 1)
    fi
    echo $domainid
}

# get the record id (uuid) given the record name and domain id
# if REQUIRED is set, die with an error if name not found
function get_record_id {
    local domain_id=$1
    local record_name=$2
    local record_type=$3
    local required=$4
    local record_id=$(designate record-list $domain_id | egrep " $record_name " | egrep " $record_type " | get_field 1)
    if [ "$required" = "1" ] ; then
        die_if_not_set $LINENO record_id "Failure retrieving RECORD_ID"
    fi
    echo "$record_id"
}

# Testing Servers
# ===============
designate server-list

# Testing Domains
# ===============

# List domains
designate domain-list

# Create random domain name
DOMAIN_NAME="exercise-$(openssl rand -hex 4).com."

# Create the domain
designate domain-create --name $DOMAIN_NAME --email devstack@example.org
((NUMBER_OF_RECORDS+=2))

# should have SOA and NS records
ensure_record_present $DOMAIN_NAME SOA $DESIGNATE_DEFAULT_NS_RECORD
ensure_record_present $DOMAIN_NAME NS $DESIGNATE_DEFAULT_NS_RECORD

DOMAIN_ID=$(get_domain_id $DOMAIN_NAME 1)

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
((NUMBER_OF_RECORDS++))
A_RECORD_ID=$(get_record_id $DOMAIN_ID $A_RECORD_NAME A)

# Fetch the record
designate record-get $DOMAIN_ID $A_RECORD_ID

# Verify the record is published in DNS
ensure_record_present $A_RECORD_NAME A 127.0.0.1

# -----

# Create random record name
AAAA_RECORD_NAME="$(openssl rand -hex 4).${DOMAIN_NAME}"

# Create an AAAA record
designate record-create $DOMAIN_ID --name $AAAA_RECORD_NAME --type AAAA --data "2607:f0d0:1002:51::4"
((NUMBER_OF_RECORDS++))
AAAA_RECORD_ID=$(get_record_id $DOMAIN_ID $AAAA_RECORD_NAME AAAA)

# Fetch the record
designate record-get $DOMAIN_ID $AAAA_RECORD_ID

# Verify the record is published in DNS
ensure_record_present $AAAA_RECORD_NAME AAAA 2607:f0d0:1002:51::4

# -----

# Create a MX record
designate record-create $DOMAIN_ID --name $DOMAIN_NAME --type MX --priority 5 --data "mail.example.com."
((NUMBER_OF_RECORDS++))
MX_RECORD_ID=$(get_record_id $DOMAIN_ID $DOMAIN_NAME MX)

# Fetch the record
designate record-get $DOMAIN_ID $MX_RECORD_ID

# Verify the record is published in DNS
ensure_record_present $DOMAIN_NAME MX "5 mail.example.com."

# -----

# Create a SRV record
designate record-create $DOMAIN_ID --name _sip._tcp.$DOMAIN_NAME --type SRV --priority 10 --data "5 5060 sip.example.com."
((NUMBER_OF_RECORDS++))
SRV_RECORD_ID=$(get_record_id $DOMAIN_ID _sip._tcp.$DOMAIN_NAME SRV)

# Fetch the record
designate record-get $DOMAIN_ID $SRV_RECORD_ID

# Verify the record is published in DNS
ensure_record_present _sip._tcp.$DOMAIN_NAME SRV "10 5 5060 sip.example.com."

# -----

# Create random record name
CNAME_RECORD_NAME="$(openssl rand -hex 4).${DOMAIN_NAME}"

# Create a CNAME record
designate record-create $DOMAIN_ID --name $CNAME_RECORD_NAME --type CNAME --data $DOMAIN_NAME
((NUMBER_OF_RECORDS++))
CNAME_RECORD_ID=$(get_record_id $DOMAIN_ID $CNAME_RECORD_NAME CNAME)

# Fetch the record
designate record-get $DOMAIN_ID $CNAME_RECORD_ID

# Verify the record is published in DNS
ensure_record_present $CNAME_RECORD_NAME CNAME $DOMAIN_NAME

# -----

# List Records
designate record-list $DOMAIN_ID

# Send an AXFR to MDNS and check for the records returned
verify_axfr_in_mdns $DOMAIN_NAME $NUMBER_OF_RECORDS

# -----

# Delete a Record
designate record-delete $DOMAIN_ID $CNAME_RECORD_ID

# List Records
designate record-list $DOMAIN_ID

# Fetch the record - should be gone
designate record-get $DOMAIN_ID $CNAME_RECORD_ID || echo "good - record was removed"

# verify not in DNS anymore
ensure_record_absent $CNAME_RECORD_NAME CNAME $DOMAIN_NAME

# Testing Domains Delete
# ======================

# Delete the domain
designate domain-delete $DOMAIN_ID

# Fetch the domain - should be gone
designate domain-get $DOMAIN_ID || echo "good - domain was removed"

# should not have SOA and NS records
ensure_record_absent $DOMAIN_NAME SOA $DESIGNATE_DEFAULT_NS_RECORD
ensure_record_absent $DOMAIN_NAME NS $DESIGNATE_DEFAULT_NS_RECORD

set +o xtrace
echo "*********************************************************************"
echo "SUCCESS: End DevStack Exercise: $0"
echo "*********************************************************************"

