# Copyright (C) 2014 Red Hat, Inc.
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

import sys
import logging
import pprint
import json
import copy

import requests
from oslo_config import cfg

from designate.backend import impl_ipa
from designate.i18n import _LI
from designate.i18n import _LW
from designate.i18n import _LE
from designate import utils


logging.basicConfig()
LOG = logging.getLogger(__name__)

cfg.CONF.import_opt('api_base_uri', 'designate.api', 'service:api')
cfg.CONF.import_opt('backend_driver', 'designate.central', 'service:central')


class NoNameServers(Exception):
    pass


class AddServerError(Exception):
    pass


class DeleteServerError(Exception):
    pass


class AddDomainError(Exception):
    pass


class DeleteDomainError(Exception):
    pass


class AddRecordError(Exception):
    pass


cuiberrorstr = """ERROR: You cannot have Designate configured
to use the IPA backend when running this script.  It will wipe
out your IPA DNS data.  Please follow these steps:
* shutdown designate-central
* edit designate.conf
[service:central]
backend_driver = fake # or something other than ipa
* restart designate-central and other designate services
"""


class CannotUseIPABackend(Exception):
    pass


# create mapping of ipa record types to designate types
iparectype2designate = {}
for rectype, tup in list(impl_ipa.rectype2iparectype.items()):
    iparectype = tup[0]
    iparectype2designate[iparectype] = rectype


# using the all: True flag returns fields we can't use
# strip these keys from zones
zoneskips = ['dn', 'nsrecord', 'idnszoneactive', 'objectclass']


def rec2des(rec, zonename):
    """Convert an IPA record to Designate format.  A single IPA record
    returned from the search may translate into multiple Designate.
    IPA dnsrecord_find returns a "name".  Each DNS name may contain
    multiple record types.  Each record type may contain multiple
    values.  Each one of these values must be added separately to
    Designate.  This function returns all of those as a list of
    dict designate records.
    """
    # convert record name
    if rec['idnsname'][0] == '@':
        name = zonename
    else:
        name = rec['idnsname'][0] + "." + zonename
    # find all record types
    rectypes = []
    for k in rec:
        if k.endswith("record"):
            if k in iparectype2designate:
                rectypes.append(k)
            else:
                LOG.info(_LI("Skipping unknown record type "
                             "%(type)s in %(name)s"),
                         {'type': k, 'name': name})

    desrecs = []
    for rectype in rectypes:
        dtype = iparectype2designate[rectype]
        for ddata in rec[rectype]:
            desreq = {'name': name, 'type': dtype}
            if dtype == 'SRV' or dtype == 'MX':
                # split off the priority and send in a separate field
                idx = ddata.find(' ')
                desreq['priority'] = int(ddata[:idx])
                if dtype == 'SRV' and not ddata.endswith("."):
                    # if server is specified as relative, add zonename
                    desreq['data'] = ddata[(idx + 1):] + "." + zonename
                else:
                    desreq['data'] = ddata[(idx + 1):]
            else:
                desreq['data'] = ddata
            if rec.get('description', [None])[0]:
                desreq['description'] = rec.get('description')[0]
            if rec.get('ttl', [None])[0]:
                desreq['ttl'] = int(rec['dnsttl'][0])
            desrecs.append(desreq)
    return desrecs


def zone2des(ipazone):
    # next, try to add the fake domain to Designate
    zonename = ipazone['idnsname'][0].rstrip(".") + "."
    email = ipazone['idnssoarname'][0].rstrip(".").replace(".", "@", 1)
    desreq = {"name": zonename,
              "ttl": int(ipazone['idnssoarefresh'][0]),
              "email": email}
    return desreq


def getipadomains(ipabackend, version):
    # get the list of domains/zones from IPA
    ipareq = {'method': 'dnszone_find',
              'params': [[], {'version': version,
                              'all': True}]}
    iparesp = ipabackend._call_and_handle_error(ipareq)
    LOG.debug("Response: %s" % pprint.pformat(iparesp))
    return iparesp['result']['result']


def getiparecords(ipabackend, zonename, version):
    ipareq = {'method': 'dnsrecord_find',
              'params': [[zonename], {"version": version,
                                      "all": True}]}
    iparesp = ipabackend._call_and_handle_error(ipareq)
    return iparesp['result']['result']


def syncipaservers2des(servers, designatereq, designateurl):
    # get existing servers from designate
    dservers = {}
    srvurl = designateurl + "/servers"
    resp = designatereq.get(srvurl)
    LOG.debug("Response: %s" % pprint.pformat(resp.json()))
    if resp and resp.status_code == 200 and resp.json() and \
            'servers' in resp.json():
        for srec in resp.json()['servers']:
            dservers[srec['name']] = srec['id']
    else:
        LOG.warning(_LW("No servers in designate"))

    # first - add servers from ipa not already in designate
    for server in servers:
        if server in dservers:
            LOG.info(_LI("Skipping ipa server %s already in designate"),
                     server)
        else:
            desreq = {"name": server}
            resp = designatereq.post(srvurl, data=json.dumps(desreq))
            LOG.debug("Response: %s" % pprint.pformat(resp.json()))
            if resp.status_code == 200:
                LOG.info(_LI("Added server %s to designate"), server)
            else:
                raise AddServerError("Unable to add %s: %s" %
                                     (server, pprint.pformat(resp.json())))

    # next - delete servers in designate not in ipa
    for server, sid in list(dservers.items()):
        if server not in servers:
            delresp = designatereq.delete(srvurl + "/" + sid)
            if delresp.status_code == 200:
                LOG.info(_LI("Deleted server %s"), server)
            else:
                raise DeleteServerError("Unable to delete %s: %s" %
                                        (server,
                                         pprint.pformat(delresp.json())))


def main():
    # HACK HACK HACK - allow required config params to be passed
    # via the command line
    cfg.CONF['service:api']._group._opts['api_base_uri']['cli'] = True
    for optdict in cfg.CONF['backend:ipa']._group._opts.values():
        if 'cli' in optdict:
            optdict['cli'] = True
    # HACK HACK HACK - allow api url to be passed in the usual way
    utils.read_config('designate', sys.argv)
    if cfg.CONF['service:central'].backend_driver == 'ipa':
        raise CannotUseIPABackend(cuiberrorstr)
    if cfg.CONF.debug:
        LOG.setLevel(logging.DEBUG)
    else:
        LOG.setLevel(logging.INFO)
    ipabackend = impl_ipa.IPABackend(None)
    ipabackend.start()
    version = cfg.CONF['backend:ipa'].ipa_version
    designateurl = cfg.CONF['service:api'].api_base_uri + "v1"

    # get the list of domains/zones from IPA
    ipazones = getipadomains(ipabackend, version)
    # get unique list of name servers
    servers = {}
    for zonerec in ipazones:
        for nsrec in zonerec['nsrecord']:
            servers[nsrec] = nsrec
    if not servers:
        raise NoNameServers("Error: no name servers found in IPA")

    # let's see if designate is using the IPA backend
    # create a fake domain in IPA
    # create a fake server in Designate
    # try to create the same fake domain in Designate
    # if we get a DuplicateZone error from Designate, then
    # raise the CannotUseIPABackend error, after deleting
    # the fake server and fake domain
    # find the first non-reverse zone
    zone = {}
    for zrec in ipazones:
        if not zrec['idnsname'][0].endswith("in-addr.arpa.") and \
                zrec['idnszoneactive'][0] == 'TRUE':
            # ipa returns every data field as a list
            # convert the list to a scalar
            for n, v in list(zrec.items()):
                if n in zoneskips:
                    continue
                if isinstance(v, list):
                    zone[n] = v[0]
                else:
                    zone[n] = v
            break

    assert(zone)

    # create a fake subdomain of this zone
    domname = "%s.%s" % (utils.generate_uuid(), zone['idnsname'])
    args = copy.copy(zone)
    del args['idnsname']
    args['version'] = version
    ipareq = {'method': 'dnszone_add',
              'params': [[domname], args]}
    iparesp = ipabackend._call_and_handle_error(ipareq)
    LOG.debug("Response: %s" % pprint.pformat(iparesp))
    if iparesp['error']:
        raise AddDomainError(pprint.pformat(iparesp))

    # set up designate connection
    designatereq = requests.Session()
    xtra_hdrs = {'Content-Type': 'application/json'}
    designatereq.headers.update(xtra_hdrs)

    # sync ipa name servers to designate
    syncipaservers2des(servers, designatereq, designateurl)

    domainurl = designateurl + "/domains"
    # next, try to add the fake domain to Designate
    email = zone['idnssoarname'].rstrip(".").replace(".", "@", 1)
    desreq = {"name": domname,
              "ttl": int(zone['idnssoarefresh'][0]),
              "email": email}
    resp = designatereq.post(domainurl, data=json.dumps(desreq))
    exc = None
    fakezoneid = None
    if resp.status_code == 200:
        LOG.info(_LI("Added domain %s"), domname)
        fakezoneid = resp.json()['id']
        delresp = designatereq.delete(domainurl + "/" + fakezoneid)
        if delresp.status_code != 200:
            LOG.error(_LE("Unable to delete %(name)s: %(response)s") %
                      {'name': domname, 'response': pprint.pformat(
                          delresp.json())})
    else:
        exc = CannotUseIPABackend(cuiberrorstr)

    # cleanup fake stuff
    ipareq = {'method': 'dnszone_del',
              'params': [[domname], {'version': version}]}
    iparesp = ipabackend._call_and_handle_error(ipareq)
    LOG.debug("Response: %s" % pprint.pformat(iparesp))
    if iparesp['error']:
        LOG.error(_LE("%s") % pprint.pformat(iparesp))

    if exc:
        raise exc

    # get and delete existing domains
    resp = designatereq.get(domainurl)
    LOG.debug("Response: %s" % pprint.pformat(resp.json()))
    if resp and resp.status_code == 200 and resp.json() and \
            'domains' in resp.json():
        # domains must be deleted in child/parent order i.e. delete
        # sub-domains before parent domains - simple way to get this
        # order is to sort the domains in reverse order of name len
        dreclist = sorted(resp.json()['domains'],
                          key=lambda drec: len(drec['name']),
                          reverse=True)
        for drec in dreclist:
            delresp = designatereq.delete(domainurl + "/" + drec['id'])
            if delresp.status_code != 200:
                raise DeleteDomainError("Unable to delete %s: %s" %
                                        (drec['name'],
                                         pprint.pformat(delresp.json())))

    # key is zonename, val is designate rec id
    zonerecs = {}
    for zonerec in ipazones:
        desreq = zone2des(zonerec)
        resp = designatereq.post(domainurl, data=json.dumps(desreq))
        if resp.status_code == 200:
            LOG.info(_LI("Added domain %s"), desreq['name'])
        else:
            raise AddDomainError("Unable to add domain %s: %s" %
                                 (desreq['name'], pprint.pformat(resp.json())))
        zonerecs[desreq['name']] = resp.json()['id']

    # get the records for each zone
    for zonename, domainid in list(zonerecs.items()):
        recurl = designateurl + "/domains/" + domainid + "/records"
        iparecs = getiparecords(ipabackend, zonename, version)
        for rec in iparecs:
            desreqs = rec2des(rec, zonename)
            for desreq in desreqs:
                resp = designatereq.post(recurl, data=json.dumps(desreq))
                if resp.status_code == 200:
                    LOG.info(_LI("Added record %(record)s "
                                 "for domain %(domain)s"),
                             {'record': desreq['name'], 'domain': zonename})
                else:
                    raise AddRecordError("Could not add record %s: %s" %
                                         (desreq['name'],
                                          pprint.pformat(resp.json())))

if __name__ == '__main__':
    sys.exit(main())
