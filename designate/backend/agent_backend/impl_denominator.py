# Copyright 2015 Dyn Inc.
#
# Author: Yasha Bubnov <ybubnov@dyn.com>
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
import itertools

import dns.rdata
import dns.rdatatype
import dns.rdataclass
from oslo_config import cfg
from oslo_concurrency import lockutils
from oslo_log import log as logging

from designate.backend.agent_backend import base
from designate import exceptions
from designate import utils
from designate.i18n import _LI


LOG = logging.getLogger(__name__)
CFG_GROUP = 'backend:agent:denominator'


class Denominator(object):

    def __init__(self, config):
        super(Denominator, self).__init__()
        self.config = config

    def update_record(self, zone, **kwargs):
        return self._execute(['record', '-z', zone, 'replace'], kwargs)

    def create_record(self, zone, **kwargs):
        return self._execute(['record', '-z', zone, 'add'], kwargs)

    def delete_record(self, zone, **kwargs):
        return self._execute(['record', '-z', zone, 'delete'], kwargs)

    def get_record(self, zone, **kwargs):
        return self._execute(['record', '-z', zone, 'get'], kwargs)

    def get_records(self, zone, **kwargs):
        return self._execute(['record', '-z', zone, 'list'], kwargs)

    def create_zone(self, **kwargs):
        return self._execute(['zone', 'add'], kwargs)

    def update_zone(self, **kwargs):
        return self._execute(['zone', 'update'], kwargs)

    def delete_zone(self, **kwargs):
        return self._execute(['zone', 'delete'], kwargs)

    def _params(self, **kwargs):
        params = [('--%s' % k, str(v)) for k, v in kwargs.items()]
        return list(itertools.chain(*params))

    def _base(self):
        call = ['denominator', '-q', '-n', self.config.name]

        # NOTE: When path to denominator configuration file is ommited,
        #       ~/.denominatorconfig file will be used by default.
        if self.config.config_file:
            call.extend(['-C', self.config.config_file])
        return call

    def _execute(self, op, kwargs):
        try:
            call = self._base() + op + self._params(**kwargs)
            LOG.debug(('Executing Denominator call: %s' % ' '.join(call)))

            stdout, _ = utils.execute(*call)
            return stdout
        except utils.processutils.ProcessExecutionError as e:
            LOG.debug('Denominator call failure: %s' % e)
            raise exceptions.Base(e)


class DenominatorBackend(base.AgentBackend):
    __plugin_name__ = 'denominator'

    __backend_status__ = 'untested'

    def __init__(self, agent_service):
        super(DenominatorBackend, self).__init__(agent_service)
        self.denominator = Denominator(cfg.CONF[CFG_GROUP])

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(
            name=CFG_GROUP,
            title='Backend options for Denominator',
        )

        opts = [
            cfg.StrOpt('name', default='fake',
                help='Name of the affected provider'),
            cfg.StrOpt('config_file', default='/etc/denominator.conf',
                help='Path to Denominator configuration file')
        ]

        return [(group, opts)]

    def start(self):
        LOG.info(_LI("Started Denominator backend"))

    def stop(self):
        LOG.info(_LI("Stopped Denominator backend"))

    def find_domain_serial(self, domain_name):
        LOG.debug("Finding %s" % domain_name)

        domain_name = domain_name.rstrip('.')
        output = self.denominator.get_record(
            zone=domain_name,
            type='SOA',
            name=domain_name)
        try:
            text = ' '.join(output.split()[3:])
            rdata = dns.rdata.from_text(dns.rdataclass.IN,
                                        dns.rdatatype.SOA,
                                        text)
        except Exception:
            return None
        return rdata.serial

    def create_domain(self, domain):
        LOG.debug("Creating %s" % domain.origin.to_text())
        domain_name = domain.origin.to_text(omit_final_dot=True)

        # Use SOA TTL as zone default TTL
        soa_record = domain.find_rrset(domain.origin, dns.rdatatype.SOA)
        rname = soa_record.items[0].rname.derelativize(origin=domain.origin)

        # Lock domain to prevent concurrent changes.
        with self._sync_domain(domain.origin):
            # NOTE: If zone already exists, denominator will update it with
            #       new values, in other a duplicate zone will be created if
            #       provider supports such functionality.
            self.denominator.create_zone(
                name=domain_name,
                ttl=soa_record.ttl,
                email=rname)

            # Add records one by one.
            for name, ttl, rtype, data in self._iterate_records(domain):
                # Some providers do not support creationg of SOA record.
                rdatatype = dns.rdatatype.from_text(rtype)
                if rdatatype == dns.rdatatype.SOA:
                    continue

                self.denominator.create_record(
                    zone=domain_name,
                    name=name,
                    type=rtype,
                    ttl=ttl,
                    data=data)

    def update_domain(self, domain):
        LOG.debug("Updating %s" % domain.origin)
        domain_name = domain.origin.to_text(omit_final_dot=True)

        soa_record = domain.find_rrset(domain.origin, dns.rdatatype.SOA)
        rname = soa_record.items[0].rname.derelativize(origin=domain.origin)

        with self._sync_domain(domain.origin):
            # Update zone with a new parameters
            self.denominator.update_zone(
                id=domain_name,
                ttl=soa_record.ttl,
                email=rname)

            # Fetch records to create a differential update of a zone.
            output = self.denominator.get_records(domain_name)
            subdomains = dict()

            # Subdomains dict will contain names of subdomains without
            # trailing dot.
            for raw in output.splitlines():
                data = raw.split()
                name, rtype = data[0], data[1]

                rtypes = subdomains.get(name, set())
                rtypes.add(rtype)
                subdomains[name] = rtypes

            for name, ttl, rtype, data in self._iterate_records(domain):
                record_action = self.denominator.create_record

                if name in subdomains and rtype in subdomains[name]:
                    # When RR set already exists, replace it with a new one.
                    rdatatype = dns.rdatatype.from_text(rtype)
                    record_action = self.denominator.update_record

                    # So next call will ADD a new record to record set
                    # instead of replacing of the existing one.
                    subdomains[name].remove(rtype)

                    # NOTE: DynECT does not support deleting of the SOA
                    #       record. Skip updating of the SOA record.
                    if rdatatype == dns.rdatatype.SOA:
                        continue

                record_action(zone=domain_name,
                              name=name,
                              type=rtype,
                              ttl=ttl,
                              data=data)

            # Remaining records should be deleted
            for name, types in subdomains.items():
                for rtype in types:
                    self.denominator.delete_record(
                        zone=domain_name, id=name, type=rtype)

    def delete_domain(self, domain_name):
        LOG.debug('Delete Domain: %s' % domain_name)

        with self._sync_domain(domain_name):
            self.denominator.delete_zone(id=domain_name)

    def _sync_domain(self, domain_name):
        LOG.debug('Synchronising domain: %s' % domain_name)
        return lockutils.lock('denominator-%s' % domain_name)

    def _iterate_records(self, domain):
        for rname, ttl, rdata in domain.iterate_rdatas():
            name = rname.derelativize(origin=domain.origin)
            name = name.to_text(omit_final_dot=True)

            data = rdata.to_text(origin=domain.origin, relativize=False)
            yield name, ttl, dns.rdatatype.to_text(rdata.rdtype), data
