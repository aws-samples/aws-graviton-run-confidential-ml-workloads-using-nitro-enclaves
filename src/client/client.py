import argparse
import json
import subprocess

import requests
from filesystem.rfs_client import RFSClient
from fuse import FUSE
from network.rpc_client import RPCClient

PORT_SYNC = 5000
PORT_RUN = 6000
PROXY_PORT = 8001


def get_cid():
    proc = subprocess.Popen(
        ["/bin/nitro-cli", "describe-enclaves"], stdout=subprocess.PIPE
    )
    output = json.loads(proc.communicate()[0].decode())
    if output:
        return output[0]["EnclaveCID"]
    else:
        return None


def process_command():
    parser = argparse.ArgumentParser(prog="Enclave Client")
    subparsers = parser.add_subparsers(help="Choose command")

    # parser for "proxy" command
    parser_sync = subparsers.add_parser(
        "proxy", help="Start vsocks proxy to allow enclave server to connect outbound"
    )
    parser_sync.add_argument(
        "-s",
        "--svc",
        type=str,
        choices=["kms"],
        help="Provide which AWS service to allow access to",
    )
    parser_sync.set_defaults(func=proxy)

    # parser for "sync" command
    parser_sync = subparsers.add_parser(
        "sync", help="Sync local folder to enclave /tmp/client filesystem"
    )
    parser_sync.add_argument("-d", "--dir", type=str, help="Provide empty local folder")
    parser_sync.set_defaults(func=sync)

    # parser for "run" command
    parser_run = subparsers.add_parser(
        "run", help="Application code to run inside enclave"
    )
    parser_run.add_argument(
        "-f", "--file", type=str, help="Provide encrypted application code file name"
    )
    parser_run.add_argument(
        "-s", "--script", type=str, help="Provide script file name to run"
    )
    parser_run.add_argument(
        "-a", "--script_args", type=str, help="Provide script file arguments"
    )
    parser_run.set_defaults(func=run)

    args = parser.parse_args()
    args.func(args)


# Command "proxy"
def proxy(args):
    # Start a proxy to the specified AWS service
    if args.svc == "kms":
        subprocess.Popen(
            [
                "vsock-proxy",
                str(PROXY_PORT),
                "kms.eu-west-1.amazonaws.com",
                "443",
                "--config",
                "network/proxy-config-kms.yaml",
            ]
        )


# Command "sync"
def sync(args):
    # Open communication channel
    rpc_client_sync = RPCClient(get_cid(), PORT_SYNC)
    # Mount directory from args.dir to sync with enclave /tmp/client filesystem
    rfs_client = RFSClient(rpc_client_sync)
    # Set foreground to True if you need to debug filesystem operations
    FUSE(rfs_client, args.dir, nothreads=True, foreground=False, allow_other=False)


# Command "run"
def run(args):
    # get credentials from EC2 instance's metadata
    res = requests.get(
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
    )
    instance_role_name = res.text
    res = requests.get(
        f"http://169.254.169.254/latest/meta-data/iam/security-credentials/{instance_role_name}"
    )
    response = res.json()

    credentials = {
        "access": response["AccessKeyId"],
        "secret": response["SecretAccessKey"],
        "token": response["Token"],
    }

    # Open communication channel
    rpc_client_run = RPCClient(get_cid(), PORT_RUN)
    rpc_client_run.run(credentials, args.file, args.script, args.script_args)

    print(f"Success. Script {args.script} executed. Check synced folder for output.")


def main():
    enclave_cid = get_cid()
    if enclave_cid is None:
        print("Error. No running enclave has been detected.")
        return 1

    # Process user command
    process_command()


if __name__ == "__main__":
    main()
