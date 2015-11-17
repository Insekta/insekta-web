from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'account/index.html', {
        'show_vpn': 'insekta.vpn' in settings.INSTALLED_APPS
    })
