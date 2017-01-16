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
import os
import logging

from requests import auth
import kerberos

from designate.utils import generate_uuid
from designate.backend.impl_ipa import IPAAuthError
from designate.i18n import _LW
from designate.i18n import _LE


LOG = logging.getLogger(__name__)


class IPAAuth(auth.AuthBase):
    def __init__(self, keytab, hostname):
        # store the kerberos credentials in memory rather than on disk
        os.environ['KRB5CCNAME'] = "MEMORY:" + generate_uuid()
        self.token = None
        self.keytab = keytab
        self.hostname = hostname
        if self.keytab:
            os.environ['KRB5_CLIENT_KTNAME'] = self.keytab
        else:
            LOG.warning(_LW('No IPA client kerberos keytab file given'))

    def __call__(self, request):
        if not self.token:
            self.refresh_auth()
        request.headers['Authorization'] = 'negotiate ' + self.token
        return request

    def refresh_auth(self):
        service = "HTTP@" + self.hostname
        flags = kerberos.GSS_C_MUTUAL_FLAG | kerberos.GSS_C_SEQUENCE_FLAG
        try:
            (_, vc) = kerberos.authGSSClientInit(service, flags)
        except kerberos.GSSError as e:
            LOG.error(_LE("caught kerberos exception %r") % e)
            raise IPAAuthError(str(e))
        try:
            kerberos.authGSSClientStep(vc, "")
        except kerberos.GSSError as e:
            LOG.error(_LE("caught kerberos exception %r") % e)
            raise IPAAuthError(str(e))
        self.token = kerberos.authGSSClientResponse(vc)
