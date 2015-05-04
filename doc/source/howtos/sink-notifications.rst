..
    Copyright 2015 Christopher Liles

    Author: Christophes Liles <christopherliles@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>

How To Setup Sink Notifications
===============================

.. note::
   In this how to, we assume you have the Designate installed and configured. If you can not manually add records via the API or dashboard,
   stop reading now, and go follow some of the other documentation to get that working first.

   This example will go over setting up the nova handler only.

   The most basic use case for this example is that you want all instances to be automatically assigned an A record when an instance boots,
   and you would also like that A record to be removed when the instance is terminated.

Setup Nova notifications
------------------------

On all nova compute nodes make changes to nova.conf to include at a minimum, the following:

.. code-block:: bash

    notification_driver=nova.openstack.common.notifier.rpc_notifier
    notification_topics=notifications,designate_sink
    notify_on_state_change=vm_and_task_state
    default_notification_level=INFO

This will setup the notifications and the send them to a new topic. This is critical to add as using the default topic will also be used for ceilometer, which will consume the notification prior to sink receiving it.

Setup Sink nova_handler
-----------------------

On all sink nodes, make changes to designate.conf

.. code-block:: bash

    [service:sink]
    enabled_notification_handlers = nova_fixed
    [handler:nova_fixed]
    # Domain ID of domain to create records in. Should be pre-created
    domain_id = <insert-domain-id-here>
    notification_topics = designate_sink
    control_exchange = 'nova'
    #format = '%(octet0)s-%(octet1)s-%(octet2)s-%(octet3)s.%(domain)s'
    format = '%(instance_name)s.%(domain)s'

This will setup the sink to consume from the new topic we created specifically for designate-sink. There are two choices for the format of the A record.
