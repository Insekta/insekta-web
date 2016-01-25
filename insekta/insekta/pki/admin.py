from django.contrib import admin

from insekta.pki.models import Certificate


class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'fingerprint', 'expires', 'is_revoked')
    list_filter = ('is_revoked', )

admin.site.register(Certificate, CertificateAdmin)
