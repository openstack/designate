Troubleshooting
===============

I have a broken zone
--------------------

A zone is considered broken when it is not receiving updates anymore.
Its status can be "ERROR" if Designate detected the error condition
or it can be stuck in "PENDING" for a long time.

Review the logs from the API, Central, Producer, Worker and MiniDNS.
Identify the transaction ID of the last successful change and the first
failing change. Using the ID, you can filter logs from the Designate
components that are related to the same transaction.
Look for log messages with ERROR level before and after
the first failing update.

Failures in updating a zone are usually related to problems in Producer,
Worker, MiniDNS or the database.

Ensure the services are running and network connectivity is not impaired.

Transient network issues can be the cause of a broken zone.
Producer and Worker are stateful services and perform attempts at restoring
failing zones over time. Restarting the services will trigger new attempts.


I have a broken pool
--------------------

I deleted a zone but it's still in the database
-----------------------------------------------

Deleted zones are flagged with "status" set to "DELETED" and "task" set to
"NONE" once the deletion process terminates successfully.

What ports should be open?
--------------------------

Port numbers are configurable: review your designate.conf

The default values are:

+------------------------+------------+----------+
| Component              | Protocol   | Port     |
| (header rows optional) |            | numbers  |
+========================+============+==========+
+------------------------+------------+----------+
| API                    | TCP        | 9001     |
+------------------------+------------+----------+
| Keystone (external)    | TCP        | 35357    |
+------------------------+------------+----------+
| MiniDNS                | TCP        | 5354     |
+                        +------------+----------+
|                        | UDP        | 5354     |
+------------------------+------------+----------+
| MySQL                  | TCP        |    3306  |
+------------------------+------------+----------+
| RabbitMQ               | TCP        |    5672  |
+------------------------+------------+----------+
| Resolvers              | TCP        | 53       |
+                        +------------+----------+
|                        | UDP        | 53       |
+------------------------+------------+----------+
| ZooKeeper              | TCP        |    2181  |
+                        +------------+----------+
|                        | TCP        | 2888,3888|
+------------------------+------------+----------+



What network protocol are used?
-------------------------------

HTTP[S] by the API, RabbitMQ and the MySQL protocol by most components,
DNS (resolution and XFR), ZooKeeper, Memcached.

What needs access to the Database?
----------------------------------

Central, MiniDNS

What needs access to RabbitMQ?
------------------------------

The API, Central, Producer, Worker, MiniDNS

What needs access to ZooKeeper?
-------------------------------

Pool and Producer

What needs access to Memcached?
-------------------------------

API and Worker

How do I monitor Designate?
---------------------------

Designate can be monitored by various
`monitoring systems listed here <https://wiki.openstack.org/wiki/Operations/Monitoring>`_

What are useful metrics to monitor?
-----------------------------------

* General host monitoring, i.e. CPU load, memory usage, disk and network I/O
* MySQL performance, errors and free disk space
* Number of zones in ACTIVE, PENDING and ERROR status
* API queries per second, broken down by "read" and "write" operation on zones,
  records, etc
* Zone change propagation time i.e. how long does it takes for a record update
  to reach the resolvers
* Log messages containing having "ERROR" level
* Quotas utilization i.e. number of existing records/zones against the
  maximum allowed
* Memcached, RabbitMQ, ZooKeeper performance and errors


What are useful metrics to review first during an incident?
-----------------------------------------------------------

* Host, network and MySQL performance metrics
* Number of zones in ACTIVE, PENDING and ERROR status
* Log messages containing having "ERROR" level
