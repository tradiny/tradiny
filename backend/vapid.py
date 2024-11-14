# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import os
import logging

from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode

from config import Config

from utils import resource_path

vapid = None


def private_key_to_string(private_key):
    """Convert a private key to a string"""
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def get_vapid():
    global vapid
    return vapid


def generate():
    global vapid

    private_key_path = get_private_key_path()
    if not os.path.isfile(private_key_path):
        vapid = Vapid()
        vapid.generate_keys()

        private_key_string = vapid.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        with open(private_key_path, "wb") as f:
            f.write(private_key_string)

        logging.info("New VAPID keys generated and saved.")
    else:
        with open(private_key_path, "rb") as f:
            private_key_string = f.read()
        vapid = Vapid.from_pem(
            private_key_string
        )  # parse the string to get the key object
        logging.info("VAPID keys loaded.")

    return vapid


def get_private_key_path():
    return resource_path(Config.VAPID_KEY_PATH)


def save_private_key_to_file(private_key_string, file_path):
    with open(file_path, "w") as f:
        f.write(private_key_string)


def load_private_key_from_file(private_key_path):
    with open(private_key_path, "rb") as f:
        pem = f.read()

    private_key = serialization.load_pem_private_key(
        pem, password=None, backend=default_backend()
    )

    return private_key


def get_private_key():
    private_key_path = get_private_key_path()
    if os.path.isfile(private_key_path):
        return load_private_key_from_file(private_key_path)
    else:
        raise FileNotFoundError("No VAPID keys found. Run generate() first.")


def get_public_key():
    global vapid

    # Export raw public key instead of default PEM format
    raw_public_key = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return raw_public_key


def get():
    global vapid

    # Export raw public key instead of default PEM format
    raw_public_key = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Extract EC point from DER encoded format
    ec_point = raw_public_key[26:]

    # No need to replace BEGIN/END lines when exporting in raw DER format
    b64_public_key = urlsafe_b64encode(ec_point).decode("utf-8")

    return {"publicKey": b64_public_key}
