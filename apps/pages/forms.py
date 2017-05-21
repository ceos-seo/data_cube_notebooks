from django import forms
from django.utils.translation import ugettext_lazy as _


class SubmitFeedbackForm(forms.Form):
    reasons = [('General Comments', 'General Comments'), ('Bug Report', 'Bug Report'),
               ('Feature Request', 'Feature Request'), ('Problems With Account', 'Problems With Account')]
    feedback_reason = forms.ChoiceField(label='Reason for Feedback:', choices=reasons)
    feedback = forms.CharField(
        label=('Additional Comments'),
        max_length=2500,
        widget=forms.Textarea(attrs={'cols': 65,
                                     'rows': 30,
                                     'style': 'resize: none;'}))
