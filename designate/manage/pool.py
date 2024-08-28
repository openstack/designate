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
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_utils import uuidutils
import stevedore.exception
import yaml

from designate.backend import base as backend_base
from designate.central import rpcapi as central_rpcapi
import designate.conf
from designate import exceptions
from designate.manage import base
from designate import objects
from designate.objects.adapters import DesignateAdapter
from designate import policy
from designate import rpc


CONF = designate.conf.CONF
LOG = logging.getLogger(__name__)


class PoolCommands(base.Commands):
    def __init__(self):
        super().__init__()
        self.central_api = None
        self.dry_run = False
        self.skip_verify_drivers = False

    def _setup(self, dry_run=False, skip_verify_drivers=False):
        self.dry_run = dry_run
        self.skip_verify_drivers = skip_verify_drivers
        rpc.init(CONF)
        self.central_api = central_rpcapi.CentralAPI()

    @base.args('--file', help='The path to the file the yaml output should be '
                              'written to',
               default='/etc/designate/pools.yaml')
    def generate_file(self, file):
        self._setup()

        try:
            pools = self.central_api.find_pools(self.context)
            data = DesignateAdapter.render('YAML', pools)
            self._write_config_to_file(file, data)

        except messaging.exceptions.MessagingTimeout:
            LOG.critical(
                'No response received from designate-central. '
                'Check it is running, and retry'
            )
            raise SystemExit(1)

    @base.args('--pool_id', help='ID of the pool to be examined',
               default=CONF['service:central'].default_pool_id)
    @base.args('--all_pools', help='show the config of all the pools',
               default=False, required=False, action='store_true')
    def show_config(self, pool_id, all_pools):
        self._setup()

        self.output_message.append('Pool Configuration:')
        self.output_message.append('-------------------')

        try:
            pools = objects.PoolList()
            if all_pools:
                pools.extend(self.central_api.find_pools(self.context))
            else:
                if not uuidutils.is_uuid_like(pool_id):
                    self.output_message.append(
                        'Not a valid uuid: %s' % pool_id)
                    raise SystemExit(1)
                pools.append(
                    self.central_api.find_pool(self.context, {'id': pool_id}))

            self.output_message.append(
                yaml.dump(
                    DesignateAdapter.render('YAML', pools),
                    default_flow_style=False
                )
            )

        except exceptions.PoolNotFound:
            self.output_message.append('Pool not found')
            raise SystemExit(1)
        except messaging.exceptions.MessagingTimeout:
            LOG.critical(
                'No response received from designate-central. '
                'Check it is running, and retry'
            )
            raise SystemExit(1)
        finally:
            self._print_result()

    @base.args('--file', help='The path to the yaml file describing the pools',
               default='/etc/designate/pools.yaml')
    @base.args(
        '--delete',
        help='Any Pools not listed in the config file will be deleted. '
             ' WARNING: This will delete any zones left in this pool',
        action='store_true',
        default=False)
    @base.args(
        '--dry-run',
        help='This will simulate what will happen when you run this command',
        action='store_true',
        default=False)
    @base.args(
        '--skip-verify-drivers',
        help='Don\'t verify the designate backend drivers',
        action='store_true',
        default=False)
    def update(self, file, delete, dry_run=False, skip_verify_drivers=False):
        self._setup(dry_run, skip_verify_drivers)

        try:
            self.output_message.append('Updating Pools Configuration')
            self.output_message.append('****************************')

            pools_data = self._load_config(file)

            if dry_run:
                self.output_message.append('The following changes will occur:')
                self.output_message.append('*********************************')

            for pool_data in pools_data:
                try:
                    self._create_or_update_pool(pool_data)
                except exceptions.DuplicatePool:
                    raise exceptions.DuplicatePool(
                        f'Pool {pool_data["name"]} already exist with id '
                        f'{pool_data["id"]}. You cannot change id to an '
                        'existing pool.')

            if delete:
                pools = self.central_api.find_pools(self.context)
                pools_in_db = {pool.name for pool in pools}
                pools_in_yaml = {pool_data['name'] for pool_data in pools_data}
                pools_to_delete = pools_in_db - pools_in_yaml
                for pool_name in pools_to_delete:
                    self._delete_pool(pool_name)

        except exceptions.InvalidObject as e:
            self.output_message.append(str(e))
            raise SystemExit(1)
        except messaging.exceptions.MessagingTimeout:
            LOG.critical(
                'No response received from designate-central. '
                'Check it is running, and retry'
            )
            raise SystemExit(1)
        finally:
            self._print_result()

    def _create_or_update_pool(self, pool_data):
        try:
            pool = self._get_pool(pool_data)
            self._update_pool(pool_data, pool)

        except exceptions.PoolNotFound:
            self._create_pool(pool_data)

    def _get_pool(self, pool_data):
        if 'id' in pool_data:
            pool_id = pool_data['id']
            if not uuidutils.is_uuid_like(pool_id):
                self.output_message.append('Not a valid uuid: %s' % pool_id)
                raise SystemExit(1)

            pool = self.central_api.get_pool(
                self.context, pool_id
            )
        else:
            pool = self.central_api.find_pool(
                self.context, {'name': pool_data['name']}
            )

        return pool

    def _create_pool(self, pool_data):
        pool = DesignateAdapter.parse('YAML', pool_data, objects.Pool())
        self._validate_pool(pool)

        if self.dry_run:
            self.output_message.append('Create Pool: %s' % pool)
        else:
            LOG.info('Creating new pool: %s', pool)
            self.central_api.create_pool(self.context, pool)

        return pool

    def _update_pool(self, pool_data, pool):
        pool = DesignateAdapter.parse('YAML', pool_data, pool)
        self._validate_pool(pool)

        if self.dry_run:
            self.output_message.append('Update Pool: %s' % pool)
        else:
            pool = self.central_api.update_pool(self.context, pool)
            self._update_zones(pool)

    def _delete_pool(self, pool_name):
        pool = self.central_api.find_pool(
            self.context, criterion={'name': pool_name}
        )

        if self.dry_run:
            self.output_message.append('Delete Pool: %s' % pool_name)
        else:
            LOG.info('Deleting %s', pool_name)
            self.central_api.delete_pool(self.context, pool.id)

    def _update_zones(self, pool):
        LOG.info('Updating zone masters for pool: %s', pool.id)

        policy.init()
        self.context.all_tenants = True
        zones = self.central_api.find_zones(
            self.context, criterion={'pool_id': pool.id}
        )

        for zone in zones:
            zone.masters = objects.ZoneMasterList().from_list(
                self._get_masters_from_pool(pool)
            )
            self.central_api.update_zone(self.context, zone)

    def _validate_pool(self, pool):
        for ns_record in pool.ns_records:
            ns_record.validate()

        if not self.skip_verify_drivers:
            for target in pool.targets:
                try:
                    backend_base.Backend.get_driver(target.type)
                except stevedore.exception.NoMatches:
                    self.output_message.append(
                        'Unable to find designate backend driver type: '
                        '%s' % target.type
                    )
                    if not self.dry_run:
                        raise SystemExit(1)

    @staticmethod
    def _get_masters_from_pool(pool):
        masters = []
        for target in pool.targets:
            for master in target.get('masters', []):
                master = {'host': master['host'], 'port': master['port']}
                found = False
                for existing_master in masters:
                    if master == existing_master:
                        found = True
                if not found:
                    masters.append(master)
        return masters

    @staticmethod
    def _load_config(filename):
        with open(filename) as stream:
            return yaml.safe_load(stream)

    @staticmethod
    def _write_config_to_file(filename, data):
        with open(filename, 'w') as stream:
            yaml.dump(data, stream, default_flow_style=False)
