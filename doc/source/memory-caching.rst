
.. _memory-caching-details:

==============
Memory caching
==============

This page documents how memory caching is used in Designate.

Pool Manager can leverage a memory caching service to speed up its operations and significantly reduce traffic to the DNS resolvers.

Upon zone creation, update and deletion, Pool Manager polls the resolvers through MiniDNS to check if the zone is present or absent and get the zone serial.
When using Memcache, this information is cached for 1 hour (see expiration time).

The cache is not involved in sending NOTIFY/AXFR/IXFR traffic.

The available cache drivers are Memcached, Sqlalchemy or Noop. Set `cache_driver` to 'memcache', 'sqlalchemy' or 'noop' accordingly.

Configuration
=============

The following block in /etc/designate/designate.conf is used to configure the caching system used by Pool Manager:

.. code-block:: ini

    #-----------------------
    # Pool Manager Service
    #-----------------------
    [service:pool_manager]
    <omitted lines>
    # The cache driver to use
    #cache_driver = memcache

    #-----------------------
    # Memcache Pool Manager Cache
    #-----------------------
    [pool_manager_cache:memcache]
    #memcached_servers = None
    #expiration = 3600

.. note:: By configuring cache_driver = memcache (default configuration) and setting memcached_servers to None, Designate will use a simple, local cache.

   Setting cache_driver to 'noop' will disable caching completely. This is not recommended.

It is recommended to run a Memcached instance for any deployment scenarios running large zones receiving frequent updates.

Deployment, monitoring and troubleshooting
==========================================

The contents of Memcached can be flushed at runtime without impacting Designate. The only effect is a temporary loss of performance while the cache is being rebuilt.

Useful metrics that can be monitored are: to-and-from Memcached traffic, concurrent connections, size of the cache, cache hit ratio, key age (expiration time)

To get a simple status snapshot:

.. code-block:: console

    echo stats | nc <memcached_ip_address> <memcached_port>

When Pool Manager logging verbosity is set to DEBUG, the following log messages will be generated::

    Cache hit! Retrieved status ... and serial ... for zone ... on nameserver ... with action ... from the cache.
    Cache miss! Did not retrieve status and serial for zone ... on nameserver ... with action ... from the cache. Getting it from the server.

