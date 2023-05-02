"""insekta URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""


from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.views.static import serve
from django.apps import apps

from insekta.base import views as base_views



urlpatterns = [
    path('', base_views.index, name='index'),
    path('admin/', admin.site.urls),
    path('account/', include('insekta.account.urls', namespace='account')),
    path('topics/', include('insekta.scenarios.urls', namespace='scenarios')),
    path('help/', include('insekta.scenariohelp.urls', namespace='scenariohelp')),
]

if apps.is_installed('insekta.ethics'):
    urlpatterns += [
        path('ethics/', include('insekta.ethics.urls', namespace='ethics')),
    ]

if apps.is_installed('insekta.vpn'):
    urlpatterns += [
        path('pki/', include('insekta.pki.urls', namespace='pki')),
        path('vpn/', include('insekta.vpn.urls', namespace='vpn')),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += path('admin/', include('loginas.urls')),
