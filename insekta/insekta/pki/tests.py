import tempfile
from cryptography import x509
from django.test import TestCase

from .certs import CSRSigner, SignError, cert_to_pem, pem_to_cert


PRIVATE_KEY = '''
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAx+3vaJYjXY95IagEwmcR4HBisWGMnu+3h9MOEx0PT46Kgwux
ZpRruNOxokP/xCMDnLLKUIr3dppyNsnfNeI/EO96VH/NJdDcE60iP2q9HJsPsMMF
OktKddm5VPBw7kUPEb4yY0uQSkiGnshDGqMiAr6VBbzSJGuoWIt2Yg9mC+wmBPD+
8xxtBrI6BnrhEWYBOCZRFdQR9ANNvagdtqEZoMtkuC3wFkV5aNt1oLIeBFI9CFgH
/MpsClWesaYJMfYlf7ZZXnlS7rhj+MxYR+wa2zgHZe18yncNtnEcwR11r0t6NBRn
vpCCWtYtVpDxyqtGQNr8GI6Fwk09YLhgryB8IQIDAQABAoIBAFUIjATtpokKlriL
38pXUDEnW7KaDNckmei5CYlzmKl7tMnb1U4N3ms0Dp83ULc5NTYWjRoIoQve0Kkg
30Dpw20OjfcWjEiDNrdfsetLGLfr85Z4u+Z5U2ggfET2JvIQiUJApOm6n9oYUrmB
75iKvdJxAKz6DF7VMzrFxkoaxopW27jYsQ6t/ur4yQJEewfmsrGQIjCkn/5u0+Aq
qNrapUaFG+DlIvSlrd6+c7laa6GEIBrqCMowxaw0yQ+AiKhi0LjKcZq+Dc6LfPpS
3CuRGa+Uri3+/1K9nMnTDtBPjhbFkCONAPDjVx0wUsvq6xFY+j6npL9WPyQe6QXg
772gdWECgYEA5DsHbMSJ3MuB7JMj7AymSZgM+sdUCUsuijFnrDJvSVlzRfhuE0lY
AmjIqNVWEEWUqJWc37wTjD+t1xjty2X35gQzL2grlqiQn3/J8Fj8/1+UPypy+7/R
8IMEqIJjePp/FB2Kt87xoLaX0dnER5Fo/QQPMb1EvYStM7pNi299noUCgYEA4EFg
YOfFaScdYh+odsmfpAFs5aomnFmQZNmKehlQSRhauYoMpMdpSAKWQhQGBouWPQFS
zyoD23dQWltyT8Cu3jm+LYh2w+2bnwV0mP3ISJIxWXJMHJ/E6f656Ft4OYVbKvM0
eMuPmVIIK7o+ii/RMh117H6QkcsidgQmyBwqP+0CgYEAglhoHCl/JvefQzKhwG1V
BxDs0MjIaOpkMQ6YTBMd1cFdgWepziAEQJQBjdMRbQegKEwSJQFwFJhFu2QEYzbg
RqC9buTKiCfLORytgzP/ggXfT9f5hWf/CaJ6JZcaInzF2QIqOGHbQ9Mkj/gUDl+w
m1gXKWwT9zzwAmvzX6AUGVUCgYA0jH1GF+l1a3oCLULvmu1yo/bdllJ33rDsQOGn
HNloV3Gi+otd7XBpNFn7X+/NhtYMs4uxCbpfqgTFN5qAv7j6T/OVfd2+qaYGzGN3
GjjdcIxp1lOpfXLKFiuAHDb+25XyaY0JJUIf/k312S2gefX+VVL1uO6tizknCHAC
Aj+QPQKBgEpadFDh4NIccjfdCzY9k3Y3jKZmBUjg2JAo4tc9elXEkoHeU6ChTgd+
3utQARxgaRqBgBHCiIQjaK+sEAh1NToETKjz6QRds13ab/NA2BamDywysXiqchxe
kFeXE9zvHrCcdQBAB7DULJrP2v1ssyhFObs8y6NxcJ3dcfiRmzrZ
-----END RSA PRIVATE KEY-----
'''

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

INVALID_CSR = '''
---BEGIN CERTIFICATE REQUEST-----
MIICZTCCAU0CAQAwDzENMAsGA1UEAwwEdGVzdDCCASIwDQYJKoZIhvcNAQEBBQAD
-----END CERTIFICATE REQUEST-----
'''

VALID_CSR_MD5 = '''
-----BEGIN CERTIFICATE REQUEST-----
MIICZTCCAU0CAQAwDzENMAsGA1UEAwwEdGVzdDCCASIwDQYJKoZIhvcNAQEBBQAD
ggEPADCCAQoCggEBAKbvDhmFXEDV5V7dMDhW/NZltEp+RVpZPdgxli5tniI7W6xL
W6gRWlT4RqJKB7I4oLfmIQonnMtB4XF6J7TTEu49WPNZNa1Bthe5cHq8oTkeSPK2
hwVT1m/bq+FaRyLTCHk6FMvZnppH56yPSGKoKZD6Oee52fX2ZfRQphaD3IvARiDJ
CsIlgQ4eh0CO8s3NTYaDlpcR/wRYTzaFKYAXovvqsaDPiTcGP3jtYBB31DUtL2dP
FfKTQ5XuifEk3UQ+G2iXcwlNLnzKHtTDFb389oF4PZhTcNaAEoNWfH/BSdtveTBM
sf9DEcAKlJoBN1Mdpwr6TG1uOjXftuEC8fH0dpcCAwEAAaARMA8GCSqGSIb3DQEJ
DjECMAAwDQYJKoZIhvcNAQEEBQADggEBAFUg+1lp6cVJOQLqS/yde2DeYs36UCB4
/JRAHdNyQA2EmqaHlTCzhwb+jiBHaVRLMjk4rG24SqQ86+GTurvz1QtaL5DOUKYD
HMYMr+Fg9rXRod32VqzvY0Au7Rjrtcr5B50R0vcJLzAtMfScTuyzYAtkRHZGL0bd
4k2/3sPbFWO+gopRisoUGeSs/8NvK8eG3i4qnzUgY74RGWOk8tB5kasHqRc+3Uu/
ITrWbUhWQYtWqPyqpQRloffYsiI4gw8FkkKmkn3xFtYvYgm4Upy3vXY1W5UNEb+s
HB09mXudXVSkmAV/Tnqn3lq1ITOzmnzboYxcVmG/0vco74SVJw99hMk=
-----END CERTIFICATE REQUEST-----
'''


class SignerTestCase(TestCase):
    def test_sign_csr(self):
        with tempfile.NamedTemporaryFile(mode='w') as f:
            f.write(PRIVATE_KEY)
            f.flush()
            signer = CSRSigner(f.name, 'Insekta')
        cert = signer.sign_csr(VALID_CSR, 'test')
        self.assertIsInstance(cert, x509.Certificate)
        # TODO: Some more checks

        self.assertEqual(pem_to_cert(cert_to_pem(cert)), cert)

        with self.assertRaises(SignError):
            signer.sign_csr(INVALID_CSR, 'test')
        with self.assertRaises(SignError):
            signer.sign_csr(VALID_CSR_MD5, 'test')
