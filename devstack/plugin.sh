# Install and start **Designate** service in Devstack

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace

LIBDIR=$DEST/designate/devstack/lib

source $LIBDIR/wsgi

# Get backend configuration
# -------------------------
if is_service_enabled designate && [[ -r $DESIGNATE_PLUGINS/backend-$DESIGNATE_BACKEND_DRIVER ]]; then
    # Load plugin
    source $DESIGNATE_PLUGINS/backend-$DESIGNATE_BACKEND_DRIVER
fi

# DevStack Plugin
# ---------------

# cleanup_designate - Remove residual data files, anything left over from previous
# runs that a clean run would need to clean up
function cleanup_designate {
    sudo rm -rf $DESIGNATE_STATE_PATH
    sudo rm -f $(apache_site_config_for designate-api)
    remove_uwsgi_config "$DESIGNATE_UWSGI_CONF" "$DESIGNATE_UWSGI"
    cleanup_designate_backend
}

# configure_designate - Set config files, create data dirs, etc
function configure_designate {
    local rootwrap_sudoer_cmd
    local tempfile

    [ ! -d $DESIGNATE_CONF_DIR ] && sudo mkdir -m 755 -p $DESIGNATE_CONF_DIR
    sudo chown $STACK_USER $DESIGNATE_CONF_DIR

    [ ! -d $DESIGNATE_LOG_DIR ] &&  sudo mkdir -m 755 -p $DESIGNATE_LOG_DIR
    sudo chown $STACK_USER $DESIGNATE_LOG_DIR

    # (Re)create ``designate.conf``
    rm -f $DESIGNATE_CONF

    # General Configuration
    iniset_rpc_backend designate $DESIGNATE_CONF DEFAULT

    iniset $DESIGNATE_CONF DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL
    iniset $DESIGNATE_CONF DEFAULT state_path $DESIGNATE_STATE_PATH
    iniset $DESIGNATE_CONF DEFAULT root-helper sudo designate-rootwrap $DESIGNATE_ROOTWRAP_CONF
    iniset $DESIGNATE_CONF storage:sqlalchemy connection `database_connection_url designate`

    # Quota Configuration
    iniset $DESIGNATE_CONF DEFAULT quota_zones $DESIGNATE_QUOTA_ZONES
    iniset $DESIGNATE_CONF DEFAULT quota_zone_recordsets $DESIGNATE_QUOTA_ZONE_RECORDSETS
    iniset $DESIGNATE_CONF DEFAULT quota_zone_records $DESIGNATE_QUOTA_ZONE_RECORDS
    iniset $DESIGNATE_CONF DEFAULT quota_recordset_records $DESIGNATE_QUOTA_RECORDSET_RECORDS
    iniset $DESIGNATE_CONF DEFAULT quota_api_export_size $DESIGNATE_QUOTA_API_EXPORT_SIZE

    # Coordination Configuration
    if [[ -n "$DESIGNATE_COORDINATION_URL" ]]; then
        iniset $DESIGNATE_CONF coordination backend_url $DESIGNATE_COORDINATION_URL
    fi

    # API Configuration
    sudo cp $DESIGNATE_DIR/etc/designate/api-paste.ini $DESIGNATE_APIPASTE_CONF
    iniset $DESIGNATE_CONF service:api enabled_extensions_v2 $DESIGNATE_ENABLED_EXTENSIONS_V2
    iniset $DESIGNATE_CONF service:api enabled_extensions_admin $DESIGNATE_ENABLED_EXTENSIONS_ADMIN
    iniset $DESIGNATE_CONF service:api enable_host_header True
    iniset $DESIGNATE_CONF service:api enable_api_v2 $DESIGNATE_ENABLE_API_V2
    iniset $DESIGNATE_CONF service:api enable_api_admin $DESIGNATE_ENABLE_API_ADMIN

    # Central Configuration
    iniset $DESIGNATE_CONF service:central workers $API_WORKERS
    if [[ -n "$SCHEDULER_FILTERS" ]]; then
        iniset $DESIGNATE_CONF service:central scheduler_filters $SCHEDULER_FILTERS
    fi

    # mDNS Configuration
    iniset $DESIGNATE_CONF service:mdns listen ${DESIGNATE_SERVICE_HOST}:${DESIGNATE_SERVICE_PORT_MDNS}
    iniset $DESIGNATE_CONF service:mdns workers $API_WORKERS

    # Producer Configuration
    iniset $DESIGNATE_CONF service:producer workers $API_WORKERS

    # Sink Configuration
    iniset $DESIGNATE_CONF service:sink workers $API_WORKERS

    # Worker Configuration
    iniset $DESIGNATE_CONF service:worker poll_max_retries $DESIGNATE_POLL_RETRIES
    iniset $DESIGNATE_CONF service:worker poll_retry_interval $DESIGNATE_POLL_INTERVAL
    iniset $DESIGNATE_CONF service:worker workers $API_WORKERS

    # Set up Notifications/Ceilometer Integration
    iniset $DESIGNATE_CONF oslo_messaging_notifications driver "$DESIGNATE_NOTIFICATION_DRIVER"
    iniset $DESIGNATE_CONF oslo_messaging_notifications topics "$DESIGNATE_NOTIFICATION_TOPICS"

    # Root Wrap
    sudo cp $DESIGNATE_DIR/etc/designate/rootwrap.conf $DESIGNATE_ROOTWRAP_CONF
    iniset $DESIGNATE_ROOTWRAP_CONF DEFAULT filters_path $DESIGNATE_DIR/etc/designate/rootwrap.d root-helper

    # Oslo Concurrency
    iniset $DESIGNATE_CONF oslo_concurrency lock_path "$DESIGNATE_STATE_PATH"

    # Set up the rootwrap sudoers for designate
    rootwrap_sudoer_cmd="$DESIGNATE_BIN_DIR/designate-rootwrap $DESIGNATE_ROOTWRAP_CONF *"
    tempfile=`mktemp`
    echo "$STACK_USER ALL=(root) NOPASSWD: $rootwrap_sudoer_cmd" >$tempfile
    chmod 0440 $tempfile
    sudo chown root:root $tempfile
    sudo mv $tempfile /etc/sudoers.d/designate-rootwrap

    if is_service_enabled tls-proxy; then
        iniset $DESIGNATE_CONF keystone cafile $SSL_BUNDLE_FILE
    fi

    # Setup the Keystone Integration
    if is_service_enabled keystone; then
        iniset $DESIGNATE_CONF service:api auth_strategy keystone
        configure_keystone_authtoken_middleware $DESIGNATE_CONF designate
        iniset $DESIGNATE_CONF keystone region_name $REGION_NAME
        iniset $DESIGNATE_CONF service:api quotas_verify_project_id True
    fi

    # Logging Configuration
    setup_systemd_logging $DESIGNATE_CONF

    # Backend Plugin Configuation
    configure_designate_backend

    if [[ "$DESIGNATE_WSGI_MODE" == "uwsgi" ]]; then
        designate_configure_uwsgi
    else
        designate_configure_mod_wsgi
    fi
}

function configure_designatedashboard {
    # Compile message catalogs
    if [ -d ${DESIGNATEDASHBOARD_DIR}/designatedashboard/locale ]; then
        (cd ${DESIGNATEDASHBOARD_DIR}/designatedashboard; DJANGO_SETTINGS_MODULE=openstack_dashboard.settings $PYTHON ../manage.py compilemessages)
    fi
}

# Configure the needed tempest options
function configure_designate_tempest {
    if is_service_enabled tempest; then
        # Tell tempest we're available
        iniset $TEMPEST_CONFIG service_available designate True

        # Tell tempest which APIs are available
        iniset $TEMPEST_CONFIG dns_feature_enabled api_v2 $DESIGNATE_ENABLE_API_V2
        iniset $TEMPEST_CONFIG dns_feature_enabled api_admin $DESIGNATE_ENABLE_API_ADMIN
        iniset $TEMPEST_CONFIG dns_feature_enabled api_v2_root_recordsets True
        iniset $TEMPEST_CONFIG dns_feature_enabled api_v2_quotas True
        iniset $TEMPEST_CONFIG dns_feature_enabled api_v2_quotas_verify_project True
        iniset $TEMPEST_CONFIG dns_feature_enabled bug_1573141_fixed True
        iniset $TEMPEST_CONFIG dns_feature_enabled bug_1932026_fixed True

        # Tell tempest where are nameservers are.
        nameservers=$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT_DNS
        # TODO(kiall): Remove hardcoded list of plugins
        case $DESIGNATE_BACKEND_DRIVER in
            bind9)
                nameservers="$DESIGNATE_SERVICE_HOST:$DESIGNATE_SERVICE_PORT_DNS"
                ;;
            dynect)
                nameservers="$DESIGNATE_DYNECT_NAMESERVERS"
                ;;
        esac

        if [ ! -z "$DESIGNATE_NAMESERVERS" ]; then
            nameservers=$DESIGNATE_NAMESERVERS
        fi

        iniset $TEMPEST_CONFIG dns nameservers $nameservers

        # For legacy functionaltests
        iniset $TEMPEST_CONFIG designate nameservers $nameservers
    fi
}

# create_designate_accounts - Set up common required designate accounts

# Tenant               User       Roles
# ------------------------------------------------------------------
# service              designate  admin        # if enabled
function create_designate_accounts {
    local designate_api_url

    if is_service_enabled designate-api; then
        create_service_user "designate" "admin"

        designate_api_url="$DESIGNATE_SERVICE_PROTOCOL://$DESIGNATE_SERVICE_HOST/dns"

        get_or_create_service "designate" "dns" "Designate DNS Service"
        get_or_create_endpoint \
            "dns" \
            "$REGION_NAME" \
            "$designate_api_url"
    fi
}

# create_designate_pool_configuration - Create Pool Configuration
function create_designate_pool_configuration {
    # Sync Pools Config
    $DESIGNATE_BIN_DIR/designate-manage pool update --file $DESIGNATE_CONF_DIR/pools.yaml

    # Allow Backends to do backend specific tasks
    if function_exists create_designate_pool_configuration_backend; then
        create_designate_pool_configuration_backend
    fi

    # create the tsigkey for the secondary pool acct., if necessary.
    if [ "$DESIGNATE_BACKEND_DRIVER" == "multipool-bind9" ] && \
    [ -d $BIND2_CFG_DIR ] && [ -f $BIND2_TSIGKEY_FILE ]; then
        # parse the data from the bind-2/named.conf.tsigkeys file,
        # which was created during the init_designate_backend section.
        NAME=`cat $BIND2_TSIGKEY_FILE | grep 'key' | \
            awk '{split($0, a, " "); print a[2];}' | \
            sed -e 's/^"//' -e 's/"$//'| \
            awk '{split($0, a, "{"); print a[1];}'`
        ALGORITHM=`cat $BIND2_TSIGKEY_FILE | grep 'algorithm' | \
            awk '{split($0, a, " "); print a[2];}' | \
            sed -r 's/(.*);/\1/'`
        SECRET=`cat $BIND2_TSIGKEY_FILE | grep 'secret' | \
            awk '{split($0, a, " "); print a[2];}' | \
            sed -r 's/(.*);/\1/' | sed -e 's/^"//' -e 's/"$//'`
        RESOURCE_ID=$(sudo mysql -u root -p$DATABASE_PASSWORD designate -N -e "select id from pools where name = 'secondary_pool';")

        # create the openstack
        openstack tsigkey create --name $NAME --algorithm $ALGORITHM --secret $SECRET --scope POOL --resource-id $RESOURCE_ID
    fi
}

# init_designate - Initialize etc.
function init_designate {
    # (Re)create designate database
    recreate_database designate utf8

    if [[ "$USE_SQLALCHEMY_LATEST" == "True" ]]; then
        pip3 install --upgrade alembic sqlalchemy
    fi
    # Init and migrate designate database
    $DESIGNATE_BIN_DIR/designate-manage database sync

    init_designate_backend
}

# install_designate - Collect source and prepare
function install_designate {
    if [[ "$DESIGNATE_WSGI_MODE" == "uwsgi" ]]; then
        install_apache_uwsgi
    else
        install_apache_wsgi
    fi

    if is_fedora; then
        # bind-utils package provides `dig`
        install_package bind-utils
    fi

    git_clone $DESIGNATE_REPO $DESIGNATE_DIR $DESIGNATE_BRANCH
    setup_develop $DESIGNATE_DIR

    # Install reqs for tooz driver
    if [[ "$DESIGNATE_COORDINATION_URL" =~ "memcached" ]]; then
        pip_install_gr "pymemcache"
    fi

    install_designate_backend
}

# install_designateclient - Collect source and prepare
function install_designateclient {
    if use_library_from_git "python-designateclient"; then
        git_clone_by_name "python-designateclient"
        setup_dev_lib "python-designateclient"
    else
        pip_install_gr "python-designateclient"
    fi
}

# install_designatedashboard - Collect source and prepare
function install_designatedashboard {
    git_clone_by_name "designate-dashboard"
    setup_dev_lib "designate-dashboard"

    for panel in _1710_project_dns_panel_group.py \
            _1721_dns_zones_panel.py \
            _1722_dns_reversedns_panel.py; do
        ln -fs $DESIGNATEDASHBOARD_DIR/designatedashboard/enabled/$panel $HORIZON_DIR/openstack_dashboard/local/enabled/$panel
    done
}

# install_designatetempest - Collect source and prepare
function install_designatetempest {
    git_clone_by_name "designate-tempest-plugin"
    setup_dev_lib "designate-tempest-plugin"
}

# start_designate - Start running processes
function start_designate {
    start_designate_backend

    run_process designate-central "$DESIGNATE_BIN_DIR/designate-central --config-file $DESIGNATE_CONF"
    run_process designate-mdns "$DESIGNATE_BIN_DIR/designate-mdns --config-file $DESIGNATE_CONF"
    run_process designate-sink "$DESIGNATE_BIN_DIR/designate-sink --config-file $DESIGNATE_CONF"

    run_process designate-worker "$DESIGNATE_BIN_DIR/designate-worker --config-file $DESIGNATE_CONF"
    run_process designate-producer "$DESIGNATE_BIN_DIR/designate-producer --config-file $DESIGNATE_CONF"



    if [[ "$DESIGNATE_WSGI_MODE" == "uwsgi" ]]; then
        run_process "designate-api" "$(which uwsgi) --procname-prefix designate-api --ini $DESIGNATE_UWSGI_CONF"
        enable_apache_site designate-api-wsgi
        restart_apache_server
    else
        enable_apache_site designate-api
        restart_apache_server
    fi

    echo "Waiting for designate-api to start..."
    if ! wait_for_service $SERVICE_TIMEOUT $DESIGNATE_SERVICE_PROTOCOL://$DESIGNATE_SERVICE_HOST/dns; then
        die $LINENO "designate-api did not start"
    fi
}

# stop_designate - Stop running processes
function stop_designate {
    if [[ "$DESIGNATE_WSGI_MODE" == "uwsgi" ]]; then
        stop_process "designate-api"
        disable_apache_site designate-api-wsgi
        restart_apache_server
    else
        disable_apache_site designate-api
        restart_apache_server
    fi

    stop_process designate-central
    stop_process designate-mdns
    stop_process designate-sink
    stop_process designate-worker
    stop_process designate-producer

    stop_designate_backend
}

# This is the main for plugin.sh
if is_service_enabled designate; then
    # ------------------------------
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Designate client"
        install_designateclient

        echo_summary "Installing Designate"
        stack_install_service designate

        if is_service_enabled horizon; then
            echo_summary "Installing Designate dashboard"
            install_designatedashboard
        fi

        if is_service_enabled tempest; then
            echo_summary "Installing Designate Tempest Plugin"
            install_designatetempest
        fi

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Designate"
        configure_designate
        if is_service_enabled horizon; then
            echo_summary "Configuring Designate dashboard"
            configure_designatedashboard
        fi

        if is_service_enabled keystone; then
            echo_summary "Creating Designate Keystone accounts"
            create_designate_accounts
        fi

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Designate"
        init_designate

        echo_summary "Starting Designate"
        start_designate

        echo_summary "Creating Pool Configuration"
        create_designate_pool_configuration
    elif [[ "$1" == "stack" && "$2" == "test-config" ]]; then
        echo_summary "Configuring Tempest options for Designate"
        configure_designate_tempest
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_designate
    fi

    if [[ "$1" == "clean" ]]; then
        echo_summary "Cleaning Designate"
        cleanup_designate
    fi
fi

# Restore xtrace
$XTRACE
