import datetime
import uuid

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509.oid import NameOID


class SignError(Exception):
    pass


class CSRSigner:
    valid_hash_algorithms = (hashes.SHA224, hashes.SHA256, hashes.SHA384,
                             hashes.SHA512)

    def __init__(self, ca_key_file, ca_cert_file):
        self.backend = default_backend()
        with open(ca_key_file, 'rb') as f:
            pem_data = f.read()
        self.ca_key = serialization.load_pem_private_key(
            pem_data, password=None, backend=self.backend)
        with open(ca_cert_file) as f:
            pem_data = f.read()
        self.ca_cert = pem_to_cert(pem_data)

    def sign_csr(self, csr_pem, username):
        if isinstance(csr_pem, str):
            csr_pem = csr_pem.encode()
        try:
            csr = x509.load_pem_x509_csr(csr_pem, self.backend)
        except ValueError:
            raise SignError('Invalid CSR.')
        if not isinstance(csr.signature_hash_algorithm, self.valid_hash_algorithms):
            raise SignError('CSR is not signed with an accepted hash algorithm.')
        return self.sign_public_key(csr.public_key(), username)

    def sign_public_key(self, public_key, username):
        if isinstance(public_key, rsa.RSAPublicKey) and public_key.key_size < 2048:
            raise SignError('RSA modulus must be at least 2048 bits.')

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, username),
        ]))
        builder = builder.issuer_name(self.ca_cert.subject)
        one_day = datetime.timedelta(1, 0, 0)
        one_year = datetime.timedelta(365, 0, 0)
        now = datetime.datetime.utcnow()
        start_date = now - one_day
        expire_date = now + one_year
        builder = builder.not_valid_before(start_date)
        builder = builder.not_valid_after(expire_date)
        builder = builder.serial_number(int(uuid.uuid4()))
        builder = builder.public_key(public_key)
        builder = builder.add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True)
        certificate = builder.sign(
            private_key=self.ca_key,
            algorithm=hashes.SHA256(),
            backend=self.backend)
        return certificate


def generate_private_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend())


def key_to_pem(key):
    return key.private_bytes(encoding=serialization.Encoding.PEM,
                             format=serialization.PrivateFormat.TraditionalOpenSSL,
                             encryption_algorithm=serialization.NoEncryption()).decode()


def cert_to_pem(cert: x509.Certificate):
    return cert.public_bytes(serialization.Encoding.PEM).decode()


def pem_to_cert(pem: str):
    return x509.load_pem_x509_certificate(pem.encode(), default_backend())
