from typing import NamedTuple
from itertools import chain
from thundersnow.precondition import check_argument
from thundersnow.reflection import class_name
import os
from base64 import b16encode


SEPARATOR = ':'
UID_BYTES_SIZE = 6


def prefix_for(message):
    return message.DESCRIPTOR.name.lower()


def uuid_for(message):
    prefix = prefix_for(message)
    uid = generate_uuid()
    return f'{prefix}-{uid}'


def generate_uuid():
    return b16encode(os.urandom(UID_BYTES_SIZE)).decode('ascii')


class ResourceID(NamedTuple):
    prefix: str
    partition: str
    service: str
    version: str
    owner: str
    type: str
    id: str

    def __str__(self):
        return ':'.join(self)

    @staticmethod
    def parse(string):
        check_argument(string.count(SEPARATOR) == 6, 'Not the correct resource id format')
        parts = string.split(SEPARATOR)
        return ResourceID(*parts)


class BifrostResourceID(ResourceID):
    def __new__(cls,  service='', version='', owner='', type='', id=''):
        return super().__new__(
            cls, 'hackday', 'api', str(service), str(version), str(owner), str(type), str(id))

    def __repr__(self):
        fields = self._asdict()
        body = ', '.join(['{}={!r}'] * len(fields))
        template = ''.join(['{}(', body, ')'])
        return template.format(class_name(self), *chain.from_iterable(fields.items()))

    def __str__(self):
        return ':'.join(self)

    @staticmethod
    def parse(string):
        check_argument(string.count(SEPARATOR) == 6, 'Not the correct resource id format {!r}', string)
        parts = string.split(SEPARATOR)
        check_argument(parts[0] == 'bifrost')
        check_argument(parts[1] == 'api')
        return BifrostResourceID(*parts[2:])
