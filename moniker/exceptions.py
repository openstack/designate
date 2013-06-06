# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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


class Base(Exception):
    error_code = 500
    error_type = None
    error_message = None
    errors = None

    def __init__(self, *args, **kwargs):
        self.errors = kwargs.pop('errors', None)

        super(Base, self).__init__(*args, **kwargs)

        if len(args) > 0 and isinstance(args[0], basestring):
            self.error_message = args[0]


class Backend(Exception):
    pass


class NotImplemented(Base, NotImplementedError):
    pass


class ConfigurationError(Base):
    error_type = 'configuration_error'


class NoServersConfigured(ConfigurationError):
    pass


class OverQuota(Base):
    error_code = 413
    error_type = 'over_quota'


class QuotaResourceUnknown(Base):
    error_type = 'quota_resource_unknown'


class InvalidObject(Base):
    error_code = 400
    error_type = 'invalid_object'


class BadRequest(Base):
    error_code = 400
    error_type = 'bad_request'


class InvalidDomainName(Base):
    error_code = 400
    error_type = 'invalid_domain_name'


class InvalidRecordName(Base):
    error_code = 400
    error_type = 'invalid_record_name'


class InvalidRecordLocation(Base):
    error_code = 400
    error_type = 'invalid_record_location'


class DomainHasSubdomain(Base):
    error_code = 400
    error_type = 'domain_has_subdomain'


class Forbidden(Base):
    error_code = 403
    error_type = 'forbidden'


class Duplicate(Base):
    error_code = 409
    error_type = 'duplicate'


class DuplicateQuota(Duplicate):
    error_type = 'duplicate_quota'


class DuplicateServer(Duplicate):
    error_type = 'duplicate_server'


class DuplicateTsigKey(Duplicate):
    error_type = 'duplicate_tsigkey'


class DuplicateDomain(Duplicate):
    error_type = 'duplicate_domain'


class DuplicateRecord(Duplicate):
    error_type = 'duplicate_record'


class NotFound(Base):
    error_code = 404
    error_type = 'not_found'


class QuotaNotFound(NotFound):
    error_type = 'quota_not_found'


class ServerNotFound(NotFound):
    error_type = 'server_not_found'


class TsigKeyNotFound(NotFound):
    error_type = 'tsigkey_not_found'


class DomainNotFound(NotFound):
    error_type = 'domain_not_found'


class RecordNotFound(NotFound):
    error_type = 'record_not_found'


class ResourceNotFound(NotFound):
    # TODO(kiall): Should this be extending NotFound??
    pass
