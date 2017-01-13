import logging
import subprocess
import os
import stat
from tempfile import TemporaryDirectory
from pathlib import Path
from bifrostv1.client import BifrostClient
from bifrostv1.bifrost_pb2 import StreamProxyClientBinaryRequest, ClientConfigRequest
import yaml
import time

LOG = logging.getLogger(__name__)


class ExternalProxyTunnel(object):
    def __init__(self, name, local_port='5001', bifrost_host='127.0.0.1', bifrost_port='8080'):
        self.client = BifrostClient(bifrost_host, bifrost_port)
        self.local_port = local_port
        self.session_name = None
        self.name = name

    def __enter__(self):

        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'ngrok'

            with filepath.open('w+b') as tmp:
                for chunk in self.client.stream_proxy_client_binary(StreamProxyClientBinaryRequest(uuid='12312')):
                    tmp.write(chunk.chunk)

                tmp.flush()

            config_path= Path(tmpdir) / 'ngrok.yml'
            response = self.client.client_config(ClientConfigRequest())
            data = yaml.load(response.config)
            uri = data['server_addr'].replace('ngrok', self.name).replace('4443', '4480')
            proxy_uri = f'http://{uri}'

            with config_path.open('w') as configfile:
                configfile.write(response.config)

            LOG.info('Config: %s', response.config)
            st = os.stat(str(filepath))
            os.chmod(str(filepath), st.st_mode | stat.S_IEXEC)

            self.session_name = f'ngrok-{filepath.parent.name}'

            ngrok_cmd = '{} -config={} -subdomain={} {}'.format(
                filepath, config_path, self.name, self.local_port)

            args = [
                'tmux', 'new', '-s', self.session_name,
                '-d', ngrok_cmd]

            LOG.info('Starting bridge client: %s', args)
            subprocess.check_call(args)
            time.sleep(1.0)  # Bad

        return proxy_uri

    def __exit__(self, exc_type, exc_val, exc_tb):
        subprocess.check_call(['tmux', 'kill-session', '-t', self.session_name])
