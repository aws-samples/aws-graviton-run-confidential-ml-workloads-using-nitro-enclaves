import threading

from common.rpc import RPCException, RPCResult
from common.socket import Socket, SocketException

MAX_QUEUE = 10


class RPCServer:
    def __init__(self, host, port):
        self.socket = Socket()
        self.socket.listen(host, port, MAX_QUEUE)
        self.endpoints = dict()

    def export(self, func):
        name = func.__name__
        self.endpoints[name] = func

    def workload(self, client):
        while True:
            try:
                endpoint = client.recv()
            except SocketException as e:
                break
            except:
                continue

            try:
                result = self.invoke(endpoint)
                client.send(RPCResult(result))
            except RPCException as e:
                client.send(e)

    def run(self):
        while True:
            client = self.socket.accept()
            thread = threading.Thread(target=self.workload, args=[client])
            thread.start()
            # Prevent running of concurrent client commands (especially run script commands)
            thread.join()

    def invoke(self, endpoint):
        if not endpoint.name in self.endpoints:
            raise RPCException("Unknown endpoint")

        func = self.endpoints[endpoint.name]

        try:
            return func(*endpoint.args)
        except Exception as e:
            raise RPCException(e)
