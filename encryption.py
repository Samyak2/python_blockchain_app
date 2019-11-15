from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from base64 import b64encode, b64decode

def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def save_private_key(private_key, filename):
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    with open(filename, 'wb') as f:
        f.write(pem)

def get_private_key_string(private_key):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

def save_public_key(public_key, filename):
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(filename, 'wb') as f:
        f.write(pem)

def get_public_key_string(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def read_private_key(filename):
    with open(filename, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def read_private_key_string(s):
    private_key = serialization.load_pem_private_key(
        s,
        password=None,
        backend=default_backend()
    )
    return private_key

def read_public_key(filename):
    with open(filename, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    return public_key

def read_public_key_string(s):
    public_key = serialization.load_pem_public_key(
        s,
        backend=default_backend()
    )
    return public_key


def encrypt_message(message, public_key):
    encrypted = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return b64encode(encrypted)


def decrypt_message(encrypted, private_key):
    try:
        original_message = private_key.decrypt(
            b64decode(encrypted),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    except ValueError:
        original_message = "**Decryption Error**"
    return original_message

if __name__ == "__main__":
    message = bytes("Hello World!!!!!!!!!!!!!!!!!", encoding="UTF-8")
    private_key = read_private_key("private_key.pem")
    public_key = read_public_key("public_key.pem")
    print("Public Key: ", public_key)
    print("Private Key: ", private_key)
    encrypted = encrypt_message(message, public_key)
    print(len(encrypted))
    original_message = decrypt_message(encrypted, private_key)
    print(original_message)