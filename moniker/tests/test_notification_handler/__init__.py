# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import json
import os
from moniker.openstack.common import cfg
from moniker.tests import TestCase

FIXTURES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..',
                                             'sample_notifications'))


class NotificationHandlerTestCase(TestCase):
    __test__ = False
    handler_cls = None

    def setUp(self):
        super(NotificationHandlerTestCase, self).setUp()
        self.central_service = self.get_central_service()
        self._init_handler()

    def _pre_init_handler(self):
        """
        Stuff to run before actually initializing the handler.

        Should return a dict that will be passed to the handler's register_opts
        """
        return {}

    def _init_handler(self):
        """
        Initialize the Handler doing _pre_init_handler before
        instantiating the handler
        """
        self.handler_cls.register_opts(cfg.CONF)

        handler_conf = self._pre_init_handler() or {}
        self.config(group=self.handler_cls.get_canonical_name(),
                    **handler_conf)
        self.handler = self.handler_cls(self.central_service)

    def get_notification_fixture(self, service, name):
        filename = os.path.join(FIXTURES_PATH, service, '%s.json' % name)

        if not os.path.exists(filename):
            raise Exception('Invalid notification fixture requested')

        with open(filename, 'r') as fh:
            return json.load(fh)

    def test_invalid_event_type(self):
        event_type = 'invalid'

        self.assertNotIn(event_type, self.handler.get_event_types())

        with self.assertRaises(ValueError):
            self.handler.process_notification(event_type, 'payload')


class AddressHandlerTestCase(NotificationHandlerTestCase):
    """
    Test something that receives notifications with regards to addresses
    """
    def _pre_init_handler(self):
        # Create provider domain
        values = {'name': 'exampe.com', 'email': 'info@example.com'}

        domain = self.central_service.create_domain(self.admin_context, values)
        self.domain_id = str(domain['id'])
        return {"domain_id": str(domain["id"])}
