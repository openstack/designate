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


class ListTsigKeysCommand(base.ListCommand):
    """ List TsigKeys """

    def execute(self, parsed_args):
        return central_api.get_tsigkeys(self.context)


class GetTsigKeyCommand(base.GetCommand):
    """ Get TsigKey """

    def get_parser(self, prog_name):
        parser = super(GetTsigKeyCommand, self).get_parser(prog_name)

        parser.add_argument('id', help="TSIG Key ID")

        return parser

    def execute(self, parsed_args):
        return central_api.get_tsigkey(self.context, parsed_args.id)


class CreateTsigKeyCommand(base.CreateCommand):
    """ Create TsigKey """

    def get_parser(self, prog_name):
        parser = super(CreateTsigKeyCommand, self).get_parser(prog_name)

        parser.add_argument('--name', help="TSIG Key Name", required=True)
        parser.add_argument('--algorithm', help="TSIG Key Algorithm",
                            required=True)
        parser.add_argument('--secret', help="TSIG Key Secret", required=True)

        return parser

    def execute(self, parsed_args):
        tsigkey = dict(
            name=parsed_args.name,
            algorithm=parsed_args.algorithm,
            secret=parsed_args.secret,
        )

        return central_api.create_tsigkey(self.context, tsigkey)


class UpdateTsigKeyCommand(base.UpdateCommand):
    """ Update TsigKey """

    def get_parser(self, prog_name):
        parser = super(UpdateTsigKeyCommand, self).get_parser(prog_name)

        parser.add_argument('id', help="TSIG Key ID")
        parser.add_argument('--name', help="TSIG Key Name")
        parser.add_argument('--algorithm', help="TSIG Key Algorithm")
        parser.add_argument('--secret', help="TSIG Key Secret")

        return parser

    def execute(self, parsed_args):
        tsigkey = {}

        if parsed_args.name:
            tsigkey['name'] = parsed_args.name

        if parsed_args.algorithm:
            tsigkey['algorithm'] = parsed_args.algorithm

        if parsed_args.secret:
            tsigkey['secret'] = parsed_args.secret

        return central_api.update_tsigkey(self.context, parsed_args.id,
                                          tsigkey)


class DeleteTsigKeyCommand(base.DeleteCommand):
    """ Delete TsigKey """

    def get_parser(self, prog_name):
        parser = super(DeleteTsigKeyCommand, self).get_parser(prog_name)

        parser.add_argument('id', help="TSIG Key ID")

        return parser

    def execute(self, parsed_args):
        return central_api.delete_tsigkey(self.context, parsed_args.id)
