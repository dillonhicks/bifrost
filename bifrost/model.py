from functools import partial

import arrow
from google.protobuf import any_pb2
from sqlalchemy import Column, String
from thundersnow.reflection import module_name

import bifrost
from bifrost.const import Size
from bifrost.sqlaext import SQLAlchemyBaseModel, ResourceTagMixin, UTCDateTime, MessageEnvelope, \
    PackageMetadata, \
    ModelMetadata
from bifrost.type import Version


__all__ = (
    'KeyValue'
)


# For the sake of a demo have all of the columns not null by default
_Column = Column
Column = partial(_Column, nullable=False)
SmallString = String(255)


def utcnow():
    return arrow.utcnow().datetime


class TimestampMixin(object):
    created = Column(UTCDateTime, default=utcnow)
    updated = Column(UTCDateTime, default=utcnow, onupdate=utcnow)


class PkgBaseModel(SQLAlchemyBaseModel, ResourceTagMixin, TimestampMixin):
    """Combines together a package specific base model which has metadata and
    default mixins"""
    __abstract__ = True
    __bifrost_metadata__ = PackageMetadata(
        module_name(bifrost),
        Version.from_string(bifrost.__version__)
    )


class KeyValue(PkgBaseModel):
    __bifrost_model_metadata__ = ModelMetadata(
        table='key_value',
        resource_type='kv'
    )

    key = Column(String(2 * Size.KiB), primary_key=True)
    value = Column(MessageEnvelope(Message=any_pb2.Any))
    owner_id = Column(SmallString)
