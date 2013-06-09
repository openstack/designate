General
=======

Administrative Access
---------------------

Administrative users can "sudo" into another tenant by providing an additional HTTP header: 'X-Designate-Sudo-Tenant-ID'

.. http:get:: /url

   Example HTTP Request using the X-Designate-Sudo-Tenant-ID header

   **Example request**:

   .. sourcecode:: http

      GET /domains/09494b72b65b42979efb187f65a0553e HTTP/1.1
      Host: example.com
      Accept: application/json
      X-Designate-Sudo-Tenant-ID: 12345
