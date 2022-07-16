# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
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
import sys

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
import yaml

from designate.central import rpcapi as central_rpcapi
from designate import exceptions
from designate.manage import base
from designate import objects
from designate.objects.adapters import DesignateAdapter
from designate import policy
from designate import rpc

LOG = logging.getLogger(__name__)


CONF = cfg.CONF


class PoolCommands(base.Commands):
    def __init__(self):
        super(PoolCommands, self).__init__()

    # NOTE(jh): Cannot do this earlier because we are still missing the config
    # at that point, see bug #1651576
    def _startup(self):
        rpc.init(cfg.CONF)
        self.central_api = central_rpcapi.CentralAPI()

    def _update_zones(self, pool):
        LOG.info("Updating zone masters for pool: {}".format(pool.id))

        def __get_masters_from_pool(pool):
            masters = []
            for target in pool.targets:
                for master in target.get("masters", []):
                    master = {'host': master['host'], 'port': master['port']}
                    found = False
                    for existing_master in masters:
                        if master == existing_master:
                            found = True
                    if not found:
                        masters.append(master)
            return masters

        policy.init()

        self.context.all_tenants = True
        zones = self.central_api.find_zones(
            self.context,
            criterion={'pool_id': pool.id})

        for zone in zones:
            zone.masters = objects.ZoneMasterList().from_list(
                __get_masters_from_pool(pool))
            self.central_api.update_zone(self.context,
                                         zone)

    @base.args('--file', help='The path to the file the yaml output should be '
               'written to',
               default='/etc/designate/pools.yaml')
    def generate_file(self, file):
        self._startup()
        try:
            pools = self.central_api.find_pools(self.context)
        except messaging.exceptions.MessagingTimeout:
            LOG.critical("No response received from designate-central. "
                         "Check it is running, and retry")
            sys.exit(1)
        with open(file, 'w') as stream:
            yaml.dump(
                DesignateAdapter.render('YAML', pools),
                stream,
                default_flow_style=False
            )

    @base.args('--pool_id', help='ID of the pool to be examined',
               default=CONF['service:central'].default_pool_id)
    def show_config(self, pool_id):
        self._startup()
        try:
            pool = self.central_api.find_pool(self.context, {"id": pool_id})

            print('Pool Configuration:')
            print('-------------------')

            print(yaml.dump(DesignateAdapter.render('YAML', pool),
                            default_flow_style=False))

        except messaging.exceptions.MessagingTimeout:
            LOG.critical("No response received from designate-central. "
                         "Check it is running, and retry")
            sys.exit(1)

    @base.args('--file', help='The path to the yaml file describing the pools',
               default='/etc/designate/pools.yaml')
    @base.args(
        '--delete',
        help='Any Pools not listed in the config file will be deleted. '
             ' WARNING: This will delete any zones left in this pool',
        action="store_true",
        default=False)
    @base.args(
        '--dry-run',
        help='This will simulate what will happen when you run this command',
        action="store_true",
        default=False)
    def update(self, file, delete, dry_run):
        self._startup()
        print('Updating Pools Configuration')
        print('****************************')
        output_msg = ['']

        with open(file, 'r') as stream:
            xpools = yaml.safe_load(stream)

        if dry_run:
            output_msg.append("The following changes will occur:")
            output_msg.append("*********************************")

        for xpool in xpools:
            try:
                if 'id' in xpool:
                    try:
                        pool = self.central_api.get_pool(
                            self.context, xpool['id'])
                    except Exception as e:
                        msg = ("Bad ID Supplied for pool. pool_id: "
                            "%(pool)s message: %(res)s")
                        LOG.critical(msg, {'pool': xpool['id'], 'res': e})
                        continue
                else:
                    pool = self.central_api.find_pool(
                        self.context, {"name": xpool['name']})

                LOG.info('Updating existing pool: %s', pool)

                # TODO(kiall): Move the below into the pool object

                pool = DesignateAdapter.parse('YAML', xpool, pool)

                # TODO(graham): We should be doing a full validation, but right
                # now there is quirks validating through nested objects.

                for ns_record in pool.ns_records:
                    try:
                        ns_record.validate()
                    except exceptions.InvalidObject as e:
                        LOG.error(e.errors.to_list()[0]['message'])
                        sys.exit(1)

                if dry_run:
                    output_msg.append("Update Pool: %s" % pool)
                else:
                    pool = self.central_api.update_pool(self.context, pool)
                    # Bug: Changes in the pool targets should trigger a
                    # zone masters update LP: #1879798.
                    self._update_zones(pool)

            except exceptions.PoolNotFound:
                pool = DesignateAdapter.parse('YAML', xpool, objects.Pool())
                for ns_record in pool.ns_records:
                    try:
                        ns_record.validate()
                    except exceptions.InvalidObject as e:
                        LOG.error(e.errors.to_list()[0]['message'])
                        sys.exit(1)
                if dry_run:
                    output_msg.append("Create Pool: %s" % pool)
                else:
                    LOG.info('Creating new pool: %s', pool)
                    self.central_api.create_pool(self.context, pool)
            except messaging.exceptions.MessagingTimeout:
                LOG.critical("No response received from designate-central. "
                             "Check it is running, and retry")
                sys.exit(1)

        if delete:
            pools = self.central_api.find_pools(self.context)
            pools_in_db = {pool.name for pool in pools}
            pools_in_yaml = {xpool['name'] for xpool in xpools}

            pools_to_delete = pools_in_db - pools_in_yaml

            for pool in pools_to_delete:
                try:
                    p = self.central_api.find_pool(
                        self.context,
                        criterion={'name': pool})

                    if dry_run:
                        output_msg.append("Delete Pool: %s" % p)

                    else:
                        LOG.info('Deleting %s', p)
                        self.central_api.delete_pool(self.context, p.id)

                except messaging.exceptions.MessagingTimeout:
                    LOG.critical(
                        "No response received from designate-central. "
                        "Check it is running, and retry")
                    sys.exit(1)

        for line in output_msg:
            print(line)
