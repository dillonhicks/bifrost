import contextlib
import os
from base64 import b16encode
from enum import Enum
from typing import Optional, List

import google
from google.protobuf import any_pb2
from google.protobuf.message import Message
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from bifrost.id import uuid_for, prefix_for
from bifrost.model import KeyValue


__all__ = (
    'IsolationLevel',
    'SessionFactory',
    'BaseRepository',
)


class IsolationLevel(Enum):
    """Define the names of common database isolation levels"""
    read_committed = "READ COMMITTED"
    read_uncommitted = "READ UNCOMMITTED"
    repeatable_read = "REPEATABLE READ"
    serializable = "SERIALIZABLE"
    engine_default = "ENGINE DEFAULT ISOLATION_LEVEL"


class SessionFactory(object):
    def __init__(self, engine):
        self._engine = engine

        self._sessionmaker = sessionmaker(
            bind=self._engine,
            # prevents SQLAlchemy from creating a 'default' txn
            autocommit=True,
            # prevents SQLAlchemy from randomly doing db queries on property access of entities
            expire_on_commit=False)

    def create_session(self):
        return self._sessionmaker()

    @contextlib.contextmanager
    def create_context(self, session=None):
        should_close = False
        if session is None:
            should_close = True
            session = self.create_session()

        try:
            yield session
        finally:
            if should_close:
                session.close()


class Storage(object):
    def __init__(self, session_factory):
        # type: (SessionFactory, google.protobuf.message.Message) -> None
        self.session_factory = session_factory

    def put(self, key: str, message: google.protobuf.message.Message,
            existing_session: Session=None) -> KeyValue:

        envelope = any_pb2.Any()
        envelope.Pack(message)

        with self.session_factory.create_context(existing_session) as session, session.begin():
            entry = KeyValue()
            entry.key = uuid_for(message)
            entry.value = envelope
            entry.owner_id = getattr(message, 'owner', '')
            session.add(entry)

        return entry

    def get(self, key: str, message, existing_session: Session=None) -> Optional[Message]:

        with self.session_factory.create_context(existing_session) as session:
            entry = session.query(KeyValue).filter(KeyValue.key == key).first()

        if entry is None:
            return None

        return entry.value.UnPack(message)

    def all(self, Message, existing_session: Session=None) -> List[Message]:
        prefix = prefix_for(Message)
        with self.session_factory.create_context(existing_session) as session:
            entries = session.query(KeyValue).filter(KeyValue.key.startswith(prefix)).all()

        def unpack(entry):
            message = Message()
            entry.value.Unpack(message)
            message.tags.append(str(entry.uuid))
            return message

        return [unpack(e) for e in entries]
