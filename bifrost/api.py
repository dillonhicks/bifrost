from typing import Generator
import grpc
from google.protobuf import empty_pb2

from bifrost.service import BifrostService
from bifrostv1 import bifrost_pb2_grpc
from bifrostv1.bifrost_pb2 import CreateEndpointRequest, CreateEndpointResponse, ListEndpointsResponse, \
    StreamProxyClientBinaryRequest, ProxyClientBinaryPart, ClientConfigResponse


class BifrostAPI(bifrost_pb2_grpc.BifrostServicer):

    def __init__(self, *args, service: BifrostService, **kwargs):
        super().__init__(*args, **kwargs)
        self._service = service

    def CreateEndpoint(self, request: CreateEndpointRequest,
                       context: grpc.RpcContext) -> CreateEndpointResponse:
        details = self._service.create_endpoint(request.endpoint)
        return CreateEndpointResponse(details=details)

    def ListEndpoints(self, request: empty_pb2.Empty,
                      context: grpc.RpcContext) ->  Generator[ListEndpointsResponse, None, None]:

        for endpoint in self._service.list_endpoints():
            yield endpoint

    def StreamProxyClientBinary(self, request: StreamProxyClientBinaryRequest,
                                context: grpc.RpcContext) -> Generator[ProxyClientBinaryPart, None, None]:

        for chunk in self._service.iter_client_binary():
            response = ProxyClientBinaryPart()
            response.chunk = chunk
            yield response

    def ClientConfig(self, request, context):
        response = ClientConfigResponse()
        response.config = self._service.client_config()
        return response
