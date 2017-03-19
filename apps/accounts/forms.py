from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')


class LoginForm(forms.Form):
    username = forms.CharField(label=_('Username'), max_length=100)
    password = forms.CharField(label=_('Password'), max_length=100, widget=forms.PasswordInput)


class RegistrationForm(forms.Form):
    username = forms.CharField(label=_('Username'), max_length=100, validators=[alphanumeric])
    password = forms.CharField(label=_('Password'), max_length=100, widget=forms.PasswordInput, validators=[validate_password])
    confirm_password = forms.CharField(label=_('Confirm Password'), max_length=100, widget=forms.PasswordInput)
    email = forms.EmailField(label=_('Email'))
    confirm_email = forms.EmailField(label=_('Confirm Email'))

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()

        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('confirm_password')
        email = cleaned_data.get('email')
        email_confirm = cleaned_data.get('confirm_email')

        if password != password_confirm:
            self.add_error('password', _("Your passwords do not match, please try again."))
            self.add_error('confirm_password', _(""))
        elif email != email_confirm:
            self.add_error('email', _("Your emails do not match, please try again."))
            self.add_error('confirm_email', _(""))
        elif len(User.objects.filter(username=username)) != 0:
            self.add_error('username', _("That username is already taken, please try another."))
        elif len(User.objects.filter(email=email)) != 0:
            self.add_error('email', _("This email is already registered to another account. Please log in or reset your password to obtain your username."))


class PasswordChangeForm(forms.Form):
    password = forms.CharField(label=_('Password'), max_length=100, widget=forms.PasswordInput)
    new_password = forms.CharField(label=_('New Password'), max_length=100, widget=forms.PasswordInput, validators=[validate_password])
    new_password_confirm = forms.CharField(label=_('New Password Confirmation'), max_length=100, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(PasswordChangeForm, self).clean()

        password = cleaned_data.get('password')
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')

        if new_password != new_password_confirm:
            self.add_error('new_password', _("Your passwords do not match, please try again."))
            self.add_error('new_password_confirm', _(""))


class LostPasswordForm(forms.Form):
    email = forms.EmailField(label=_('Email'))
    confirm_email = forms.EmailField(label=_('Confirm Email'))

    def clean(self):
        cleaned_data = super(LostPasswordForm, self).clean()

        email = cleaned_data.get('email')
        email_confirm = cleaned_data.get('confirm_email')

        if email != email_confirm:
            self.add_error('email', _("Your emails do not match, please try again."))
            self.add_error('confirm_email', _(""))
        user = User.objects.filter(email=email)
        if len(user) == 0:
            self.add_error('email', _("This email is not registered to any account. Please enter a valid email"))
            self.add_error('confirm_email', _(""))


class PasswordResetForm(forms.Form):
    new_password = forms.CharField(label=_('New Password'), max_length=100, widget=forms.PasswordInput, validators=[validate_password])
    new_password_confirm = forms.CharField(label=_('New Password Confirmation'), max_length=100, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(PasswordResetForm, self).clean()

        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')

        if new_password != new_password_confirm:
            self.add_error('new_password', _("Your passwords do not match, please try again."))
            self.add_error('new_password_confirm', _(""))
