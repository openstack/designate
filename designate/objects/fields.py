# Copyright 2015 Red Hat, Inc.
# Copyright 2017 Fujitsu Vietnam Ltd.
# All Rights Reserved.
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
import dns.exception
from dns import ipv4
import re
import uuid

from oslo_versionedobjects import fields as ovoo_fields

from designate.common import constants


class IntegerField(ovoo_fields.IntegerField):
    pass


class BooleanField(ovoo_fields.BooleanField):
    pass


class PolymorphicObject(ovoo_fields.Object):
    def coerce(self, obj, attr, value):
        if hasattr(value, '__bases__'):
            check_value = value.__bases__[0]
            super().coerce(obj, attr, check_value)
        return value


class PolymorphicObjectField(ovoo_fields.AutoTypedField):
    def __init__(self, objtype, subclasses=False, **kwargs):
        self.AUTO_TYPE = PolymorphicObject(objtype, subclasses)
        self.objname = objtype
        super().__init__(**kwargs)


class ListOfObjectsField(ovoo_fields.ListOfObjectsField):
    pass


class ObjectFields(ovoo_fields.ObjectField):
    def __init__(self, objtype, subclasses=False, relation=False, **kwargs):
        self.AUTO_TYPE = ovoo_fields.List(
            ovoo_fields.Object(objtype, subclasses))
        self.objname = objtype
        super().__init__(objtype, **kwargs)
        self.relation = relation


class IntegerFields(IntegerField):
    def __init__(self, nullable=False, default=ovoo_fields.UnspecifiedDefault,
                 read_only=False, minimum=0, maximum=None):
        super().__init__(
            nullable=nullable, default=default, read_only=read_only
        )
        self.min = minimum
        self.max = maximum

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if value is None:
            return value
        if value < self.min:
            # return self.min
            raise ValueError('Value must be >= {} for field {}'.format(
                self.min, attr)
            )
        if self.max and value > self.max:
            raise ValueError('Value too high for %s' % attr)
        return value


class StringFields(ovoo_fields.StringField):
    def __init__(self, nullable=False, read_only=False,
                 default=ovoo_fields.UnspecifiedDefault, description='',
                 maxLength=None):
        super().__init__(
            nullable=nullable, default=default, read_only=read_only
        )
        self.description = description
        self.maxLength = maxLength

    def coerce(self, obj, attr, value):
        if value is None:
            return self._null(obj, attr)
        else:
            value = super().coerce(obj, attr, value)
            if self.maxLength and len(value) > self.maxLength:
                raise ValueError('Value too long for %s' % attr)
            return value


class UUID(ovoo_fields.UUID):
    def coerce(self, obj, attr, value):
        try:
            value = int(value)
            uuid.UUID(int=value)
        except ValueError:
            uuid.UUID(hex=value)
        return str(value)


class UUIDFields(ovoo_fields.AutoTypedField):
    AUTO_TYPE = UUID()


class DateTimeField(ovoo_fields.DateTimeField):
    def __init__(self, tzinfo_aware=False, **kwargs):
        super().__init__(tzinfo_aware, **kwargs)


class ObjectField(ovoo_fields.ObjectField):
    pass


class IPV4AddressField(ovoo_fields.IPV4AddressField):

    def coerce(self, obj, attr, value):
        try:
            # make sure that DNS Python agrees that it is a valid IP address
            ipv4.inet_aton(str(value))
        except dns.exception.SyntaxError:
            raise ValueError()
        value = super().coerce(obj, attr, value)
        # we use this field as a string, not need a netaddr.IPAdress
        # as oslo.versionedobjects is using
        return str(value)


class IPV6AddressField(ovoo_fields.IPV6AddressField):

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        # we use this field as a string, not need a netaddr.IPAdress
        # as oslo.versionedobjects is using
        return str(value)


class IPV4AndV6AddressField(ovoo_fields.IPV4AndV6AddressField):

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        # we use this field as a string, not need a netaddr.IPAdress
        # as oslo.versionedobjects is using
        return str(value)


class Enum(ovoo_fields.Enum):
    def get_schema(self):
        return {
            'enum': self._valid_values,
            'type': 'any'
        }


class EnumField(ovoo_fields.BaseEnumField):
    def __init__(self, valid_values, **kwargs):
        self.AUTO_TYPE = Enum(valid_values=valid_values)
        super().__init__(**kwargs)


class DomainField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if value is None:
            return
        domain = value.split('.')
        for host in domain:
            if len(host) > 63:
                raise ValueError("Host %s is too long" % host)
        if not value.endswith('.'):
            raise ValueError("Domain %s does not end with a dot" % value)
        if not constants.RE_ZONENAME.match(value):
            raise ValueError("Domain %s is invalid" % value)
        return value


class EmailField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if value.count('@') != 1:
            raise ValueError("%s is not an email" % value)
        email = value.replace('@', '.')
        if not constants.RE_ZONENAME.match("%s." % email):
            raise ValueError("Email %s is invalid" % value)
        return value


class HostField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if value is None:
            return
        hostname = value.split('.')
        for host in hostname:
            if len(host) > 63:
                raise ValueError("Host %s is too long" % host)
        if value.endswith('.') is False:
            raise ValueError("Host name %s does not end with a dot" % value)
        if not constants.RE_HOSTNAME.match(value):
            raise ValueError("Host name %s is invalid" % value)
        return value


class SRVField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if value is None:
            return
        srvtype = value.split('.')
        for host in srvtype:
            if len(host) > 63:
                raise ValueError("Host %s is too long" % host)
        if value.endswith('.') is False:
            raise ValueError("Host name %s does not end with a dot" % value)
        if not constants.RE_SRV_HOST_NAME.match(value):
            raise ValueError("Host name %s is not a SRV record" % value)
        return value


class TxtField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if value.endswith('\\'):
            raise ValueError("Do NOT put '\\' into end of TXT record")
        return value


class Sshfp(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if not constants.RE_SSHFP_FINGERPRINT.match("%s" % value):
            raise ValueError("Host name %s is not a SSHFP record" % value)
        return value


class TldField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if not constants.RE_TLDNAME.match(value):
            raise ValueError("%s is not a TLD" % value)
        return value


class NaptrFlagsField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if (len(value) > 255):
            raise ValueError("NAPTR record flags field cannot be longer than"
                             " 255 characters" % value)
        if not constants.RE_NAPTR_FLAGS.match("%s" % value):
            raise ValueError("NAPTR record flags can be S, A, U and P" % value)
        return value


class NaptrServiceField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if (len(value) > 255):
            raise ValueError("NAPTR record service field cannot be longer than"
                             " 255 characters" % value)
        if not constants.RE_NAPTR_SERVICE.match("%s" % value):
            raise ValueError("%s NAPTR record service is invalid" % value)
        return value


class NaptrRegexpField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if (len(value) > 255):
            raise ValueError("NAPTR record regexp field cannot be longer than"
                             " 255 characters" % value)
        if value:
            if not constants.RE_NAPTR_REGEXP.match("%s" % value):
                raise ValueError("%s NAPTR record is invalid" % value)
        return value


class CaaPropertyField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        prpt = value.split(' ', 1)
        tag = prpt[0]
        val = prpt[1]
        if (tag == 'issue' or tag == 'issuewild'):
            entries = val.split(';')
            idn = entries.pop(0)
            domain = idn.split('.')
            for host in domain:
                if len(host) > 63:
                    raise ValueError("Host %s is too long" % host)
            idn_with_dot = idn + '.'
            if not constants.RE_ZONENAME.match(idn_with_dot):
                raise ValueError("Domain %s is invalid" % idn)
            for entry in entries:
                if not constants.RE_KVP.match(entry):
                    raise ValueError("%s is not a valid key-value pair" %
                                     entry)
        elif tag == 'iodef':
            if constants.RE_URL_MAIL.match(val):
                parts = val.split('@')
                idn = parts[1]
                domain = idn.split('.')
                for host in domain:
                    if len(host) > 63:
                        raise ValueError("Host %s is too long" % host)
                idn_with_dot = idn + '.'
                if not constants.RE_ZONENAME.match(idn_with_dot):
                    raise ValueError("Domain %s is invalid" % idn)
            elif constants.RE_URL_HTTP.match(val):
                parts = val.split('/')
                idn = parts[2]
                domain = idn.split('.')
                for host in domain:
                    if len(host) > 63:
                        raise ValueError("Host %s is too long" % host)
                idn_with_dot = idn + '.'
                if not constants.RE_ZONENAME.match(idn_with_dot):
                    raise ValueError("Domain %s is invalid" % idn)
            else:
                raise ValueError("%s is not a valid URL" % val)
        else:
            raise ValueError("Property tag %s must be 'issue', 'issuewild'"
                             " or 'iodef'" % value)
        return value


class CertTypeField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if not constants.RE_CERT_TYPE.match("%s" % value):
            raise ValueError("Cert type %s is not a valid Mnemonic or "
                             "value" % value)
        return value


class CertAlgoField(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)
        if not constants.RE_CERT_ALGO.match("%s" % value):
            raise ValueError("Cert Algo %s is not a valid Mnemonic or "
                             "value" % value)
        return value


class Any(ovoo_fields.FieldType):
    @staticmethod
    def coerce(obj, attr, value):
        return value


class AnyField(ovoo_fields.AutoTypedField):
    AUTO_TYPE = Any()


class BaseObject(ovoo_fields.FieldType):
    @staticmethod
    def coerce(obj, attr, value):
        if isinstance(value, object):
            return value
        else:
            raise ValueError("BaseObject valid values are not valid")


class BaseObjectField(ovoo_fields.AutoTypedField):
    AUTO_TYPE = BaseObject()


class IPOrHost(IPV4AndV6AddressField):
    def __init__(self, nullable=False, read_only=False,
                 default=ovoo_fields.UnspecifiedDefault):
        super().__init__(
            nullable=nullable, default=default, read_only=read_only
        )

    def coerce(self, obj, attr, value):
        try:
            value = super().coerce(obj, attr, value)
        except ValueError:
            if not constants.RE_ZONENAME.match(value):
                raise ValueError("%s is not IP address or host name" % value)
        return value


class DenylistFields(StringFields):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def coerce(self, obj, attr, value):
        value = super().coerce(obj, attr, value)

        if value is None:
            return self._null(obj, attr)

        # determine the validity if a regex expression filter has been used.
        msg = "%s is not a valid regular expression" % value
        if not len(value):
            raise ValueError(msg)
        try:
            re.compile(value)
        except Exception:
            raise ValueError(msg)

        return value
