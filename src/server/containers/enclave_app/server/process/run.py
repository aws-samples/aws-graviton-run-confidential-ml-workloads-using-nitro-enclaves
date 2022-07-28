import base64
import os
import shutil
import subprocess

from cryptography.fernet import Fernet

PROXY_PORT = 8001
HEADER_LEN = 4

REGION = "eu-west-2"

SECRET_DIR = "/tmp/decrypted/"
APP_DIR = SECRET_DIR + "app/"

SYNC_DIR = "/tmp/client/"
ENC_DIR = SYNC_DIR + "encrypted/"


def client_path(path):
    if path.startswith("/"):
        path = path[1:]
        path = os.path.join(SYNC_DIR, path)
    return path


def decrypt_data_key(data_key_enc, credentials):
    proc = subprocess.Popen(
        [
            "/app/kmstool_enclave_cli",
            "--region",
            REGION,
            "--proxy-port",
            str(PROXY_PORT),
            "--aws-access-key-id",
            credentials["access"],
            "--aws-secret-access-key",
            credentials["secret"],
            "--aws-session-token",
            credentials["token"],
            "--ciphertext",
            data_key_enc,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    ret = proc.communicate()
    if ret[0]:
        file_dec = ret[0].decode()
        return file_dec
    else:
        raise Exception("Error. Data key decryption failed.")


def run(credentials, filename, script_name, script_args):
    os.makedirs(SECRET_DIR, exist_ok=True)

    # Locate encrypted file, expected in ENC_DIR
    try:
        with open(ENC_DIR + filename, "rb") as file:
            data = file.read()
    except Exception:
        raise Exception(f"Error. Could not read encrypted file {filename}.")

    # Extract data key length from header
    data_key_enc_len = int.from_bytes(data[:HEADER_LEN], byteorder="big") + HEADER_LEN
    # Extract encrypted data key
    data_key_enc = data[HEADER_LEN:data_key_enc_len]
    # Extract encrypted file
    file_enc = data[data_key_enc_len:]

    # Run decryption on encrypted data key
    data_key_enc = base64.b64encode(data_key_enc)
    data_key_enc = data_key_enc.decode("utf-8")
    data_key_plain = decrypt_data_key(data_key_enc, credentials)

    # Decrypt the encrypted file
    try:
        f = Fernet(data_key_plain)
        data_dec = f.decrypt(file_enc)
    except Exception:
        raise Exception(f"Error. Failed to decrypt file {filename}.")

    # Store decrypted file on disk
    file_dec = (
        SECRET_DIR + filename + ".decrypted"
    )  # Change to SYNC_DIR only for debugging

    try:
        with open(file_dec, "wb") as fh:
            fh.write(data_dec)
    except Exception:
        raise Exception(f"Error. Could not write file: {file_dec}.")

    # Unzip the decrypted application code
    shutil.unpack_archive(file_dec, APP_DIR, "zip")

    # Convert string to arguments list
    script_args = script_args.split(" ")

    # Adjust absolute paths to match SYNC_DIR
    script_args = [client_path(arg) for arg in script_args]
    args = ["python3", script_name] + script_args

    # Run decrypted script
    proc = subprocess.Popen(
        args=args, cwd=APP_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    output, err = proc.communicate()

    # Remove decrypted application code before exiting
    shutil.rmtree(APP_DIR)

    if proc.returncode != 0:
        raise Exception(
            f"Exited with error code: {proc.returncode}.\n{err.decode('utf-8')}"
        )

    return output.decode("utf-8")
