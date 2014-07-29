Designate API Testing using Tempest Framework.
==============================================

This is a set of Designate API tests written for Tempest Framework
to be run against a live OpenStack cluster with Designate service
enabled.

Configuration
-------------

Detailed configuration of Designate tests and configuration files is
the scope of this document.

Added all the required parameters in etc/tempest.conf.sample
to enable Designate service.

The sample config file is auto generated using the script
(based on parameters added in config.py):
tools/generate_sample.sh

To run Tempest, you first need to create a configuration file that will
tell Tempest where to find the designate service.

The easiest way to create a configuration file is to copy the sample
(tempest.conf.sample) one in the etc/ directory.

    $> cd $TEMPEST_ROOT_DIR
    $> cp etc/tempest.conf.sample etc/tempest.conf

After that, open up the etc/tempest.conf file and edit the configuration
variables to match valid data in your environment. This includes your
Keystone endpoint, a valid user and credentials, and reference
data to be used in testing.

Tests and Clients for Designate feature
---------------------------------------

    1> Added tests for Domains, Records, Servers of Designate API
       under dns_tests folder.

    2> Added respective supporting functions for Json Interface
       under dns_clients folder.

    3> Modified respective clients.py and config.py files with respect
       to Designate service and should be placed under'tempest' folder.

    4> Implemented Schema validation for all the Designate operations as per
       current Tempest framework under dns_schema.

Steps to execute Designate API tests.
-------------------------------------

In order to run Designate API tests against Tempest Suite, all the above
test scripts and client files has to be placed in paths as mentioned below.

    1> Clone Tempest
       git clone https://github.com/openstack/tempest.git

    2> Add the following files
        $> cp tempest.conf.sample $TEMPEST_ROOT_DIR/tempest/etc
        $> cp config.py TEMPEST_ROOT_DIR/tempest
        $> cp clients.py TEMPEST_ROOT_DIR/tempest
        $> cp -r dns_clients TEMPEST_ROOT_DIR/tempest/services/dns
        $> cp -r dns_schema TEMPEST_ROOT_DIR/tempest/api_schema/dns
        $> cp -r dns_tests TEMPEST_ROOT_DIR/tempest/api/dns

After setting up your configuration files, you can execute the set of
designate tests by using testr.
    $> testr run --parallel

To run one single test
    $> testr run --parallel tempest.api.dns.test_domains.DnsDomainsTest.test_list_domains
