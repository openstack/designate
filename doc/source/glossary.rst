..
    Copyright 2012 Endre Karlson for Bouvet ASA

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.

============
Glossary
============

.. glossary::

   agent
     The Agent would be a standalone service that acts as a sort of mirror to
     mdns. It would receive AXFR/IXFR, NOTIFYs, and other notifications and
     perform changes to a DNS server through a plugin-style backend.  The agent
     is intended for deployments that may not be able to use mdns as a true DNS
     Master.

   api
     HTTP REST API service for Designate

   central
     Software service running on a central management node that stores
     information persistently in a backend storage using a configurable driver
     like SQLAlchemy or other.

   mdns
     Also known as mini dns. This is a dns server with limited capabilities like
     NOTIFY's, AXFR's and record queries. The pool manager uses mdns to transfer
     data to/from the pool servers.

   mq
     A message queue, typically something like RabbitMQ or ZeroMQ

   name server
     A FQDN (or IP, but usually a FQDN) that is used to populate the NS Records
     of a Designate Managed Zone. Each Pool will have a set of Name Servers,
     which users then delegate to from their registrar.

   node
     A server, physical or virtual, running some aspect of the designate system.

   pool
     A collection of pool servers sharing similar attributes. Different pools
     could have different capabilities - such as GeoIP / Round Robin DNS / Anycast.

   pool manager
     This is a service that is responsible for notifying pool servers of the
     changes that have occurred. It also updates central once the changes are
     live on the pool servers.

   pool manager backend
     A backend is used by the pool manager to transfer the data from storage to
     name servers.  There are backends that support PowerDNS, BIND, & NSD.

   pool server
     The DNS servers that are updated by the pool manager. These need not be the
     same as the name servers. When they are different a mechanism outside of designate
     is needed to ensure the data on pool servers is consistent with that on the
     name servers.

   private pool
     A pool of ‘private’ DNS servers. These servers would typically allow non
     standard TLDs (.dev , .local etc), and may not have the same level of
     blacklist restrictions. They would be aimed at people with Neutron Networking,
     and VPC style set ups, where access to the DNS server would come from trusted
     networks (E.G. in-cloud - owned instances, and onsite resources connect by VPN)

     This would allow customers to set DNS entries for internal servers, on domains
     that would not be available on the public pools, and have them accessible
     by internal users

   secondary zone
     A zone within Designate that has external Masters.

   sink
     Optional Software Service that is configured to listen to events from the Nova
     or Neutron event queue and use the central service to generate simple A records
     for instances as they are created, and delete A records as they are deleted.

   storage
     A backend for storing data/information persistently. Typically MongoDB or
     a SQL based server software.
