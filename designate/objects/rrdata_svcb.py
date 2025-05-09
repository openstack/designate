# Copyright 2025 Cloudification GmbH
#
# Author: cloudification <contact@cloudification.io>
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

import base64
import dns.exception

from dns import ipv4
from dns import ipv6

from designate.objects import base
from designate.objects import fields
from designate.objects.record import Record
from designate.objects.record import RecordList


def validate_alpn(alpn_string, params):
    """
    h2 means HTTP/2 over TLS, h3 means HTTP/3
    or QUIC (for example, "alpn"="h2").
    """
    valid_values = ("h3", "h2", "h2c", "http/1.1", "http/1.0")
    values = alpn_string.split(",")
    for value in values:
        if value not in valid_values:
            raise ValueError(f"{value} is not supported."
                             f"Supported values {valid_values}")


def validate_ipv4hint(ipv4hint):
    # Should be list of ipv4 comma separated
    for value in ipv4hint.split(","):
        try:
            ipv4.inet_aton(str(value))
        except dns.exception.SyntaxError:
            raise ValueError(f"Value {value} is not ipv4 address")


def validate_ipv6hint(ipv6hint):
    # Should be list of ipv6 comma separated
    for value in ipv6hint.split(","):
        try:
            ipv6.inet_aton(str(value))
        except dns.exception.SyntaxError:
            raise ValueError(f"Value {value} is not ipv6 address")


def validate_ech(ech):
    if "\\" in ech:
        raise ValueError("escape in ECH value")
    try:
        base64.b64decode(ech)
    except Exception:
        raise ValueError("ECH value is not base64 string")


def validate_port(port):
    if not port.isnumeric():
        raise ValueError('Port is not an integer')


def validate_mandatory(mandatory_params, all_params):
    values = mandatory_params.split(",")
    if not set(values).issubset(
            all_params.keys()
    ) or len(values) > len(all_params):
        raise ValueError(
            f"Record should have all mandatory params."
            f"Mandatory params: {values}."
            f"All params: {all_params}")


def validate_doh(doh):
    if not doh.startswith("/"):
        raise ValueError("dohpath must be relative")
    if len(doh) < 7:
        raise ValueError("Minimal valid dohpath length 7")
    if "{?dns}" not in doh:
        raise ValueError("dohpath MUST contain '{?dns}'")


@base.DesignateRegistry.register
class SVCB(Record):
    """
    General-purpose service binding record type
    Defined in: RFC9460
    """

    params = ["alpn", "ipv4hint", "ipv6hint",
              "port", "ech", "no-default-alpn",
              "mandatory", "dohpath"]

    svcb_params = {"alpn": validate_alpn,
                   "ipv4hint": validate_ipv4hint,
                   "ipv6hint": validate_ipv6hint,
                   "port": validate_port,
                   "ech": validate_ech,
                   "mandatory": validate_mandatory,
                   'dohpath': validate_doh,
                   }

    fields = {
        'priority': fields.IntegerFields(minimum=0, maximum=65535),
        'target': fields.DomainField(maxLength=255),
        'alpn': fields.StringFields(maxLength=255, nullable=True),
        'ech': fields.StringFields(maxLength=255, nullable=True),
        'ipv4hint': fields.StringFields(maxLength=255, nullable=True),
        'ipv6hint': fields.StringFields(maxLength=255, nullable=True),
        'port': fields.StringFields(nullable=True, maxLength=10),
        'no_default_alpn': fields.BooleanField(nullable=True, default=False),
        'mandatory': fields.StringFields(nullable=True, maxLength=255),
        'dohpath': fields.StringFields(nullable=True, maxLength=255)
    }

    def from_string(self, value):
        values = value.split(' ')
        priority, target = values[:2]

        def _svcbparams_to_dict(params):
            result = {}
            for param in params:
                if param == 'no-default-alpn':
                    result[param] = True
                    continue
                if "=" not in param:
                    raise ValueError(f"Missed '=' in value {param}")

                svc_param = param.split("=")
                if len(svc_param[1:]) > 1:
                    if param.startswith("ech"):
                        echstr = []
                        for el in svc_param[1:]:
                            if not el:
                                el = "="
                            echstr.append(el)
                        result[svc_param[0]] = "".join(echstr)
                else:
                    result[svc_param[0]] = svc_param[1]
            return result

        svcbparams = _svcbparams_to_dict(values[2:])
        for param_name, param_value in svcbparams.items():
            if param_name not in self.params:
                raise ValueError(f"Unsupported param {param_name}")
            if param_name == 'no-default-alpn':
                if "alpn" in svcbparams.keys():
                    self.no_default_alpn = True
                    continue
                else:
                    raise ValueError("ALPN should be presented"
                                     " if no-default-alpn param exist")
            else:
                if param_name in ("alpn", "mandatory"):
                    self.svcb_params[param_name](param_value, svcbparams)
                else:
                    self.svcb_params[param_name](param_value)
                if param_name == "alpn":
                    self.alpn = "=".join([param_name, param_value])
                elif param_name == "port":
                    self.port = "=".join([param_name, param_value])
                elif param_name == "ipv4hint":
                    self.ipv4hint = "=".join([param_name, param_value])
                elif param_name == "ipv6hint":
                    self.ipv6hint = "=".join([param_name, param_value])
                elif param_name == "mandatory":
                    self.mandatory = "=".join([param_name, param_value])
                elif param_name == "ech":
                    self.ech = "=".join(["ech", param_value])
                elif param_name == 'dohpath':
                    self.dohpath = "=".join([param_name, param_value])

        try:
            self.priority = int(priority)
        except ValueError:
            raise ValueError('Value priority is not an integer')
        self.target = target

    # The record type is defined in the RFC. This will be used when the record
    # is sent by mini-dns.
    RECORD_TYPE = 64


@base.DesignateRegistry.register
class SVCBList(RecordList):

    LIST_ITEM_TYPE = SVCB

    fields = {
        'objects': fields.ListOfObjectsField('SVCB'),
    }
