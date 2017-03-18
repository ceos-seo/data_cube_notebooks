from django.forms import EmailField
from django.core.exceptions import ValidationError
import string
import random


def isEmailAddressValid(email):
    try:
        EmailField().clean(email)
        return True
    except ValidationError:
        return False
