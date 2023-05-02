from django.urls import path

from insekta.pki import views


app_name = 'pki'
urlpatterns = [
    path('', views.index, name='index'),
    path('create_certificate_csr', views.create_certificate, name='create_certificate'),
    path('create_certificate_auto', views.create_certificate_auto, name='create_certificate_auto'),
    path('revoke_certificate', views.revoke_certificate, name='revoke_certificate'),
]
