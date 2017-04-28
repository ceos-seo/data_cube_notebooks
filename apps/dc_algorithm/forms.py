from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class DataSelectionForm(forms.Form):

    two_column_format = True

    title = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'class': 'hidden_form_title'}))
    description = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'class': 'hidden_form_description'}))
    platform = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'hidden_form_platform'}))
    area_id = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'hidden_form_area_id'}))

    latitude_min = forms.FloatField(
        label='Min Latitude',
        widget=forms.NumberInput(attrs={'class': 'field-divided',
                                        'step': "any",
                                        'required': 'required'}))
    latitude_max = forms.FloatField(
        label='Max Latitude',
        widget=forms.NumberInput(attrs={'class': 'field-divided',
                                        'step': "any",
                                        'required': 'required'}))
    longitude_min = forms.FloatField(
        label='Min Longitude',
        widget=forms.NumberInput(attrs={'class': 'field-divided',
                                        'step': "any",
                                        'required': 'required'}))
    longitude_max = forms.FloatField(
        label='Max Longitude',
        widget=forms.NumberInput(attrs={'class': 'field-divided',
                                        'step': "any",
                                        'required': 'required'}))
    time_start = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(
            attrs={'class': 'datepicker field-divided',
                   'placeholder': '01/01/2010',
                   'required': 'required'}))
    time_end = forms.DateField(
        label='End Date',
        widget=forms.DateInput(
            attrs={'class': 'datepicker field-divided',
                   'placeholder': '01/02/2010',
                   'required': 'required'}))

    def __init__(self, *args, **kwargs):
        time_start = kwargs.pop('time_start', None)
        time_end = kwargs.pop('time_end', None)
        super(DataSelectionForm, self).__init__(*args, **kwargs)
        #meant to prevent this routine from running if trying to init from querydict.
        if time_start and time_end:
            self.fields['time_start'] = forms.DateField(
                initial=time_start.strftime("%m/%d/%Y"),
                label='Start Date',
                widget=forms.DateInput(attrs={'class': 'datepicker field-divided',
                                              'required': 'required'}))
            self.fields['time_end'] = forms.DateField(
                initial=time_end.strftime("%m/%d/%Y"),
                label='End Date',
                widget=forms.DateInput(attrs={'class': 'datepicker field-divided',
                                              'required': 'required'}))

    def clean(self):
        cleaned_data = super(DataSelectionForm, self).clean()
        #self.add_error('region', _("Selected region does not exist."))
        if cleaned_data.get('latitude_min') > cleaned_data.get('latitude_max'):
            self.add_error(
                'latitude_min',
                "Please enter a valid pair of latitude values where the lower bound is less than the upper bound.")

        if cleaned_data.get('longitude_min') > cleaned_data.get('longitude_max'):
            self.add_error(
                'longitude_min',
                "Please enter a valid pair of longitude values where the lower bound is less than the upper bound.")

        if cleaned_data.get('time_start') > cleaned_data.get('time_end'):
            self.add_error('time_start',
                           "Please enter a valid start and end time range where the start is before the end.")
