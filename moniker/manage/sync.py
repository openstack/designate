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
from moniker.openstack.common import log as logging
from moniker.manage import base
from moniker.central import api as central_api

LOG = logging.getLogger(__name__)


class SyncAllCommand(base.Command):
    """ Sync Everything """

    def take_action(self, parsed_args):
        return central_api.sync_all(self.context)


class SyncDomainCommand(base.Command):
    """ Sync A Single Domain """

    def get_parser(self, prog_name):
        parser = super(SyncDomainCommand, self).get_parser(prog_name)

        parser.add_argument('id', help="Domain ID")

        return parser

    def take_action(self, parsed_args):
        return central_api.sync_domain(self.context, parsed_args.id)


class SyncRecordCommand(base.Command):
    """ Sync A Single Record """

    def get_parser(self, prog_name):
        parser = super(SyncDomainCommand, self).get_parser(prog_name)

        parser.add_argument('domain_id', help="Domain ID")
        parser.add_argument('id', help="Record ID")

        return parser

    def take_action(self, parsed_args):
        return central_api.sync_record(self.context, parsed_args.domain_id,
                                       parsed_args.id)
