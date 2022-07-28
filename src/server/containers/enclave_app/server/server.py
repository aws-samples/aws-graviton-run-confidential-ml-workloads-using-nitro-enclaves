import os
import socket
import threading

from filesystem.rfs_server import RFSServer
from network.proxy import Proxy
from network.rpc_server import RPCServer

# Custom RPC functions to enable required functionality
from process.run import run

CID = 18
PORT_SYNC = 5000
PORT_RUN = 6000
PROXY_PORT = 8001

SYNC_DIR = "/tmp/client/"


def write_banner():
    os.makedirs(SYNC_DIR, exist_ok=True)

    with open(SYNC_DIR + "from_server.txt", "w") as fh:
        fh.write("Enclave Server Initialised\n")


def main():
    # Write file to confirm client synced folder can access server
    write_banner()

    # Create a proxy for KMS
    proxy = Proxy(PROXY_PORT, CID)

    # Open proxy to allow connections to KMS for decryption
    thread_proxy = threading.Thread(target=proxy.connect)
    thread_proxy.start()

    # Open communication channel to allow client connections for filesystem commands
    rpc_server_sync = RPCServer(socket.VMADDR_CID_ANY, PORT_SYNC)
    # Process filesystem commands from client's synced folder
    RFSServer(SYNC_DIR, rpc_server_sync)

    # Listen for filesystem commands
    thread_sync = threading.Thread(target=rpc_server_sync.run)
    thread_sync.start()

    # Open communication channel to allow client connections for run commands
    rpc_server_run = RPCServer(socket.VMADDR_CID_ANY, PORT_RUN)
    # Process client "run" command to execute scripts
    rpc_server_run.export(run)

    # Listen for run script commands
    thread_run = threading.Thread(target=rpc_server_run.run)
    thread_run.start()

    thread_proxy.join()
    thread_sync.join()
    thread_run.join()


if __name__ == "__main__":
    main()
