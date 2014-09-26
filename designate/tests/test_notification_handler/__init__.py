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

from designate.tests import resources


FIXTURES_PATH = os.path.join(resources.path, 'sample_notifications')


class NotificationHandlerMixin(object):
    def get_notification_fixture(self, service, name):
        filename = os.path.join(FIXTURES_PATH, service, '%s.json' % name)

        if not os.path.exists(filename):
            raise Exception('Invalid notification fixture requested')

        with open(filename, 'r') as fh:
            return json.load(fh)
