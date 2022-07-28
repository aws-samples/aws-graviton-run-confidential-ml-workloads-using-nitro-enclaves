import argparse
import base64
import shutil
import sys

import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet

REGION = "eu-west-1"
HEADER_LEN = 4


def generate_key(cmk_key):
    # Generate a data key associated with the CMK
    # The data key will be used to encrypt files
    kms_client = boto3.client("kms", region_name=REGION)

    try:
        response = kms_client.generate_data_key(KeyId=cmk_key, KeySpec="AES_256")
    except ClientError:
        raise Exception(f"Error. A new data key could not be generated.")

    # Return both encrypted and plain data keys
    data_key_enc = response["CiphertextBlob"]
    data_key_plain = base64.b64encode(response["Plaintext"])

    if data_key_enc is None or data_key_plain is None:
        raise Exception(f"Error. A new data key could not be generated.")

    return data_key_enc, data_key_plain


def encrypt_file(args):
    dirname = args.dir
    cmk_key = args.key

    # Name for the zip file
    filename = "application_code"

    # Zip the directory provided
    shutil.make_archive(filename, "zip", dirname)

    # Read the zip file into memory
    try:
        with open(filename + ".zip", "rb") as file:
            data = file.read()
    except IOError:
        raise Exception(f"Error. Could not read file {filename}.")

    # Generate a new data key from the CMK key
    data_key_enc, data_key_plain = generate_key(cmk_key)

    # Encrypt the data file
    f = Fernet(data_key_plain)
    data_enc = f.encrypt(data)

    # Write encrypted file and encrypted data key in the same file
    try:
        with open(filename + ".zip.encrypted", "wb") as fh:
            # header
            fh.write(len(data_key_enc).to_bytes(HEADER_LEN, byteorder="big"))
            # data key
            fh.write(data_key_enc)
            # zipped directory
            fh.write(data_enc)
    except IOError:
        raise Exception(f"Error. File {filename} could not be encrypted.")

    print(
        f"Success. Directory {dirname} has been encrypted and the output file is {filename}.zip.encrypted."
    )


def process_command():
    parser = argparse.ArgumentParser(prog="Encryption Utility")
    subparsers = parser.add_subparsers(help="Choose command")

    # parser for "encrypt" command
    parser_enc = subparsers.add_parser(
        "encrypt", help="Encrypt directory with a new generated data key."
    )
    parser_enc.add_argument(
        "-d",
        "--dir",
        required=True,
        help="Directory with files to encrypt. One zip file will be generated and encrypted.",
    )
    parser_enc.add_argument(
        "-k", "--key", required=True, help="KMS CMK ID to use to encrypt the file."
    )
    parser_enc.set_defaults(func=encrypt_file)

    args = parser.parse_args()
    args.func(args)


def main():
    try:
        process_command()
    except Exception as e:
        print(e)
        sys.exit("Program is exiting...")

    return 0


if __name__ == "__main__":
    main()
