from common.rpc import RPCEndpoint, RPCException, RPCResult
from common.socket import Socket, SocketException


class RPCClient:
    def __init__(self, host, port):
        self.socket = Socket()
        self.socket.connect(host, port)

    def __getattr__(self, name):
        def rpc_func(*args):
            rpc_endpoint = RPCEndpoint(name, args)
            self.socket.send(rpc_endpoint)

            try:
                response = self.socket.recv()
            except SocketException as e:
                raise e

            if isinstance(response, RPCException):
                raise response.reason
            elif isinstance(response, RPCResult):
                if response.data:
                    return response.data

        return rpc_func
