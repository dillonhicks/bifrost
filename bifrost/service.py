from bifrost.storage import Storage
from bifrostv1.bifrost_pb2 import Endpoint
from sqlalchemy import create_engine
from bifrost.storage import SessionFactory


__all__ = (
    'BifrostService',
    'BifrostServiceFactory'
)


class BifrostService(object):
    def __init__(self, storage: Storage):
        self.storage = storage

    def create_endpoint(self, endpoint: Endpoint):
        self.storage.put(endpoint.name, endpoint)
        return f'{endpoint.owner} is a winner'

    def list_endpoints(self):
        return self.storage.all(Endpoint)


class BifrostServiceFactory(object):

    def __init__(self):
        pass

    def create(config):
        session_factory = SessionFactory(create_engine(config.DATABASE_URI))
        storage = Storage(session_factory)
        return BifrostService(storage)

