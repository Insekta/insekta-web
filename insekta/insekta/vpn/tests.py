import io

from django.test import TestCase
from django.contrib.auth import get_user_model

from insekta.vpn.bundlebuilder import write_vpn_bundle
from insekta.pki.models import Certificate


VALID_CSR = '''
-----BEGIN CERTIFICATE REQUEST-----
MIICZTCCAU0CAQAwDzENMAsGA1UEAwwEdGVzdDCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBAKbvDhmFXEDV5V7dMDhW/NZltEp+RVpZPdgxli5tniI7W6xL
W6gRWlT4RqJKB7I4oLfmIQonnMtB4XF6J7TTEu49WPNZNa1Bthe5cHq8oTkeSPK2
hwVT1m/bq+FaRyLTCHk6FMvZnppH56yPSGKoKZD6Oee52fX2ZfRQphaD3IvARiDJ
CsIlgQ4eh0CO8s3NTYaDlpcR/wRYTzaFKYAXovvqsaDPiTcGP3jtYBB31DUtL2dP
FfKTQ5XuifEk3UQ+G2iXcwlNLnzKHtTDFb389oF4PZhTcNaAEoNWfH/BSdtveTBM
sf9DEcAKlJoBN1Mdpwr6TG1uOjXftuEC8fH0dpcCAwEAAaARMA8GCSqGSIb3DQEJ
DjECMAAwDQYJKoZIhvcNAQELBQADggEBABtFgxNY4ns4KU9/DJeyVohMpHEen0ys
GWfxaUxQGDmU+z4pWBaBBNPLm6cKm7MWM8ZXqnCJGK4B8/IIPBT8L6cawXzwm5gB
bxYDAomEP3k0BpHwcQAUkefbeyorHmbLYXmzKCYJ5rXw+XLVtWl3CaQlQSYUYUQo
7uXM13bqmtcLoIgOsLUU4Jp8NeM+SeoP18WvTnAeKkezElKAqXdhhaUH2vQ0Tc5G
rK/+0M9u0M8AhYPmy7rfGfunGx6OAcyn7Ybxk0zI/8V9wmFHjHhPJtr1LL5Qwvnw
gH82jkoPiWzvlXBXW76sFkDihsFCNShosNpjLHW9CX/sPZ4XlZNau+I=
-----END CERTIFICATE REQUEST-----
'''


class BuilderTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username='test')
        Certificate.create_from_csr(self.user, VALID_CSR)

    def test_builder(self):
        fileobj = io.BytesIO()
        write_vpn_bundle(self.user, fileobj)
