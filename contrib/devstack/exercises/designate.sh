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
source $TOP_DIR/openrc admin admin

# Import exercise configuration
source $TOP_DIR/exerciserc

# Skip if designate is not enabled
is_service_enabled designate || exit 55

# Import designate library
source $TOP_DIR/lib/designate

# NUMBER_OF_RECORDS keeps track of the records we need to get for AXFR
# We start with 1 to account for the additional SOA at the end
NUMBER_OF_RECORDS=1

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
verify_name_type_dns $DOMAIN_NAME SOA $DESIGNATE_TEST_NSREC
verify_name_type_dns $DOMAIN_NAME NS $DESIGNATE_TEST_NSREC

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
verify_name_type_dns $A_RECORD_NAME A 127.0.0.1

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
verify_name_type_dns $AAAA_RECORD_NAME AAAA 2607:f0d0:1002:51::4

# -----

# Create a MX record
designate record-create $DOMAIN_ID --name $DOMAIN_NAME --type MX --priority 5 --data "mail.example.com."
((NUMBER_OF_RECORDS++))
MX_RECORD_ID=$(get_record_id $DOMAIN_ID $DOMAIN_NAME MX)

# Fetch the record
designate record-get $DOMAIN_ID $MX_RECORD_ID

# Verify the record is published in DNS
verify_name_type_dns $DOMAIN_NAME MX "5 mail.example.com."

# -----

# Create a SRV record
designate record-create $DOMAIN_ID --name _sip._tcp.$DOMAIN_NAME --type SRV --priority 10 --data "5 5060 sip.example.com."
((NUMBER_OF_RECORDS++))
SRV_RECORD_ID=$(get_record_id $DOMAIN_ID _sip._tcp.$DOMAIN_NAME SRV)

# Fetch the record
designate record-get $DOMAIN_ID $SRV_RECORD_ID

# Verify the record is published in DNS
verify_name_type_dns _sip._tcp.$DOMAIN_NAME SRV "10 5 5060 sip.example.com."

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
verify_name_type_dns $CNAME_RECORD_NAME CNAME $DOMAIN_NAME

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
verify_name_type_dns $CNAME_RECORD_NAME CNAME $DOMAIN_NAME 1

# Testing Domains Delete
# ======================

# Delete the domain
designate domain-delete $DOMAIN_ID

# Fetch the domain - should be gone
designate domain-get $DOMAIN_ID || echo "good - domain was removed"

# should not have SOA and NS records
verify_name_type_dns $DOMAIN_NAME SOA $DESIGNATE_TEST_NSREC 1
verify_name_type_dns $DOMAIN_NAME NS $DESIGNATE_TEST_NSREC 1

set +o xtrace
echo "*********************************************************************"
echo "SUCCESS: End DevStack Exercise: $0"
echo "*********************************************************************"

