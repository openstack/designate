"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from oslo_config import cfg
from tempest_lib import exceptions

from functionaltests.api.v2.clients.quotas_client import QuotasClient
from functionaltests.api.v2.clients.tld_client import TLDClient
from functionaltests.api.v2.models.quotas_model import QuotasModel
from functionaltests.api.v2.models.tld_model import TLDModel
from functionaltests.common.base import BaseDesignateTest


class DesignateV2Test(BaseDesignateTest):

    def increase_quotas(self, user):
        if cfg.CONF.testconfig.no_admin_setup:
            return
        QuotasClient.as_user('admin').patch_quotas(
            QuotasClient.as_user(user).tenant_id,
            QuotasModel.from_dict({
                'quota': {
                    'zones': 9999999,
                    'recordset_records': 9999999,
                    'zone_records': 9999999,
                    'zone_recordsets': 9999999}}))

    def ensure_tld_exists(self, tld='com'):
        if cfg.CONF.testconfig.no_admin_setup:
            return
        try:
            tld_model = TLDModel.from_dict({'name': tld})
            TLDClient.as_user('admin').post_tld(tld_model)
        except exceptions.Conflict:
            pass

    def _assert_invalid_uuid(self, method, *args, **kw):
        """
        Test that UUIDs used in the URL is valid.
        """
        self._assert_exception(
            exceptions.BadRequest, 'invalid_uuid', 400, method, *args)

    def _assert_exception(self, exc, type_, status, method, *args, **kwargs):
        """
        Checks the response that a api call with a exception contains the
        wanted data.
        """
        try:
            method(*args, **kwargs)
        except exc as e:
            self.assertEqual(status, e.resp_body['code'])
            self.assertEqual(type_, e.resp_body['type'])
            return e
        else:
            raise self.failureException("Test failed due to no exception.")
