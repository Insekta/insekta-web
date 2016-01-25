from django.contrib import admin

from insekta.remoteapi.models import VMResourceDummy


class VMResourceDummyAdmin(admin.ModelAdmin):
    list_display = ('resource_name', 'is_started', 'vpn_enabled', 'vm_names')


admin.site.register(VMResourceDummy, VMResourceDummyAdmin)
