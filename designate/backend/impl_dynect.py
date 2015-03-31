# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
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
import json
import time

from eventlet import Timeout
from oslo.config import cfg
from oslo_log import log as logging
import requests
from requests.adapters import HTTPAdapter

from designate import exceptions
from designate import utils
from designate.backend import base
from designate.i18n import _LI
from designate.i18n import _LW


LOG = logging.getLogger(__name__)
CONF = cfg.CONF
CFG_GROUP = 'backend:dynect'


class DynClientError(exceptions.Backend):
    """The base exception class for all HTTP exceptions.
    """
    def __init__(self, data=None, job_id=None, msgs=None,
                 http_status=None, url=None, method=None, details=None):
        self.data = data
        self.job_id = job_id
        self.msgs = msgs

        self.http_status = http_status
        self.url = url
        self.method = method
        self.details = details
        formatted_string = "%s (HTTP %s to %s - %s) - %s" % (self.msgs,
                                                             self.method,
                                                             self.url,
                                                             self.http_status,
                                                             self.details)
        if job_id:
            formatted_string += " (Job-ID: %s)" % job_id
        super(DynClientError, self).__init__(formatted_string)

    @staticmethod
    def from_response(response, details=None):
        data = response.json()

        exc_kwargs = dict(
            data=data['data'],
            job_id=data['job_id'],
            msgs=data['msgs'],
            http_status=response.status_code,
            url=response.url,
            method=response.request.method,
            details=details)

        for msg in data.get('msgs', []):
            if msg['INFO'].startswith('login:'):
                raise DynClientAuthError(**exc_kwargs)
            elif 'Operation blocked' in msg['INFO']:
                raise DynClientOperationBlocked(**exc_kwargs)
        return DynClientError(**exc_kwargs)


class DynClientAuthError(DynClientError):
    pass


class DynTimeoutError(exceptions.Backend):
    """
    A job timedout.
    """
    error_code = 408
    error_type = 'dyn_timeout'


class DynClientOperationBlocked(exceptions.BadRequest, DynClientError):
    error_type = 'operation_blocked'


class DynClient(object):
    """
    DynECT service client.

    https://help.dynect.net/rest/
    """
    def __init__(self, customer_name, user_name, password,
                 endpoint="https://api.dynect.net:443",
                 api_version='3.5.6', headers=None, verify=True, retries=1,
                 timeout=10, timings=False, pool_maxsize=10,
                 pool_connections=10):
        self.customer_name = customer_name
        self.user_name = user_name
        self.password = password
        self.endpoint = endpoint
        self.api_version = api_version

        self.times = []  # [("item", starttime, endtime), ...]
        self.timings = timings
        self.timeout = timeout

        self.authing = False
        self.token = None

        session = requests.Session()
        session.verify = verify

        session.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'API-Version': api_version,
            'User-Agent': 'DynECTClient'}

        if headers is not None:
            session.headers.update(headers)

        adapter = HTTPAdapter(max_retries=int(retries),
                              pool_maxsize=int(pool_maxsize),
                              pool_connections=int(pool_connections),
                              pool_block=True)
        session.mount(endpoint, adapter)
        self.http = session

    def _http_log_req(self, method, url, kwargs):
        string_parts = [
            "curl -i",
            "-X '%s'" % method,
            "'%s'" % url,
        ]

        for element in kwargs['headers']:
            header = "-H '%s: %s'" % (element, kwargs['headers'][element])
            string_parts.append(header)

        LOG.debug("REQ: %s" % " ".join(string_parts))
        if 'data' in kwargs:
            LOG.debug("REQ BODY: %s\n" % (kwargs['data']))

    def _http_log_resp(self, resp):
        LOG.debug(
            "RESP: [%s] %s\n" %
            (resp.status_code,
             resp.headers))
        if resp._content_consumed:
            LOG.debug(
                "RESP BODY: %s\n" %
                resp.text)

    def get_timings(self):
        return self.times

    def reset_timings(self):
        self.times = []

    def _request(self, method, url, **kwargs):
        """
        Low level request helper that actually executes the request towards a
        wanted URL.

        This does NOT do any authentication.
        """
        # NOTE: Allow passing the url as just the path or a full url
        if not url.startswith('http'):
            if not url.startswith('/REST'):
                url = '/REST' + url
            url = self.endpoint + url

        kwargs.setdefault("headers", kwargs.get("headers", {}))
        kwargs['proxies'] = utils.get_proxies()

        if self.token is not None:
            kwargs['headers']['Auth-Token'] = self.token
        if self.timeout is not None:
            kwargs.setdefault("timeout", self.timeout)

        data = kwargs.get('data')
        if data is not None:
            kwargs['data'] = data.copy()

            # NOTE: We don't want to log the credentials (password) that are
            # used in a auth request.
            if 'password' in kwargs['data']:
                kwargs['data']['password'] = '**SECRET**'

            self._http_log_req(method, url, kwargs)

            # NOTE: Set it back to the original data and serialize it.
            kwargs['data'] = json.dumps(data)
        else:
            self._http_log_req(method, url, kwargs)

        if self.timings:
            start_time = time.time()
        resp = self.http.request(method, url, **kwargs)
        if self.timings:
            self.times.append(("%s %s" % (method, url),
                               start_time, time.time()))
        self._http_log_resp(resp)

        if resp.status_code >= 400:
            LOG.debug(
                "Request returned failure status: %s" %
                resp.status_code)
            raise DynClientError.from_response(resp)
        return resp

    def poll_response(self, response):
        """
        The API might return a job nr in the response in case of a async
        response: https://github.com/fog/fog/issues/575
        """
        status = response.status

        timeout = Timeout(CONF[CFG_GROUP].job_timeout)
        try:
            while status == 307:
                time.sleep(1)
                url = response.headers.get('Location')
                LOG.debug("Polling %s" % url)

                polled_response = self.get(url)
                status = response.status
        except Timeout as t:
            if t == timeout:
                raise DynTimeoutError('Timeout reached when pulling job.')
        finally:
            timeout.cancel()
        return polled_response

    def request(self, method, url, retries=2, **kwargs):
        if self.token is None and not self.authing:
            self.login()

        try:
            response = self._request(method, url, **kwargs)
        except DynClientAuthError:
            if retries > 0:
                self.token = None
                retries = retries - 1
                return self.request(method, url, retries, **kwargs)
            else:
                raise

        if response.status_code == 307:
            response = self.poll_response(response)

        return response.json()

    def login(self):
        self.authing = True
        data = {
            'customer_name': self.customer_name,
            'user_name': self.user_name,
            'password': self.password
        }
        response = self.post('/Session', data=data)
        self.token = response['data']['token']
        self.authing = False

    def logout(self):
        self.delete('/Session')
        self.token = None

    def post(self, *args, **kwargs):
        response = self.request('POST', *args, **kwargs)
        return response

    def get(self, *args, **kwargs):
        response = self.request('GET', *args, **kwargs)
        return response

    def put(self, *args, **kwargs):
        response = self.request('PUT', *args, **kwargs)
        return response

    def patch(self, *args, **kwargs):
        response = self.request('PATCH', *args, **kwargs)
        return response

    def delete(self, *args, **kwargs):
        response = self.request('DELETE', *args, **kwargs)
        return response


class DynECTBackend(base.Backend):
    """
    Support for DynECT as a secondary DNS.
    """
    __plugin_name__ = 'dynect'

    @classmethod
    def get_cfg_opts(cls):
        group = cfg.OptGroup(
            name=CFG_GROUP, title='Backend options for DynECT'
        )

        opts = [
            cfg.IntOpt('job_timeout', default=30,
                       help="Timeout in seconds for pulling a job in DynECT."),
            cfg.IntOpt('timeout', help="Timeout in seconds for API Requests.",
                       default=10),
            cfg.BoolOpt('timings', help="Measure requests timings.",
                        default=False),
        ]

        return [(group, opts)]

    def __init__(self, target):
        super(DynECTBackend, self).__init__(target)

        self.customer_name = self.options.get('customer_name')
        self.username = self.options.get('username')
        self.password = self.options.get('password')
        self.contact_nickname = self.options.get('contact_nickname', None)
        self.tsig_key_name = self.options.get('tsig_key_name', None)

        for m in self.masters:
            if m.port != 53:
                raise exceptions.ConfigurationError(
                    "DynECT only supports mDNS instances on port 53")

    def get_client(self):
        return DynClient(
            customer_name=self.customer_name,
            user_name=self.username,
            password=self.password,
            timeout=CONF[CFG_GROUP].timeout,
            timings=CONF[CFG_GROUP].timings)

    def create_domain(self, context, domain):
        LOG.info(_LI('Creating domain %(d_id)s / %(d_name)s') %
                 {'d_id': domain['id'], 'd_name': domain['name']})

        url = '/Secondary/%s' % domain['name'].rstrip('.')
        data = {
            'masters': [m.host for m in self.masters]
        }

        if self.contact_nickname is not None:
            data['contact_nickname'] = self.contact_nickname

        if self.tsig_key_name is not None:
            data['tsig_key_name'] = self.tsig_key_name

        client = self.get_client()

        try:
            client.post(url, data=data)
        except DynClientError as e:
            for emsg in e.msgs:
                if emsg['ERR_CD'] == 'TARGET_EXISTS':
                    msg = _LI("Domain already exists, updating existing "
                              "domain instead %s")
                    LOG.info(msg % domain['name'])
                    client.put(url, data=data)
                    break
            else:
                raise e

        client.put(url, data={'activate': True})
        client.logout()

    def update_domain(self, context, domain):
        LOG.debug('Discarding update_domain call, not-applicable')

    def delete_domain(self, context, domain):
        LOG.info(_LI('Deleting domain %(d_id)s / %(d_name)s') %
                 {'d_id': domain['id'], 'd_name': domain['name']})
        url = '/Zone/%s' % domain['name'].rstrip('.')
        client = self.get_client()
        try:
            client.delete(url)
        except DynClientError as e:
            if e.http_status == 404:
                LOG.warn(_LW("Attempt to delete %(d_id)s / %(d_name)s "
                             "caused 404, ignoring.") %
                         {'d_id': domain['id'], 'd_name': domain['name']})
                pass
            else:
                raise
        client.logout()

    def create_recordset(self, context, domain, recordset):
        LOG.debug('Discarding create_recordset call, not-applicable')

    def update_recordset(self, context, domain, recordset):
        LOG.debug('Discarding update_recordset call, not-applicable')

    def delete_recordset(self, context, domain, recordset):
        LOG.debug('Discarding delete_recordset call, not-applicable')

    def create_record(self, context, domain, recordset, record):
        LOG.debug('Discarding create_record call, not-applicable')

    def update_record(self, context, domain, recordset, record):
        LOG.debug('Discarding update_record call, not-applicable')

    def delete_record(self, context, domain, recordset, record):
        LOG.debug('Discarding delete_record call, not-applicable')
