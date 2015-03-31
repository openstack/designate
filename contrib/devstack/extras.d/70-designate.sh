# check for service enabled
if is_service_enabled designate; then

    if [[ "$1" == "source" ]]; then
        # Initial source of lib script
        source $TOP_DIR/lib/designate
    fi

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Designate"
        install_designate

        echo_summary "Installing Designate Client"
        install_designateclient

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Designate"
        configure_designate

        if is_service_enabled key; then
            echo_summary "Creating Designate Keystone Accounts"
            create_designate_accounts
        fi

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing Designate"
        init_designate

        echo_summary "Starting Designate"
        start_designate

        echo_summary "Creating Pool NS Records"
        create_designate_ns_records
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_designate
    fi

    if [[ "$1" == "clean" ]]; then
        echo_summary "Cleaning Designate"
        cleanup_designate
    fi
fi
