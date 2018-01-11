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
from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
from django.views.static import serve

from insekta.base import views as base_views


urlpatterns = [
    url(r'^$', base_views.index, name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('insekta.account.urls')),
    url(r'^topics/', include('insekta.scenarios.urls')),
    url(r'^help/', include('insekta.scenariohelp.urls')),
]

if 'insekta.ethics' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^ethics/', include('insekta.ethics.urls')),
    ]

if 'insekta.vpn' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^pki/', include('insekta.pki.urls')),
        url(r'^vpn/', include('insekta.vpn.urls')),
    ]

if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
   ]
