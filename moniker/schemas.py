    from moniker.schema import Schema, CollectionSchema

SERVER_PROPERTIES = {
    'id': {
        'type': 'string',
        'description': 'Server identifier',
        'pattern': ('^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}'
                    '-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}$'),
    },
    'name': {
        'type': 'string',
        'description': 'Server DNS name',
        'maxLength': 255,
        'required': True,
    },
    'ipv4': {
        'type': 'string',
        'description': 'IPv4 address of server',
        'maxLength': 15,
        'required': True,
    },
    'ipv6': {
        'type': 'string',
        'description': 'IPv6 address of server',
        'maxLength': 15,
    },
    'created_at': {
        'type': 'string',
        'description': 'Date and time of server creation',
        'format': 'date-time',
    },
    'updated_at': {
        'type': 'string',
        'description': 'Date and time of last server update',
        'format': 'date-time',
    },
    'self': {'type': 'string'},
    'schema': {'type': 'string'},
}

SERVER_LINKS = [
    {'rel': 'self', 'href': '{self}'},
    {'rel': 'describedby', 'href': '{schema}'},
]

DOMAIN_PROPERTIES = {
    'id': {
        'type': 'string',
        'description': 'Domain identifier',
        'pattern': ('^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}'
                    '-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}$'),
    },
    'name': {
        'type': 'string',
        'description': 'Domain name',
        'maxLength': 255,
        'required': True,
    },
    'serial': {
        'type': 'integer',
        'description': 'Zone serial number',
    },
    'ttl': {
        'type': 'integer',
        'description': 'Time to live',
    },
    'created_at': {
        'type': 'string',
        'description': 'Date and time of image registration',
        'format': 'date-time',
    },
    'updated_at': {
        'type': 'string',
        'description': 'Date and time of image registration',
        'format': 'date-time',
    },
    'self': {'type': 'string'},
    'records': {'type': 'string'},
    'schema': {'type': 'string'},
}

DOMAIN_LINKS = [
    {'rel': 'self', 'href': '{self}'},
    {'rel': 'records', 'href': '{records}', 'method': 'GET'},
    {'rel': 'describedby', 'href': '{schema}', 'method': 'GET'},
]

RECORD_PROPERTIES = {
    'id': {
        'type': 'string',
        'description': 'Record identifier',
        'pattern': ('^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}'
                    '-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}$'),
    },
    'domain_id': {
        'type': 'string',
        'description': 'Domain identifier',
        'pattern': ('^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}'
                    '-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}$'),
    },
    'name': {
        'type': 'string',
        'description': 'DNS Record Name',
        'maxLength': 255,
        'required': True,
    },
    'data': {
        'type': 'string',
        'description': 'DNS Record Value',
        'maxLength': 255,
        'required': True,
    },
    'ttl': {
        'type': 'integer',
        'description': 'Time to live.',
    },
    'created_at': {
        'type': 'string',
        'description': 'Date and time of image registration',
        'format': 'date-time',
    },
    'updated_at': {
        'type': 'string',
        'description': 'Date and time of image registration',
        'format': 'date-time',
    },
    'self': {'type': 'string'},
    'domain': {'type': 'string'},
    'schema': {'type': 'string'},
}

RECORD_LINKS = [
    {'rel': 'self', 'href': '{self}'},
    {'rel': 'domain', 'href': '{domain}'},
    {'rel': 'describedby', 'href': '{schema}'},
]

server_schema = Schema('server', SERVER_PROPERTIES, SERVER_LINKS)
servers_schema = CollectionSchema('servers', server_schema)

domain_schema = Schema('domain', DOMAIN_PROPERTIES, DOMAIN_LINKS)
domains_schema = CollectionSchema('domains', domain_schema)

record_schema = Schema('record', RECORD_PROPERTIES, RECORD_LINKS)
records_schema = CollectionSchema('records', record_schema)
