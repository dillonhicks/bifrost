"""Python Stub implementation of bifrostv1"""
import sys
import time
from concurrent import futures
from subprocess import Popen

import grpc
import pkg_resources
from sqlalchemy import create_engine
from thundersnow.dateutil import Delta
from thundersnow.type import immutable

from bifrost.api import BifrostAPI
from bifrost.model import SQLAlchemyBaseModel
from bifrost.service import BifrostServiceFactory
from bifrostv1 import bifrost_pb2_grpc


def serve(config, port, with_proxy_server=False):

    engine = create_engine(config.DATABASE_URI, echo=True)
    SQLAlchemyBaseModel.metadata.create_all(engine, checkfirst=True)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    bifrost_service = BifrostServiceFactory.create(config)
    bifrost_api = BifrostAPI(service=bifrost_service)

    bifrost_pb2_grpc.add_BifrostServicer_to_server(bifrost_api, server)

    server.add_insecure_port('[::]:{}'.format(port))
    server.start()

    proxy_process = None
    proxy_filepath = pkg_resources.resource_filename('bifrostv1', 'bin/rest-proxy-server.bin')
    if sys.platform.lower() == 'darwin':
        proxy_filepath = '.'.join([proxy_filepath, 'darwin'])

    try:
        if with_proxy_server:
            proxy_process = Popen([proxy_filepath])
        while True:
            time.sleep(Delta.one_day.total_seconds())
    except KeyboardInterrupt:
        if proxy_process is not None:
            proxy_process.terminate()

        server.stop(0)


def load_config():
    return immutable(
        'Config',
        DATABASE_URI='postgres+psycopg2://APIServerUser:DieInBattleAndGoToValhalla@127.0.0.1/bifrostapi',
        docker=immutable('DOCKER_CONFIG',
                         IMAGE_NAME='sequenceiq/ngrokd',)
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Run bifrostv1, optionally with the REST Proxy Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--port', type=str, action='store',
                        default=8080,
                        help='server port')

    parser.add_argument('--with-proxy-server', action='store_true',
                        default=False, help='Start the rest proxy server')

    args = parser.parse_args()
    serve(load_config(), args.port, args.with_proxy_server)


if __name__ == '__main__':
    main()