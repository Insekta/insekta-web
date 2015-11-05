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
    certificates = [cert for cert in Certificate.objects.filter(user=user)
                    if cert.is_valid]
    certificates.sort(key=attrgetter('expires'))

    cert_entries = []
    last_index = len(certificates)-1
    for i, cert in enumerate(certificates):
        cert_entries.append(_CertEntry(
            filename='cert_{}.crt'.format(str(i + 1).zfill(2)),
            cert=cert,
            enabled=i == last_index
        ))

    mtime = int(time.time())
    with tarfile.open(mode='w|gz', fileobj=fileobj) as archive:
        client_conf = loader.render_to_string('vpn/client.conf', {
            'remote': settings.VPN_SERVER,
            'certificate_entries': cert_entries
        }).encode()
        _add_bytes(archive, 'insekta-vpn/client.conf', mtime, client_conf)

        readme = loader.render_to_string('vpn/README.txt').encode()
        _add_bytes(archive, 'insekta-vpn/README.txt', mtime, readme)

        with open(settings.CA_CERTIFICATE_FILE, 'rb') as f:
            ca_crt = f.read()
        _add_bytes(archive, 'insekta-vpn/ca.crt', mtime, ca_crt)

        for cert_entry in cert_entries:
            filename = 'insekta-vpn/' + cert_entry.filename
            pem_data = cert_entry.cert.pem_data.encode()
            _add_bytes(archive, filename, mtime, pem_data)

def _add_bytes(archive, filename, mtime, content):
    info = tarfile.TarInfo(filename)
    info.size = len(content)
    info.mtime = mtime
    info.type = tarfile.REGTYPE
    archive.addfile(info, io.BytesIO(content))
