import io
import tarfile
import time
from collections import namedtuple
from operator import attrgetter

from django.conf import settings
from django.template import loader

from insekta.pki.models import Certificate


_CertEntry = namedtuple('_CertEntry', ['filename', 'cert', 'enabled'])

def write_vpn_bundle(user, fileobj):
    # For historical reasons a user might have multiple valid certificates
    # so we take the one which expires latest
    certificates = [cert for cert in Certificate.objects.filter(user=user)
                    if cert.is_valid]
    certificates.sort(key=attrgetter('expires'), reverse=True)
    certificate = certificates[0] if certificates else None

    mtime = int(time.time())
    with tarfile.open(mode='w|gz', fileobj=fileobj) as archive:
        client_conf = loader.render_to_string('vpn/client.conf', {
            'remote': settings.VPN_SERVER,
            'certificate': certificate
        }).encode()
        _add_bytes(archive, 'insekta-vpn/client.conf', mtime, client_conf)

        readme = loader.render_to_string('vpn/README.txt').encode()
        _add_bytes(archive, 'insekta-vpn/README.txt', mtime, readme)

        with open(settings.CA_CERTIFICATE_FILE, 'rb') as f:
            ca_crt = f.read()
        _add_bytes(archive, 'insekta-vpn/ca.crt', mtime, ca_crt)

        filename = 'insekta-vpn/client.crt'
        pem_data = certificate.pem_data.encode()
        _add_bytes(archive, filename, mtime, pem_data)

def _add_bytes(archive, filename, mtime, content):
    info = tarfile.TarInfo(filename)
    info.size = len(content)
    info.mtime = mtime
    info.type = tarfile.REGTYPE
    archive.addfile(info, io.BytesIO(content))
