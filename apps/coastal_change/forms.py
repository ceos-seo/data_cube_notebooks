from django import forms
import datetime
from data_cube_ui.models import Baseline


class AreaExtentForm(forms.Form):
    """
    Django form for taking geospatial information for Query requests:
        latitude_min
        latitude_min
        longitude_min
        longitude_max
    """
    two_column_format = True

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

    def __init__(self, satellite=None, *args, **kwargs):
        super(AreaExtentForm, self).__init__(*args, **kwargs)


class TwoDateForm(forms.Form):
    two_column_format = True

    old = forms.ChoiceField(
        help_text='Select the date of a historic acquisition.',
        label="Beginning Year",
        choices=[(number, number) for number in range(1999, 2017)],
        widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

    new = forms.ChoiceField(
        help_text='Select the date of a new acquisition',
        label="Ending Year",
        choices=[(number, number) for number in range(1999, 2017)],
        widget=forms.Select(attrs={'class': 'field-long tooltipped'}))

    def __init__(self, satellite=None, *args, **kwargs):
        super(TwoDateForm, self).__init__(*args, **kwargs)


class AnimationToggleForm(forms.Form):
    two_column_format = False

    animated_product = forms.ChoiceField(
        help_text='Select your animated product',
        label="Animated Product:",
        choices=[('None', 'None'), ('yearly', 'Year-by-year animation')],
        widget=forms.Select(attrs={'class': 'tooltipped'}))

    def __init__(self, satellite=None, *args, **kwargs):
        super(AnimationToggleForm, self).__init__(*args, **kwargs)
