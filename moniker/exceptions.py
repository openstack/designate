

class Base(Exception):
    pass


class InvalidObject(Base):
    pass


class Forbidden(Base):
    pass


class InvalidSortKey(Base):
    pass


class NoServersConfigured(Base):
    pass


class Duplicate(Base):
    pass


class DuplicateServer(Duplicate):
    pass


class DuplicateDomain(Duplicate):
    pass


class DuplicateRecord(Duplicate):
    pass


class NotFound(Base):
    pass


class ServerNotFound(NotFound):
    pass


class DomainNotFound(NotFound):
    pass


class RecordNotFound(NotFound):
    pass
