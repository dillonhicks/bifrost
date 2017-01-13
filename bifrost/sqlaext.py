from __future__ import absolute_import

import datetime

from typing import NamedTuple
import google.protobuf.message
import pytz
from google.protobuf.json_format import MessageToDict, ParseDict
from sqlalchemy import DateTime, String, Column
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.declarative.api import DeclarativeMeta, declarative_base, declared_attr
from thundersnow.type import immutable, sentinel
from thundersnow.precondition import check_argument, check_state
from bifrost.const import Size
from bifrost.id import BifrostResourceID, generate_uuid
from bifrost.error import BifrostError
from bifrost.type import Version


__all__ = (
    'Attribute',
    'Template',
    'package_metadata',
    'model_metadata',
)


Template = immutable(
    'Format',
    tablename='{prefix}_v{major}_{table}',
)


Attribute = immutable(
    'Attribute',
    pkg_metadata='__bifrost_metadata__',
    model_metadata='__bifrost_model_metadata__',
    tablename='__tablename__'
)


class DataModelError(BifrostError):
    pass


class MissingRegistryEntryError(DataModelError):
    pass


class ModelMetadata(NamedTuple):
    table: str
    resource_type: str


class PackageMetadata(NamedTuple):
    package: str
    version: Version



class UTCDateTime(TypeDecorator):

    impl = DateTime

    def process_bind_param(self, value, engine):
        if value is not None:
            # Convert the timezoned datetime to UTC and then kill the
            # extra TZ info as it isnt compatible with mysql.
            return value.astimezone(pytz.UTC).replace(tzinfo=None)

    def process_result_value(self, value, engine):
        if value is not None:
            return datetime.datetime(value.year, value.month, value.day,
                                     value.hour, value.minute, value.second,
                                     value.microsecond, tzinfo=pytz.UTC)


class MessageEnvelope(TypeDecorator):
    # TODO-dillon: This is possible but is it necessary?
    # reflection_schema = sentinel('REFLECTION_SCHEMA')
    impl = JSONB

    def __init__(self, *args, Message, **kwargs):
        check_argument(issubclass(Message, google.protobuf.message.Message),
                       'Message must be a protobuf message class, got {}', Message)
        self._Message = Message
        super().__init__(*args, **kwargs)


    def process_bind_param(self, value, engine):
        if value is None:
            return value
        else:
            check_argument(isinstance(value, self._Message),
                'value is not an instance of {}', self._Message)

            return MessageToDict(value)


    def process_result_value(self, value, engine):
        if value is None:
            return value
        else:
            return ParseDict(value, self._Message())


class ResourceID(TypeDecorator):
    impl = String(4 * Size.KiB)

    def process_bind_param(self, value, engine):
        if value is None:
            return value
        else:
            return str(value)


    def process_result_value(self, value, engine):
        if value is None:
            return value
        else:
            return BifrostResourceID.parse(value)


# Implementation specific attributes
SQLAField = immutable(
    'SQLAField',
    abstract='__abstract__'
)


_MissingModelMetadata = sentinel('MISSING_MODEL_METADATA')
_MissingPkgMetadata = sentinel('MISSING_PACKAGE_METADATA')


class SQLAlchemyModelMeta(DeclarativeMeta):
    """

    - Adjust the tablenames to be prefixed with the package
      metdatadata defined in their mixin

    - TODO: add to model registry
    """

    # TODO: Think about how we can make a super meta that uses a
    # chained map with weak values to pull all of the registered
    # models from respective backend metas.
    #
    # _model_registry = DataModelRegistry()


    def __new__(cls, name, bases, dct):

        if dct.get(SQLAField.abstract, False) or (bases[0] is _DataModelBase):
            return super(SQLAlchemyModelMeta, cls).__new__(cls, name, bases, dct)

        model_metadata = dct.get(Attribute.model_metadata, _MissingModelMetadata)
        check_state(model_metadata is not _MissingModelMetadata,
                    'required attribue {} supplied in model class {}',
                    Attribute.model_metadata, name)

        pkg_metadata = _MissingPkgMetadata
        if Attribute.pkg_metadata in dct:
            pkg_metadata =  dct[Attribute.pkg_metadata]
        else:
            for base in bases:
                base_metadata = getattr(base, Attribute.pkg_metadata, _MissingPkgMetadata)
                if isinstance(base_metadata, PackageMetadata):
                    pkg_metadata = base_metadata

        check_state(pkg_metadata is not _MissingPkgMetadata,
                    'required attribue {} supplied in model class {} or any of its base clases',
                    Attribute.pkg_metadata, name)

        # # TODO: type checking
        # check_argument(Attribute.tablename in dct,
        #                'no tablename attribute {} supplied for model {}',
        #                Attribute.tablename, name)

        tablename = model_metadata.table
        package_prefixed_tablename = Template.tablename.format(
            prefix=pkg_metadata.package,
            major=pkg_metadata.version.major,
            table=tablename
        ).lower()

        dct[Attribute.tablename] = package_prefixed_tablename
        dct[Attribute.pkg_metadata] = pkg_metadata
        Model = super(SQLAlchemyModelMeta, cls).__new__(cls, name, bases, dct)
        return Model


class _DataModelBase(object):
    __abstract__ = True

class SQLAlchemyBaseModel(declarative_base(cls=_DataModelBase, metaclass=SQLAlchemyModelMeta)):
    """Base model from which models should inherit for sqlalchemy"""
    __abstract__ = True


def package_metadata(obj):
    """Return the package metadata attached to a model or None"""
    return getattr(obj, Attribute.pkg_metadata, None)

def model_metadata(obj):
    """Return the model metadata attached to a model or None"""
    return getattr(obj, Attribute.model_metadata, None)


class ResourceTagMixin(object):
    """mixin, creates a new uuid column based on the given metadata for
    each model class
    """

    @declared_attr
    def uuid(cls):
        pkg_metadata = package_metadata(cls)
        metadata = model_metadata(cls)
        check_state(pkg_metadata is not None)
        check_state(metadata is not None)

        def resource_tag_generator(context):
            # Try to get the owner if the resouce is an owned resouce.
            # TODO-dillon: How do we mark a resource as owned?
            owner = context.current_parameters.get('owner_id', '')
            return BifrostResourceID(
                service=pkg_metadata.package,
                version='v' + pkg_metadata.version.major,
                owner=owner,
                type=metadata.resource_type,
                id='{}-{}'.format(metadata.resource_type, generate_uuid()))

        return Column(ResourceID, unique=True, index=True, default=resource_tag_generator)

