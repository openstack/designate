#!/bin/bash

set -o errexit

source $GRENADE_DIR/grenaderc
source $GRENADE_DIR/functions

source $TOP_DIR/openrc admin admin

set -o xtrace

DESIGNATE_PROJECT=designate_grenade
DESIGNATE_USER=designate_grenade
DESIGNATE_PASS=designate_grenade
DESIGNATE_ZONE_NAME=example.com.
DESIGNATE_ZONE_EMAIL=hostmaster@example.com
DESIGNATE_RRSET_NAME=www.example.com.
DESIGNATE_RRSET_TYPE=A
DESIGNATE_RRSET_RECORD=10.0.0.1

function _set_designate_user {
    OS_TENANT_NAME=$DESIGNATE_PROJECT
    OS_PROJECT_NAME=$DESIGNATE_PROJECT
    OS_USERNAME=$DESIGNATE_USER
    OS_PASSWORD=$DESIGNATE_PASS
}


function create {

    # create a tenant for the server
    eval $(openstack project create -f shell -c id $DESIGNATE_PROJECT)
    if [[ -z "$id" ]]; then
        die $LINENO "Didn't create $DESIGNATE_PROJECT project"
    fi
    resource_save designate project_id $id

    # create the user, and set $id locally
    eval $(openstack user create $DESIGNATE_USER \
        --project $id \
        --password $DESIGNATE_PASS \
        -f shell -c id)
    if [[ -z "$id" ]]; then
        die $LINENO "Didn't create $DESIGNATE_USER user"
    fi
    resource_save designate user_id $id

    _set_designate_user

    # Create a zone, and save the id

    eval $(openstack zone create --email $DESIGNATE_ZONE_EMAIL \
        $DESIGNATE_ZONE_NAME \
        -f shell -c id)


    resource_save designate zone_id $id

    eval $(openstack recordset create --records $DESIGNATE_RRSET_RECORD \
        --type $DESIGNATE_RRSET_TYPE \
        $DESIGNATE_ZONE_NAME \
        $DESIGNATE_RRSET_NAME \
        -f shell -c id)

    resource_save designate rrset_id $id

    # wait until rrset moves to active state
    local timeleft=1000
    while [[ $timeleft -gt 0 ]]; do
        local status
        eval $(openstack recordset show $DESIGNATE_ZONE_NAME \
            $DESIGNATE_RRSET_NAME \
            -f shell -c status)

        if [[ "$status" != "ACTIVE" ]]; then
            if [[ "$cluster_state" == "Error" ]]; then
                die $LINENO "Zone is in Error state"
            fi
            echo "Zone is still not in Active state"
            sleep 10
            timeleft=$((timeleft - 10))
            if [[ $timeleft == 0 ]]; then
                die $LINENO "Zone hasn't moved to Active state \
                                                        during 1000 seconds"
            fi
        else
            break
        fi
    done

}

function verify {
    _set_designate_user
    # check that cluster is in Active state
    local zone_id
    zone_id=$(resource_get designate zone_id)

    local rrset_id
    rrset_id=$(resource_get designate rrset_id)

    eval $(openstack zone show $zone_id -f shell -c status)
    echo -n $status
    if [[ "$status" != "ACTIVE" ]]; then
        die $LINENO "Zone is not in Active state anymore"
    fi

    eval $(openstack recordset show $zone_id $rrset_id -f shell -c status)
    echo -n $status
    if [[ "$status" != "ACTIVE" ]]; then
        die $LINENO "Recordset is not in Active state anymore"
    fi

    echo "Designate verification: SUCCESS"
}

function verify_noapi {
    :
}

function destroy {
    _set_designate_user
    set +o errexit

    # delete cluster
    local cluster_id
    zone_id=$(resource_get designate zone_id)
    openstack zone delete $zone_id > /dev/null
    # wait for cluster deletion
    local timeleft=500
    while [[ $timeleft -gt 0 ]]; do
        openstack zone show $zone_id > /dev/null
        local rc=$?

        if [[ "$rc" != 1 ]]; then
            echo "Zone still exists"
            sleep 5
            timeleft=$((timeleft - 5))
            if [[ $timeleft == 0 ]]; then
                die $LINENO "Zone hasn't been deleted during 500 seconds"
            fi
        else
            break
        fi
    done
}

# Dispatcher
case $1 in
    "create")
        create
        ;;
    "verify_noapi")
        verify_noapi
        ;;
    "verify")
        verify
        ;;
    "destroy")
        destroy
        ;;
    "force_destroy")
        set +o errexit
        destroy
        ;;
esac
