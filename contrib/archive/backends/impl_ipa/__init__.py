# Copyright 2014 Red Hat, Inc.
#
# Author: Rich Megginson <rmeggins@redhat.com>
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
import pprint
import time

import requests
from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils as json
from oslo_utils import importutils

from designate import exceptions
from designate.backend import base
from designate.i18n import _LE


LOG = logging.getLogger(__name__)

IPA_DEFAULT_PORT = 443


class IPABaseError(exceptions.Backend):
    error_code = 500
    error_type = 'unknown_ipa_error'


class IPAAuthError(IPABaseError):
    error_type = 'authentication_error'


# map of designate domain parameters to the corresponding
# ipa parameter
# NOTE: ipa manages serial, and does not honor
# increment_serial=False - this means the designate serial
# and the ipa serial will diverge if updates are made
# using increment_serial=False
domain2ipa = {'ttl': 'dnsttl', 'email': 'idnssoarname',
              'serial': 'idnssoaserial', 'expire': 'idnssoaexpire',
              'minimum': 'idnssoaminimum', 'refresh': 'idnssoarefresh',
              'retry': 'idnssoaretry'}

# map of designate record types to ipa
rectype2iparectype = {'A': ('arecord', '%(data)s'),
                      'AAAA': ('aaaarecord', '%(data)s'),
                      'MX': ('mxrecord', '%(data)s'),
                      'CNAME': ('cnamerecord', '%(data)s'),
                      'TXT': ('txtrecord', '%(data)s'),
                      'SRV': ('srvrecord', '%(data)s'),
                      'NS': ('nsrecord', '%(data)s'),
                      'PTR': ('ptrrecord', '%(data)s'),
                      'SPF': ('spfrecord', '%(data)s'),
                      'SSHFP': ('sshfprecord', '%(data)s')}

IPA_INVALID_DATA = 3009
IPA_NOT_FOUND = 4001
IPA_DUPLICATE = 4002
IPA_NO_CHANGES = 4202


class IPAUnknownError(IPABaseError):
    pass


class IPACommunicationFailure(IPABaseError):
    error_type = 'communication_failure'
    pass


class IPAInvalidData(IPABaseError):
    error_type = 'invalid_data'
    pass


class IPADomainNotFound(IPABaseError):
    error_type = 'domain_not_found'
    pass


class IPARecordNotFound(IPABaseError):
    error_type = 'record_not_found'
    pass


class IPADuplicateDomain(IPABaseError):
    error_type = 'duplicate_domain'
    pass


class IPADuplicateRecord(IPABaseError):
    error_type = 'duplicate_record'
    pass


ipaerror2exception = {
    IPA_INVALID_DATA: {
        'dnszone': IPAInvalidData,
        'dnsrecord': IPAInvalidData
    },
    IPA_NOT_FOUND: {
        'dnszone': IPADomainNotFound,
        'dnsrecord': IPARecordNotFound
    },
    IPA_DUPLICATE: {
        'dnszone': IPADuplicateDomain,
        'dnsrecord': IPADuplicateRecord
    },
    # NOTE: Designate will send updates with all fields
    # even if they have not changed value.  If none of
    # the given values has changed, IPA will return
    # this error code - this can be ignored
    IPA_NO_CHANGES: {
        'dnszone': None,
        'dnsrecord': None
    }
}


def abs2rel_name(domain, rsetname):
    """convert rsetname from absolute form foo.bar.tld. to the name
    relative to the domain.  For IPA, if domain is rsetname, then use
    "@" as the relative name.  If rsetname does not end with a subset
    of the domain, the just return the raw rsetname
    """
    if rsetname.endswith(domain):
        idx = rsetname.rfind(domain)
        if idx == 0:
            rsetname = "@"
        elif idx > 0:
            rsetname = rsetname[:idx].rstrip(".")
    return rsetname


class IPABackend(base.Backend):
    __plugin_name__ = 'ipa'

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(
            name='backend:ipa', title="Configuration for IPA Backend"
        )

        opts = [
            cfg.StrOpt('ipa-host', default='localhost.localdomain',
                       help='IPA RPC listener host - must be FQDN'),
            cfg.IntOpt('ipa-port', default=IPA_DEFAULT_PORT,
                       help='IPA RPC listener port'),
            cfg.StrOpt('ipa-client-keytab',
                       help='Kerberos client keytab file'),
            cfg.StrOpt('ipa-auth-driver-class',
                       default='designate.backend.impl_ipa.auth.IPAAuth',
                       help='Class that implements the authentication '
                       'driver for IPA'),
            cfg.StrOpt('ipa-ca-cert',
                       help='CA certificate for use with https to IPA'),
            cfg.StrOpt('ipa-base-url', default='/ipa',
                       help='Base URL for IPA RPC, relative to host[:port]'),
            cfg.StrOpt('ipa-json-url',
                       default='/json',
                       help='URL for IPA JSON RPC, relative to IPA base URL'),
            cfg.IntOpt('ipa-connect-retries', default=1,
                       help='How many times Designate will attempt to retry '
                       'the connection to IPA before giving up'),
            cfg.BoolOpt('ipa-force-ns-use', default=False,
                        help='IPA requires that a specified '
                        'name server or SOA MNAME is resolvable - if this '
                        'option is set, Designate will force IPA to use a '
                        'given name server even if it is not resolvable'),
            cfg.StrOpt('ipa-version', default='2.65',
                       help='IPA RPC JSON version')
        ]

        return [(group, opts)]

    def start(self):
        LOG.debug('IPABackend start')
        self.request = requests.Session()
        authclassname = cfg.CONF[self.name].ipa_auth_driver_class
        authclass = importutils.import_class(authclassname)
        self.request.auth = \
            authclass(cfg.CONF[self.name].ipa_client_keytab,
                      cfg.CONF[self.name].ipa_host)
        ipa_base_url = cfg.CONF[self.name].ipa_base_url
        if ipa_base_url.startswith("http"):  # full URL
            self.baseurl = ipa_base_url
        else:  # assume relative to https://host[:port]
            self.baseurl = "https://" + cfg.CONF[self.name].ipa_host
            ipa_port = cfg.CONF[self.name].ipa_port
            if ipa_port != IPA_DEFAULT_PORT:
                self.baseurl += ":" + str(ipa_port)
            self.baseurl += ipa_base_url
        ipa_json_url = cfg.CONF[self.name].ipa_json_url
        if ipa_json_url.startswith("http"):  # full URL
            self.jsonurl = ipa_json_url
        else:  # assume relative to https://host[:port]
            self.jsonurl = self.baseurl + ipa_json_url
        xtra_hdrs = {'Content-Type': 'application/json',
                     'Referer': self.baseurl}
        self.request.headers.update(xtra_hdrs)
        self.request.verify = cfg.CONF[self.name].ipa_ca_cert
        self.ntries = cfg.CONF[self.name].ipa_connect_retries
        self.force = cfg.CONF[self.name].ipa_force_ns_use

    def create_zone(self, context, zone):
        LOG.debug('Create Zone %r' % zone)
        ipareq = {'method': 'dnszone_add', 'id': 0}
        params = [zone['name']]
        servers = self.central_service.get_zone_ns_records(self.admin_context)
        # just use the first one for zone creation - add the others
        # later, below - use force because designate assumes the NS
        # already exists somewhere, is resolvable, and already has
        # an A/AAAA record
        args = {'idnssoamname': servers[0]['name']}
        if self.force:
            args['force'] = True
        for dkey, ipakey in list(domain2ipa.items()):
            if dkey in zone:
                args[ipakey] = zone[dkey]
        ipareq['params'] = [params, args]
        self._call_and_handle_error(ipareq)
        # add NS records for all of the other servers
        if len(servers) > 1:
            ipareq = {'method': 'dnsrecord_add', 'id': 0}
            params = [zone['name'], "@"]
            args = {'nsrecord': servers[1:]}
            if self.force:
                args['force'] = True
            ipareq['params'] = [params, args]
            self._call_and_handle_error(ipareq)

    def update_zone(self, context, zone):
        LOG.debug('Update Zone %r' % zone)
        ipareq = {'method': 'dnszone_mod', 'id': 0}
        params = [zone['name']]
        args = {}
        for dkey, ipakey in list(domain2ipa.items()):
            if dkey in zone:
                args[ipakey] = zone[dkey]
        ipareq['params'] = [params, args]
        self._call_and_handle_error(ipareq)

    def delete_zone(self, context, zone):
        LOG.debug('Delete Zone %r' % zone)
        ipareq = {'method': 'dnszone_del', 'id': 0}
        params = [zone['name']]
        args = {}
        ipareq['params'] = [params, args]
        self._call_and_handle_error(ipareq)

    def create_recordset(self, context, domain, recordset):
        LOG.debug('Discarding create_recordset call, not-applicable')

    def update_recordset(self, context, domain, recordset):
        LOG.debug('Update RecordSet %r / %r' % (domain, recordset))
        # designate allows to update a recordset if there are no
        # records in it - we should ignore this case
        if not self._recset_has_records(context, recordset):
            LOG.debug('No records in %r / %r - skipping' % (domain, recordset))
            return
        # The only thing IPA allows is to change the ttl, since that is
        # stored "per recordset"
        if 'ttl' not in recordset:
            return
        ipareq = {'method': 'dnsrecord_mod', 'id': 0}
        dname = domain['name']
        rsetname = abs2rel_name(dname, recordset['name'])
        params = [domain['name'], rsetname]
        args = {'dnsttl': recordset['ttl']}
        ipareq['params'] = [params, args]
        self._call_and_handle_error(ipareq)

    def delete_recordset(self, context, domain, recordset):
        LOG.debug('Delete RecordSet %r / %r' % (domain, recordset))
        # designate allows to delete a recordset if there are no
        # records in it - we should ignore this case
        if not self._recset_has_records(context, recordset):
            LOG.debug('No records in %r / %r - skipping' % (domain, recordset))
            return
        ipareq = {'method': 'dnsrecord_mod', 'id': 0}
        dname = domain['name']
        rsetname = abs2rel_name(dname, recordset['name'])
        params = [domain['name'], rsetname]
        rsettype = rectype2iparectype[recordset['type']][0]
        args = {rsettype: None}
        ipareq['params'] = [params, args]
        self._call_and_handle_error(ipareq)

    def create_record(self, context, domain, recordset, record):
        LOG.debug('Create Record %r / %r / %r' % (domain, recordset, record))
        ipareq = {'method': 'dnsrecord_add', 'id': 0}
        params, args = self._rec_to_ipa_rec(domain, recordset, [record])
        ipareq['params'] = [params, args]
        self._call_and_handle_error(ipareq)

    def update_record(self, context, domain, recordset, record):
        LOG.debug('Update Record %r / %r / %r' % (domain, recordset, record))
        # for modify operations - IPA does not support a way to change
        # a particular field in a given record - e.g. for an MX record
        # with several values, IPA stores them like this:
        # name: "server1.local."
        # data: ["10 mx1.server1.local.", "20 mx2.server1.local."]
        # we could do a search of IPA, compare the values in the
        # returned array - but that adds an additional round trip
        # and is error prone
        # instead, we just get all of the current values and send
        # them in one big modify
        criteria = {'recordset_id': record['recordset_id']}
        reclist = self.central_service.find_records(self.admin_context,
                                                    criteria)
        ipareq = {'method': 'dnsrecord_mod', 'id': 0}
        params, args = self._rec_to_ipa_rec(domain, recordset, reclist)
        ipareq['params'] = [params, args]
        self._call_and_handle_error(ipareq)

    def delete_record(self, context, domain, recordset, record):
        LOG.debug('Delete Record %r / %r / %r' % (domain, recordset, record))
        ipareq = {'method': 'dnsrecord_del', 'id': 0}
        params, args = self._rec_to_ipa_rec(domain, recordset, [record])
        args['del_all'] = 0
        ipareq['params'] = [params, args]
        self._call_and_handle_error(ipareq)

    def ping(self, context):
        LOG.debug('Ping')
        # NOTE: This call will cause ipa to issue an error, but
        # 1) it should not throw an exception
        # 2) the response will indicate ipa is running
        # 3) the bandwidth usage is minimal
        ipareq = {'method': 'dnszone_show', 'id': 0}
        params = ['@']
        args = {}
        ipareq['params'] = [params, args]
        retval = {'result': True}
        try:
            self._call_and_handle_error(ipareq)
        except Exception as e:
            retval = {'result': False, 'reason': str(e)}
        return retval

    def _rec_to_ipa_rec(self, domain, recordset, reclist):
        dname = domain['name']
        rsetname = abs2rel_name(dname, recordset['name'])
        params = [dname, rsetname]
        rectype = recordset['type']
        vals = []
        for record in reclist:
            vals.append(rectype2iparectype[rectype][1] % record)
        args = {rectype2iparectype[rectype][0]: vals}
        ttl = recordset.get('ttl') or domain.get('ttl')
        if ttl is not None:
            args['dnsttl'] = ttl
        return params, args

    def _ipa_error_to_exception(self, resp, ipareq):
        exc = None
        if resp['error'] is None:
            return exc
        errcode = resp['error']['code']
        method = ipareq['method']
        methtype = method.split('_')[0]
        exclass = ipaerror2exception.get(errcode, {}).get(methtype,
                                                          IPAUnknownError)
        if exclass:
            LOG.debug("Error: ipa command [%s] returned error [%s]" %
                      (pprint.pformat(ipareq), pprint.pformat(resp)))
        elif errcode:  # not mapped
            LOG.debug("Ignoring IPA error code %d: %s" %
                      (errcode, pprint.pformat(resp)))
        return exclass

    def _call_and_handle_error(self, ipareq):
        if 'version' not in ipareq['params'][1]:
            ipareq['params'][1]['version'] = cfg.CONF[self.name].ipa_version
        need_reauth = False
        while True:
            status_code = 200
            try:
                if need_reauth:
                    self.request.auth.refresh_auth()
                rawresp = self.request.post(self.jsonurl,
                                            data=json.dumps(ipareq))
                status_code = rawresp.status_code
            except IPAAuthError:
                status_code = 401
            if status_code == 401:
                if self.ntries == 0:
                    # persistent inability to auth
                    LOG.error(_LE("Error: could not authenticate to IPA - "
                              "please check for correct keytab file"))
                    # reset for next time
                    self.ntries = cfg.CONF[self.name].ipa_connect_retries
                    raise IPACommunicationFailure()
                else:
                    LOG.debug("Refresh authentication")
                    need_reauth = True
                    self.ntries -= 1
                    time.sleep(1)
            else:
                # successful - reset
                self.ntries = cfg.CONF[self.name].ipa_connect_retries
                break
        try:
            resp = json.loads(rawresp.text)
        except ValueError:
            # response was not json - some sort of error response
            LOG.debug("Error: unknown error from IPA [%s]" % rawresp.text)
            raise IPAUnknownError("unable to process response from IPA")
        # raise the appropriate exception, if error
        exclass = self._ipa_error_to_exception(resp, ipareq)
        if exclass:
            # could add additional info/message to exception here
            raise exclass()
        return resp

    def _recset_has_records(self, context, recordset):
        """Return True if the recordset has records, False otherwise"""
        criteria = {'recordset_id': recordset['id']}
        num = self.central_service.count_records(self.admin_context,
                                                 criteria)
        return num > 0
