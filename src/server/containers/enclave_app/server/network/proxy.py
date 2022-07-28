import socket
import threading

MAX_QUEUE = 10


class Proxy:
    def __init__(self, port, cid):
        self.port = port
        self.cid = cid

    def connect(self):
        std_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        std_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        std_socket.bind(("127.0.0.1", 443))
        std_socket.listen(MAX_QUEUE)

        while True:
            client_socket = std_socket.accept()[0]

            server_socket = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
            server_socket.connect((self.cid, self.port))

            outgoing_thread = threading.Thread(
                target=self.forward, args=(client_socket, server_socket)
            )
            incoming_thread = threading.Thread(
                target=self.forward, args=(server_socket, client_socket)
            )

            outgoing_thread.start()
            incoming_thread.start()

    def forward(self, src, dest):
        payload = " "
        while payload:
            payload = src.recv(1024)
            if payload:
                dest.sendall(payload)
            else:
                src.shutdown(socket.SHUT_RD)
                dest.shutdown(socket.SHUT_WR)
