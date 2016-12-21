from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password

class SubmitFeedbackForm(forms.Form):
    reasons = [('General Comments', 'General Comments'), ('Bug Report','Bug Report'), ('Feature Request', 'Feature Request'), ('Problems With Account', 'Problems With Account')]
    
    feedback = forms.CharField(label=('Additional Comments'), max_length=2500, widget=forms.Textarea(attrs={'cols': 65, 'rows': 30, 'style': 'resize: none;'}))
    feedback_reason = forms.ChoiceField(label='Reason for Feedback:', choices=reasons)
