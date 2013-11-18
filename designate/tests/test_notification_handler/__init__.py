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
import six
import testtools
from designate.notification_handler.base import Handler
from designate.tests import TestCase
from designate.tests import SkipNotImplementedMeta

FIXTURES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             '..',
                                             'sample_notifications'))


@six.add_metaclass(SkipNotImplementedMeta)
class NotificationHandlerTestCase(TestCase):
    __plugin_base__ = Handler

    def setUp(self):
        super(NotificationHandlerTestCase, self).setUp()

        self.central_service = self.get_central_service()
        self.central_service.start()

    def tearDown(self):
        self.central_service.stop()
        super(NotificationHandlerTestCase, self).tearDown()

    def get_notification_fixture(self, service, name):
        filename = os.path.join(FIXTURES_PATH, service, '%s.json' % name)

        if not os.path.exists(filename):
            raise Exception('Invalid notification fixture requested')

        with open(filename, 'r') as fh:
            return json.load(fh)

    def test_invalid_event_type(self):
        if not hasattr(self, 'plugin'):
            raise NotImplementedError
        event_type = 'invalid'

        self.assertNotIn(event_type, self.plugin.get_event_types())

        with testtools.ExpectedException(ValueError):
            self.plugin.process_notification(event_type, 'payload')
