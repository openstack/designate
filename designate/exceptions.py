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
        self.object = kwargs.pop('object', None)

        super(Base, self).__init__(*args, **kwargs)

        if len(args) > 0 and isinstance(args[0], basestring):
            self.error_message = args[0]


class Backend(Exception):
    pass


class RelationNotLoaded(Base):
    error_code = 500
    error_type = 'relation_not_loaded'


class AdapterNotFound(Base):
    error_code = 500
    error_type = 'adapter_not_found'


class NSD4SlaveBackendError(Backend):
    pass


class NotImplemented(Base, NotImplementedError):
    pass


class XFRFailure(Base):
    pass


class ConfigurationError(Base):
    error_type = 'configuration_error'


class UnknownFailure(Base):
    error_code = 500
    error_type = 'unknown_failure'


class CommunicationFailure(Base):
    error_code = 504
    error_type = 'communication_failure'


class NeutronCommunicationFailure(CommunicationFailure):
    """
    Raised in case one of the alleged Neutron endpoints fails.
    """
    error_type = 'neutron_communication_failure'


class NoServersConfigured(ConfigurationError):
    error_code = 500
    error_type = 'no_servers_configured'


class NoPoolTargetsConfigured(ConfigurationError):
    error_code = 500
    error_type = 'no_pool_targets_configured'


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


class InvalidUUID(BadRequest):
    error_type = 'invalid_uuid'


class NetworkEndpointNotFound(BadRequest):
    error_type = 'no_endpoint'
    error_code = 403


class MarkerNotFound(BadRequest):
    error_type = 'marker_not_found'


class ValueError(BadRequest):
    error_type = 'value_error'


class InvalidMarker(BadRequest):
    error_type = 'invalid_marker'


class InvalidSortDir(BadRequest):
    error_type = 'invalid_sort_dir'


class InvalidLimit(BadRequest):
    error_type = 'invalid_limit'


class InvalidSortKey(BadRequest):
    error_type = 'invalid_sort_key'


class InvalidJson(BadRequest):
    error_type = 'invalid_json'


class InvalidOperation(BadRequest):
    error_code = 400
    error_type = 'invalid_operation'


class UnsupportedAccept(BadRequest):
    error_code = 406
    error_type = 'unsupported_accept'


class UnsupportedContentType(BadRequest):
    error_code = 415
    error_type = 'unsupported_content_type'


class InvalidDomainName(Base):
    error_code = 400
    error_type = 'invalid_domain_name'


class InvalidRecordSetName(Base):
    error_code = 400
    error_type = 'invalid_recordset_name'


class InvalidRecordSetLocation(Base):
    error_code = 400
    error_type = 'invalid_recordset_location'


class InvaildZoneTransfer(Base):
    error_code = 400
    error_type = 'invalid_zone_transfer_request'


class InvalidTTL(Base):
    error_code = 400
    error_type = 'invalid_ttl'


class DomainHasSubdomain(Base):
    error_code = 400
    error_type = 'domain_has_subdomain'


class Forbidden(Base):
    error_code = 403
    error_type = 'forbidden'
    expected = True


class IncorrectZoneTransferKey(Forbidden):
    error_type = 'invalid_key'


class Duplicate(Base):
    expected = True
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


class DuplicateTld(Duplicate):
    error_type = 'duplicate_tld'


class DuplicateRecordSet(Duplicate):
    error_type = 'duplicate_recordset'


class DuplicateRecord(Duplicate):
    error_type = 'duplicate_record'


class DuplicateBlacklist(Duplicate):
    error_type = 'duplicate_blacklist'


class DuplicatePoolManagerStatus(Duplicate):
    error_type = 'duplication_pool_manager_status'


class DuplicatePool(Duplicate):
    error_type = 'duplicate_pool'


class DuplicatePoolAttribute(Duplicate):
    error_type = 'duplicate_pool_attribute'


class DuplicateDomainAttribute(Duplicate):
    error_type = 'duplicate_domain_attribute'


class DuplicatePoolNsRecord(Duplicate):
    error_type = 'duplicate_pool_ns_record'


class MethodNotAllowed(Base):
    expected = True
    error_code = 405
    error_type = 'method_not_allowed'


class DuplicateZoneTransferRequest(Duplicate):
    error_type = 'duplicate_zone_transfer_request'


class DuplicateZoneTransferAccept(Duplicate):
    error_type = 'duplicate_zone_transfer_accept'


class NotFound(Base):
    expected = True
    error_code = 404
    error_type = 'not_found'


class QuotaNotFound(NotFound):
    error_type = 'quota_not_found'


class ServerNotFound(NotFound):
    error_type = 'server_not_found'


class TsigKeyNotFound(NotFound):
    error_type = 'tsigkey_not_found'


class BlacklistNotFound(NotFound):
    error_type = 'blacklist_not_found'


class DomainNotFound(NotFound):
    error_type = 'domain_not_found'


class DomainAttributeNotFound(NotFound):
    error_type = 'domain_attribute_not_found'


class TldNotFound(NotFound):
    error_type = 'tld_not_found'


class RecordSetNotFound(NotFound):
    error_type = 'recordset_not_found'


class RecordNotFound(NotFound):
    error_type = 'record_not_found'


class ReportNotFound(NotFound):
    error_type = 'report_not_found'


class PoolManagerStatusNotFound(NotFound):
    error_type = 'pool_manager_status_not_found'


class PoolNotFound(NotFound):
    error_type = 'pool_not_found'


class PoolAttributeNotFound(NotFound):
    error_type = 'pool_attribute_not_found'


class PoolNsRecordNotFound(NotFound):
    error_type = 'pool_ns_record_not_found'


class ZoneTransferRequestNotFound(NotFound):
    error_type = 'zone_transfer_request_not_found'


class ZoneTransferAcceptNotFound(NotFound):
    error_type = 'zone_transfer_accept_not_found'


class LastServerDeleteNotAllowed(BadRequest):
    error_type = 'last_server_delete_not_allowed'


class ResourceNotFound(NotFound):
    # TODO(kiall): Should this be extending NotFound??
    pass
