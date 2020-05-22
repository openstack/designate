# Copyright 2018 Cloudification GmbH.
#
# Author: Dmitry Galkin <contact@cloudification.io>
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

"""
F5 DNS Express backend.
Create and delete zones on F5 Load Balancer via iControl API.
"""
import json
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import Timeout
from netaddr import IPNetwork
from oslo_log import log as logging

from designate.backend import base

LOG = logging.getLogger(__name__)


class F5Backend(base.Backend):
    __plugin_name__ = 'f5'

    def __init__(self, target):
        super(F5Backend, self).__init__(target)

        self._host = self.options.get('host', '127.0.0.1')
        self._port = int(self.options.get('port', 53))
        self._auth = HTTPBasicAuth(self.options.get('icontrol_user', 'admin'),
                                   self.options.get('icontrol_pass', 'admin'))

        self._f5_hosts = self.options.get('icontrol_hosts', '127.0.0.1')
        self._express_srv = self.options.get('express_srv', 'designate-mdns')
        self._partition = self.options.get('partition', 'Common')
        self._notify_subnet = self.options.get('notify_subnet', '')
        self._notify_tsig_verify = self.options.get('notify_tsig_verify', 'no')

    def _generate_icontrol_base_request(self, method, http_url, data,
                                        failover=False):
        """
        Prepare a request for iControl API.
        Will use the second F5 device from the icontrol_hosts list
        if failover is True.
        """
        f5_hosts = self._f5_hosts.split(',')
        f5_port = int(self.options.get('icontrol_port', 443))

        if len(f5_hosts) > 1 and failover:
            f5_host = f5_hosts[1].strip()
        else:
            f5_host = f5_hosts[0].strip()

        base_url = "https://%s:%s/" % (f5_host, f5_port)
        url = base_url + http_url

        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}

        f5_request = requests.Request(method, url,
                                      data=json.dumps(data),
                                      auth=self._auth,
                                      headers=headers)
        return f5_request.prepare()

    def create_zone(self, context, zone):
        """
        Create a new Zone by executing iControl API, then notify mDNS
        Do not raise exceptions if the zone already exists.
        """
        LOG.debug('Creating Zone %s on F5' % zone)

        # the master 'self._express_srv' should already exist on F5
        # there is no option to create a zone with multiple masters

        url = 'mgmt/tm/ltm/dns/zone/'

        # zone name without . in the end
        data = {'name': zone['name'].rstrip('.'),
                'dnsExpressServer': self._express_srv,
                'dnsExpressNotifyTsigVerify': self._notify_tsig_verify,
                'partition': self._partition}

        if self._notify_subnet:
            # have to specify each IP from subnet, as F5 only accepts IPs
            allowed_ips = []
            for ip in IPNetwork(self._notify_subnet):
                allowed_ips.append(str(ip))

            data['dnsExpressAllowNotify'] = allowed_ips

        try:
            self._execute_call(method='POST', url=url, data=data)
        except (ConnectionError, HTTPError) as exc:
            LOG.debug('F5: an Error occured while creating a zone: %s', exc)

        self.mdns_api.notify_zone_changed(
            context, zone, self._host, self._port, self.timeout,
            self.retry_interval, self.max_retries, self.delay)

    def delete_zone(self, context, zone):
        """
        Delete a new Zone by calling iControl API
        Do not raise exceptions if the zone does not exist.
        """
        LOG.debug('Deleting Zone %s on F5' % zone)
        zone_name = zone['name'].rstrip('.')  # no . in the end for F5

        url = 'mgmt/tm/ltm/dns/zone/~' + self._partition + '~' + zone_name

        try:
            self._execute_call(method='DELETE', url=url, data={})
        except (ConnectionError, HTTPError) as exc:
            LOG.debug('F5: an Error occured while deleting a zone: %s', exc)

    def _execute_call(self, **kwargs):
        """
        Execute iControl via HTTP

        :param icontrol_op: iControl arguments
        :type icontrol_op: list
        :returns: None
        """
        LOG.debug('F5: preparing %s request with data %s' % (kwargs['method'],
                                                             kwargs['data']))
        with requests.Session() as sess:
            f5_req = self._generate_icontrol_base_request(kwargs['method'],
                                                          kwargs['url'],
                                                          kwargs['data'])
            try:
                LOG.debug('F5: executing iControl request: %s', f5_req.url)
                resp = sess.send(f5_req, verify=False, timeout=20)
            except (Timeout, ConnectionError) as exc:
                LOG.error('F5: an Error occured during request: %s', exc)
                LOG.debug('F5: attempting to send request to second device')
                f5_req = self._generate_icontrol_base_request(kwargs['method'],
                                                              kwargs['url'],
                                                              kwargs['data'],
                                                              failover=True)
                LOG.debug('F5: executing iControl request: %s', f5_req.url)
                resp = sess.send(f5_req, verify=False, timeout=20)

            if resp:
                LOG.debug('F5: got iControl response: %s', resp.text)
