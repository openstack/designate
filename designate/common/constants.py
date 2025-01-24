# Copyright 2021 Red Hat
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import re

# API constants
API_REF_URL = 'https://docs.openstack.org/api-ref/dns'
CURRENT = 'CURRENT'
SUPPORTED = 'SUPPORTED'
DEPRECATED = 'DEPRECATED'
EXPERIMENTAL = 'EXPERIMENTAL'

# RBAC related constants
RBAC_PROJECT_ID = 'project_id'
RBAC_TARGET_PROJECT_ID = 'target_project_id'

# Statuses
ACTIVE = 'ACTIVE'
ERROR = 'ERROR'
INACTIVE = 'INACTIVE'
PENDING = 'PENDING'

# Actions
CREATE = 'CREATE'
DELETE = 'DELETE'
NONE = 'NONE'
UPDATE = 'UPDATE'

# Floating IP constants
FLOATING_IP_ACTIONS = [CREATE, DELETE, UPDATE, NONE]
FLOATING_IP_STATUSES = [ACTIVE, ERROR, INACTIVE, PENDING]

# Quotas
MIN_QUOTA = -1
MAX_QUOTA = 2147483647
QUOTA_API_EXPORT_SIZE = 'api_export_size'
QUOTA_RECORDSET_RECORDS = 'recordset_records'
QUOTA_ZONE_RECORDS = 'zone_records'
QUOTA_ZONE_RECORDSETS = 'zone_recordsets'
QUOTA_ZONES = 'zones'
VALID_QUOTAS = [QUOTA_API_EXPORT_SIZE, QUOTA_RECORDSET_RECORDS,
                QUOTA_ZONE_RECORDS, QUOTA_ZONE_RECORDSETS, QUOTA_ZONES]

# RBAC scopes
PROJECT = 'project'

# Zone constants
ZONE_PRIMARY = 'PRIMARY'
ZONE_SECONDARY = 'SECONDARY'
ZONE_CATALOG = 'CATALOG'
ZONE_TYPES = [ZONE_PRIMARY, ZONE_SECONDARY, ZONE_CATALOG]

# Record regexes
RE_HOSTNAME = re.compile(r'^(?!.{255,})(?:(?:^\*|(?!\-)[A-Za-z0-9_\-]{1,63})(?<!\-)\.)+\Z')  # noqa
RE_ZONENAME = re.compile(r'^(?!.{255,})(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)\.)+\Z')  # noqa
RE_SRV_HOST_NAME = re.compile(r'^(?:(?!\-)(?:\_[A-Za-z0-9_\-]{1,63}\.){2})(?!.{255,})(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)\.)+\Z')  # noqa
RE_SSHFP_FINGERPRINT = re.compile(r'^([0-9A-Fa-f]{10,40}|[0-9A-Fa-f]{64})\Z')
RE_TLDNAME = re.compile(r'^(?!.{255,})(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-))(?:\.(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)))*\Z')  # noqa
RE_NAPTR_FLAGS = re.compile(r'^[APSUapsu]*$')
RE_NAPTR_SERVICE = re.compile(r'^([A-Za-z]([A-Za-z0-9]*)(\+[A-Za-z]([A-Za-z0-9]{0,31}))*)?$')  # noqa
RE_NAPTR_REGEXP = re.compile(r'^(([^0-9i\\])(.*)\2((.+)|(\\[1-9]))?\2(i?))?$')
RE_KVP = re.compile(r'^\s[A-Za-z0-9]+=[A-Za-z0-9]+')
RE_URL_MAIL = re.compile(r'^mailto:[A-Za-z0-9_\-]+(\+[A-Za-z0-9_\-]+)?@.*')
RE_URL_HTTP = re.compile(r'^http(s)?://.*/')
RE_CERT_TYPE = re.compile(r'(^[A-Z]+$)|(^[0-9]+$)')
RE_CERT_ALGO = re.compile(r'(^[A-Z]+[A-Z0-9\-]+[A-Z0-9]$)|(^[0-9]+$)')

# Floating IP regexes
RE_FIP = re.compile(r'^(?P<region>[A-Za-z0-9\.\-_]{1,100}):(?P<id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$')  # noqa

# Error Validation regexes
RE_REQUIRED = re.compile(r'\'([\w]*)\' is a required property')

TSIG_ALGORITHMS = [
                'hmac-md5',
                'hmac-sha1',
                'hmac-sha224',
                'hmac-sha256',
                'hmac-sha384',
                'hmac-sha512'
            ]
