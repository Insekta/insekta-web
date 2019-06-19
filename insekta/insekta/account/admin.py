from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from insekta.account.models import User


class CustomUserAdmin(UserAdmin):
    change_form_template = 'loginas/change_form.html'


admin.site.register(User, CustomUserAdmin)
