import io
import pickle
import socket
import struct

from common.unpickler import SafeUnpickler


class SocketException(Exception):
    pass


class Socket:
    def __init__(self):
        self.socket = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)

    def connect(self, host, port):
        try:
            self.socket.connect((host, port))
        except socket.error as e:
            raise SocketException(str(e))

    def __del__(self):
        self.socket.close()

    def send(self, data):
        payload_bytes = pickle.dumps(data)
        self.write(payload_bytes)

    def write(self, data_bytes):
        # send header
        size_bytes = struct.pack("!i", len(data_bytes))
        self.socket.send(size_bytes)
        # send data
        self.socket.sendall(data_bytes)

    def read(self, total):
        view = memoryview(bytearray(total))
        next_offset = 0
        while total - next_offset > 0:
            recv_size = self.socket.recv_into(view[next_offset:], total - next_offset)
            if not recv_size:
                raise SocketException("Server connection closed")
            next_offset += recv_size
        return view.tobytes()

    def recv(self):
        # read header
        size_bytes = self.read(4)
        total = struct.unpack("!i", size_bytes)[0]

        # read data
        payload_bytes = self.read(total)
        payload = SafeUnpickler(io.BytesIO(payload_bytes)).load()

        return payload
