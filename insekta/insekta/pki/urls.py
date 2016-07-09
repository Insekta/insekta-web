from django.conf.urls import url

from insekta.pki import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'create_certificate_csr$', views.create_certificate, name='create_certificate'),
    url(r'create_certificate_auto$', views.create_certificate_auto, name='create_certificate_auto'),
    url(r'revoke_certificate$', views.revoke_certificate, name='revoke_certificate'),
]
