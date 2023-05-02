from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=40)
    last_name = forms.CharField(max_length=40)
    email = forms.EmailField()
    invitation_code = forms.CharField(max_length=100)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name',
                                                 'invitation_code', 'email')

    def clean_invitation_code(self):
        if self.cleaned_data['invitation_code'] != settings.INVITATION_CODE:
            raise forms.ValidationError(_('Invalid invitation code.'))
        return self.cleaned_data['invitation_code']



@login_required
def index(request):
    return render(request, 'account/index.html', {
        'active_nav': 'account'
    })


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['first_name']
            user.save()
            messages.success(request, _('Account created successfully.'))
            return redirect('account:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/register.html', {
        'form': form
    })
