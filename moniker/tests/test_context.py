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
from moniker.tests import TestCase
from moniker import context


class TestMonikerContext(TestCase):
    def test_sudo(self):
        # Set the policy to accept the authz
        self.policy({'use_sudo': '@'})

        ctxt = context.MonikerContext(tenant='original')
        ctxt.sudo('effective')

        self.assertEqual('effective', ctxt.tenant_id)
        self.assertEqual('original', ctxt.original_tenant_id)

    def test_sudo_fail(self):
        # Set the policy to deny the authz
        self.policy({'use_sudo': '!'})

        ctxt = context.MonikerContext(tenant='original')
        ctxt.sudo('effective')

        self.assertEqual('original', ctxt.tenant_id)
        self.assertEqual('original', ctxt.original_tenant_id)
