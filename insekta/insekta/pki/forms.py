from django import forms


class CreateCertificateForm(forms.Form):
    csr_pem = forms.CharField(widget=forms.Textarea)
