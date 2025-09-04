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


from designate.objects import base
from designate.objects import fields
from designate.objects.record import RecordList
from designate.objects import rrdata_svcb


@base.DesignateRegistry.register
class HTTPS(rrdata_svcb.SVCB):
    """
    SVCB-compatible type for use with HTTPS
    Defined in: RFC9460
    """

    params = ["alpn", "ipv4hint", "ipv6hint",
              "port", "ech", "no-default-alpn",
              "mandatory"]

    svcb_params = {"alpn": rrdata_svcb.validate_alpn,
                   "ipv4hint": rrdata_svcb.validate_ipv4hint,
                   "ipv6hint": rrdata_svcb.validate_ipv6hint,
                   "port": rrdata_svcb.validate_port,
                   "ech": rrdata_svcb.validate_ech,
                   "mandatory": rrdata_svcb.validate_mandatory,
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

        try:
            self.priority = int(priority)
        except ValueError:
            raise ValueError('Value priority is not an integer')
        self.target = target

    RECORD_TYPE = 65


@base.DesignateRegistry.register
class HTTPSList(RecordList):

    LIST_ITEM_TYPE = HTTPS

    fields = {
        'objects': fields.ListOfObjectsField('HTTPS'),
    }
