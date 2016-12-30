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

class GeospatialForm(forms.Form):
    """
    Django form for taking geospatial information for Query requests:
        latitude_min
        latitude_min
        longitude_min
        longitude_max
        time_start
        time_end
    """

    latitude_min = forms.FloatField(label='Min Latitude', widget = forms.NumberInput(attrs={'class': 'field-divided', 'step': "any", 'required': 'required'}))
    latitude_max = forms.FloatField(label='Max Latitude', widget = forms.NumberInput(attrs={'class': 'field-divided', 'step': "any", 'required': 'required'}))
    longitude_min = forms.FloatField(label='Min Longitude', widget = forms.NumberInput(attrs={'class': 'field-divided', 'step': "any", 'required': 'required'}))
    longitude_max = forms.FloatField(label='Max Longitude', widget = forms.NumberInput(attrs={'class': 'field-divided', 'step': "any", 'required': 'required'}))
    time_start = forms.DateField(label='Start Date', widget=forms.DateInput(attrs={'class': 'datepicker field-divided', 'placeholder': '01/01/2010', 'required': 'required'}))
    time_end = forms.DateField(label='End Date', widget=forms.DateInput(attrs={'class': 'datepicker field-divided', 'placeholder': '01/02/2010', 'required': 'required'}))

    def __init__(self, satellite=None, *args, **kwargs):
        super(GeospatialForm, self).__init__(*args, **kwargs)
        if satellite is not None:
            self.fields['time_start'] = forms.DateField(initial=satellite.date_min.strftime("%m/%d/%Y"), label='Start Date', widget=forms.DateInput(attrs={'class': 'datepicker field-divided', 'required': 'required'}))
            self.fields['time_end'] = forms.DateField(initial=satellite.date_max.strftime("%m/%d/%Y"), label='End Date', widget=forms.DateInput(attrs={'class': 'datepicker field-divided', 'required': 'required'}))
