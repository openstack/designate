..
    Copyright 2012 Endre Karlson for Bouvet ASA
    Copyright 2012 New Dream Network, LLC (DreamHost)

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

.. |br| raw:: html

   <br />

.. _configuration:

=======================
 Configuration Options
=======================

Designate specific
==================

===============================  ====================================  ==============================================================
Parameter                        Default                               Note
===============================  ====================================  ==============================================================
api_host                         0.0.0.0                               API listen host
api_port                         0.0.0.0                               API listen port
control_exchange                 designate                               The MQ Control exchange
agent_topic                      agent                                 The topic that the Agent(s) should use
central_topic                    central                               The topic that the Central should use
os-username                      glance                                Username to use for openstack service access
os-password                      admin                                 Password to use for openstack service access
os-tenant-id                                                           Tenant ID to use for openstack service access
os-tenant-name                   admin                                 Tenant name to use for openstack service access
os-auth-url                      http://localhost:5000/v2.0            Auth URL to use for openstack service access
database_connection              sqlite:///$pystatepath/designate.db     Database connection string
===============================  ====================================  ==============================================================

Storage - SQL Alchemy
=====================

==========================  ====================================  ==============================================================
Parameter                   Default                               Note
==========================  ====================================  ==============================================================
connection_debug            0                                     Verbosity of SQL debugging information. 0=None, 100=Everything
connection_trace            False                                 Add python stack traces to SQL as comment strings
idle_timeout                3600                                  timeout before idle sql connections are reaped
max_retries                 10                                    maximum db connection retries during startup.
                                                                  (setting -1 implies an infinite retry count)
retry_interval              10                                    interval between retries of opening a sql connection
mysql_engine                InnoDB                                MySQL engine to use
sqlite_synchronous          True                                  If passed, use synchronous mode for sqlite
==========================  ====================================  ==============================================================


Backend - General
=================

===========================  ====================================  ==============================================================
Parameter                    Default                               Note
===========================  ====================================  ==============================================================
some_opt                     Insert something                      Insert something
===========================  ====================================  ==============================================================


Backend - Bind9
=================

===========================  ====================================  ==============================================================
Parameter                    Default                               Note
===========================  ====================================  ==============================================================
rndc_path                    /usr/sbin/rndc                        RNDC Path
rndc_host                    127.0.0.1                             RNDC Host
rndc_port                    953                                   RNDC Port
rndc_config-file             None                                  RNDC Config File
rndc_key-file                None                                  RNDC Key File
===========================  ====================================  ==============================================================


Handler - General
=================

===========================  ====================================  ==============================================================
Parameter                    Default                               Note
===========================  ====================================  ==============================================================
domain_id                    None                                  The domain ID to use
===========================  ====================================  ==============================================================

.. _handler-nova:

Handler - Nova *
================

===========================  ====================================  ==============================================================
Parameter                    Default                               Note
===========================  ====================================  ==============================================================
notification_topics          monitor                               Notification Topics
control_exchange             nova                                  Nova Control Exchange
domain_id                    None                                  UUID of a domain/zone where records are to be created/deleted
format                       None                                  you can use any field in the notification message,
                                                                   compute.instance.create.end, eg: |br|
                                                                   format = '%(octet0)s-%(octet1)s-%(octet2)s-%(octet3)s.%(domain)s' |br|
                                                                   format = '%(display_name)s.%(domain)s'
===========================  ====================================  ==============================================================


General options
===============

The following is the list of openstack-common options that we use:

===========================  ====================================  ==============================================================
Parameter                    Default                               Note
===========================  ====================================  ==============================================================
default_notification_level   INFO                                  Default notification level for outgoing notifications
default_publisher_id         $host                                 Default publisher_id for outgoing notifications
bind_host                    0.0.0.0                               IP address to listen on
bind_port                    9001                                  Port numver to listen on
port                         5672                                  Rabbit MQ port to liste on
fake_rabbit                  False                                 If passed, use a fake RabbitMQ provider
publish_errors               False                                 publish error events
use_stderr                   True                                  Log output to standard error
logfile_mode                 0644                                  Default file mode used when creating log files
logdir                                                             Log output to a per-service log file in named directory
logfile                                                            Log output to a named file
default_log_levels           ['amqplib=WARN',sqlalchemy=WARN,...]  Default log level per components
notification_topics          ['notifications', ]                   AMQP topic used for openstack notifications
enabled_apis                 ['ec2', 'osapi_compute']              List of APIs to enable by default
verbose                      False                                 Print more verbose output
debug                        False                                 Print debugging output
state_path                   currentdir                            Top-level directory for maintaining nova state
sqlite_db                    nova.sqlite                           file name for sqlite
matchmaker_ringfile          /etc/designate/matchmaker_ring.json        Matchmaker ring file (JSON)
rpc_zmq_bind_address         '*'                                   ZeroMQ bind address
rpc_zmq_matchmaker           designate.openstack.common.rpc.         MatchMaker drivers
                             matchmaker.MatchMakerLocalhost
rpc_zmq_port                 9501                                  ZeroMQ receiver listening port
rpc_zmq_port_pub             9502                                  ZeroMQ fanout publisher port
rpc_zmq_contexts             1                                     Number of ZeroMQ contexts
rpc_zmq_ipc_dir              /var/run/openstack                    Directory for holding IPC sockets
rabbit_port                  5672                                  The RabbitMQ broker port where a single node is used
rabbit_host                  localhost                             The RabbitMQ broker address where a single node is used
rabbit_hosts                 ['$rabbit_host:$rabbit_port']         The list of rabbit hosts to listen to
rabbit_userid                guest                                 the RabbitMQ userid
rabbit_password              guest                                 the RabbitMQ password
rabbit_virtual_host          /                                     the RabbitMQ virtual host
rabbit_retry_interval        1                                     how frequently to retry connecting with RabbitMQ
rabbit_retry_backoff         2                                     how long to backoff for between retries when connecting
rabbit_max_retries           0                                     maximum retries with trying to connect to RabbitMQ
                                                                   (the default of 0 implies an infinite retry count)
rabbit_durable_queues        False                                 use durable queues in RabbitMQ
rabbit_use_ssl               False                                 connect over SSL for RabbitMQ
rabbit_durable_queues        False                                 use durable queues in RabbitMQ
rabbit_ha_queues             False                                 use H/A queues in RabbitMQ (x-ha-policy: all).
kombu_ssl_version                                                  SSL version to use (valid only if SSL enabled)
kombu_ssl_keyfile                                                  SSL key file (valid only if SSL enabled)
kombu_ssl_certfile                                                 SSL cert file (valid only if SSL enabled)
kombu_ssl_ca_certs                                                 SSL certification authority file
qpid_hostname                localhost                             Qpid broker hostname
qpid_port                    5672                                  Qpid broker port
qpid_username                                                      Username for qpid connection
qpid_password                                                      Password for qpid connection
qpid_sasl_mechanisms                                               Space separated list of SASL mechanisms to use for auth
qpid_reconnect_timeout       0                                     Reconnection timeout in seconds
qpid_reconnect_limit         0                                     Max reconnections before giving up
qpid_reconnect_interval_min  0                                     Minimum seconds between reconnection attempts
qpid_reconnect_interval_max  0                                     Maximum seconds between reconnection attempts
qpid_reconnect_interval      0                                     Equivalent to setting max and min to the same value
qpid_heartbeat               60                                    Seconds between connection keepalive heartbeats
qpid_protocol                tcp                                   Transport to use, either 'tcp' or 'ssl'
qpid_reconnect               True                                  Automatically reconnect
qpid_tcp_nodelay             True                                  Disable Nagle algorithm
rpc_backend                  kombu                                 The messaging module to use, defaults to kombu.
rpc_thread_pool_size         64                                    Size of RPC thread pool
rpc_conn_pool_size           30                                    Size of RPC connection pool
rpc_response_timeout         60                                    Seconds to wait for a response from call or multicall
rpc_cast_timeout             30                                    Seconds to wait before a cast expires (TTL).
                                                                   Only supported by impl_zmq.
===========================  ====================================  ==============================================================
