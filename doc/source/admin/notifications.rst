.. _notifications:

Notifications
=============

.. HINT::

    In this context, "notifications" are not related to the DNS NOTIFY message.


Notifications are RPC calls that contain a JSON object.
Designate both generates and receives notifications.

The purpose of notifications in to inform unrelated OpenStack components
of events in real time and trigger actions.

Emitters
--------

They are emitted by Central on the following events:

* dns.tld.create
* dns.tld.update
* dns.tld.delete
* dns.tsigkey.create
* dns.tsigkey.update
* dns.tsigkey.delete
* dns.domain.create
* dns.zone.create
* dns.domain.update
* dns.zone.update
* dns.domain.delete
* dns.zone.delete
* dns.zone.touch
* dns.recordset.create
* dns.recordset.update
* dns.recordset.delete
* dns.record.create
* dns.record.update
* dns.record.delete
* dns.blacklist.create
* dns.blacklist.update
* dns.blacklist.delete
* dns.pool.create
* dns.pool.update
* dns.pool.delete
* dns.domain.update
* dns.zone.update
* dns.zone_transfer_request.create
* dns.zone_transfer_request.update
* dns.zone_transfer_request.delete
* dns.zone_transfer_accept.create
* dns.zone_transfer_accept.update
* dns.zone_transfer_accept.delete
* dns.zone_import.create
* dns.zone_import.update
* dns.zone_import.delete
* dns.zone_export.create
* dns.zone_export.update
* dns.zone_export.delete
* dns.zone.share
* dns.zone.unshare

Receivers
---------

Notification from other OpenStack component outside of Designate are
received by :ref:`designate-sink`.

Format
------

An example notification from Neutron:

.. literalinclude:: ../../../designate/tests/resources/sample_notifications/neutron/port.delete.start.json

More examples can be found at
:file:`designate/tests/resources/sample_notifications`

