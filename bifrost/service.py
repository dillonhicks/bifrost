from bifrost.storage import Storage
from bifrostv1.bifrost_pb2 import Endpoint
from sqlalchemy import create_engine
from bifrost.storage import SessionFactory
import docker
from pathlib import Path
from bifrost.const import Size


__all__ = (
    'BifrostService',
    'BifrostServiceFactory'
)


class BifrostService(object):

    def __init__(self, config, storage: Storage, client):
        self.config = config
        self.storage = storage
        self.docker = client

    def create_endpoint(self, endpoint: Endpoint):
        self.storage.put(endpoint.name, endpoint)
        return f'{endpoint.owner} is a winner'

    def list_endpoints(self):
        return self.storage.all(Endpoint)

    def create_proxy(self, user):
        proxy = None
        self.storage.put(proxy)
        self.docker.containers.run(self.config.docker.IMAGE_NAME, detach=True)

    def iter_client_binary(self):
        with Path('.local/bin/ngrok').open('rb') as binfile:
            chunk = [None]
            while len(chunk) > 0:
                chunk = binfile.read(8 * Size.KiB)
                yield chunk

    def client_config(self):
        with Path('ngrokclientconfig.yml').open('r') as infile:
            return infile.read()


class BifrostServiceFactory(object):

    def __init__(self):
        pass

    def create(config):
        client = docker.from_env()
        session_factory = SessionFactory(create_engine(config.DATABASE_URI))
        storage = Storage(session_factory)
        return BifrostService(config, storage, client)

