from django.shortcuts import render, redirect
from django.template import loader, RequestContext
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.utils import translation
from django.utils.translation import ugettext as _
from django.forms.forms import NON_FIELD_ERRORS
from django.core.mail import EmailMultiAlternatives
from django.core.mail import EmailMessage
from django.template.loader import render_to_string, get_template

from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
import smtplib

import datetime
import pytz

from .utils import isEmailAddressValid
from .models import Activation, Reset
from .forms import LoginForm, RegistrationForm, PasswordChangeForm, LostPasswordForm, PasswordResetForm

# Create your views here.


def activate(request, uuid):
    message = _("Your account has been activated, please log in.")
    try:
        activation = Activation.objects.get(url=uuid)
        if (datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - activation.time).days > 0:
            # invalid since you waited too long.
            message = _("Your activation url has expired. Please reregister.")
            user = User.objects.get(username=activation.username)
            user.delete()
            activation.delete()
        else:
            user = User.objects.get(username=activation.username)
            user.is_active = True
            user.save()
            activation.delete()
    except:
        message = _("Invalid activation url. Please try again.")

    form = LoginForm()
    form.cleaned_data = {}
    form.add_error(NON_FIELD_ERRORS, message)
    context = {
        'title': _("Log in"),
        'form': form,
    }
    return render(request, 'registration/login.html', context)


def lost_password(request):
    if request.method == "POST":
        form = LostPasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(email=form.cleaned_data['email'])
            reset = Reset(username=user[0].username, time=datetime.datetime.now())
            reset.save()

            msg = EmailMessage()
            msg['From'] = 'admin@ceos-cube.org'
            msg['To'] = form.cleaned_data['email']
            msg['Subject'] = _('DataCube Password Reset')
            msg.set_content(_('Reset your password here: ') + settings.BASE_HOST + "/accounts/" + str(reset.url) + "/reset")
            # Sending the email:
            with smtplib.SMTP('localhost') as s:
                s.send_message(msg)

            form = LoginForm()
            form.cleaned_data = {}
            form.add_error(NON_FIELD_ERRORS, _("We have sent an email containing the url required to reset your password. Please use that link then log back in."))
            context = {
                'title': _("Log in"),
                'form': form,
            }
            return render(request, 'registration/login.html', context)
        else:
            context = {'title': _("Password Reset"), 'form': form}
            return render(request, 'registration/lost_password.html', context)

    else:
        context = {'title': _("Password Reset"), 'form': LostPasswordForm()}
        return render(request, 'registration/lost_password.html', context)


def reset(request, uuid):
    try:
        reset = Reset.objects.get(url=uuid)
        if request.method == "POST":
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                user = User.objects.get(username=reset.username)
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                reset.delete()

                form = LoginForm()
                form.cleaned_data = {}
                form.add_error(NON_FIELD_ERRORS, _("Your password has been changed. Please log in."))
                context = {
                    'title': _("Log in"),
                    'form': form,
                }
                return render(request, 'registration/login.html', context)
            else:
                context = {'title': _("Password Reset"), 'user_hash': uuid, 'form': form}
                return render(request, 'registration/reset.html', context)

        else:
            if (datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - reset.time).days > 0:
                # invalid since you waited too long.
                form = LostPasswordForm()
                form.cleaned_data = {}
                form.add_error(NON_FIELD_ERRORS, _("Your password reset url has expired. Please reset it again."))
                context = {'title': _("Password Reset"), 'form': form}
                return render(request, 'registration/lost_password.html', context)
            else:
                form = PasswordResetForm()
                form.cleaned_data = {}
                form.add_error(NON_FIELD_ERRORS, _("Please enter your new password."))
                context = {'title': _("Password Reset"), 'user_hash': uuid, 'form': form}
                return render(request, 'registration/reset.html', context)

    except:
        form = LoginForm()
        form.cleaned_data = {}
        form.add_error(NON_FIELD_ERRORS, _("Invalid password reset url."))
        context = {
            'title': _("Log in"),
            'form': form,
        }
        return render(request, 'registration/login.html', context)


@login_required
def password_change(request):
    """
    Navigates to the password change page. POST will validate current password and change it,
    GET will display the form.

    **Context**
    ``message``
        An error message in the event that something is incorrect.
    ``next``
        The redirect page upon successfull login.
    **Template**

    :template:`registration/password_change.html`
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = authenticate(username=request.user.username, password=form.cleaned_data['password'])
            if user is not None:
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                auth_logout(request)
                form = LoginForm()
                form.cleaned_data = {}
                form.add_error(NON_FIELD_ERRORS, _("Your password has been changed. Please log in."))
                context = {
                    'title': _("Log in"),
                    'form': form,
                }
                return render(request, 'registration/login.html', context)
            else:
                form.add_error('password', _("Your current password is incorrect, please try again."))

        # Return an 'invalid login' error message.
        context = {
            'title': _("Password Change"),
            'form': form
        }
        return render(request, 'registration/password_change.html', context)

    else:
        context = {'title': _("Password Change"), 'form': PasswordChangeForm()}
        return render(request, 'registration/password_change.html', context)


def registration(request):
    """
    Navigates to the registration page. POST will create a user and log in,
    GET will display the form.

    **Context**
    ``message``
        An error message in the event that something is incorrect.
    ``next``
        The redirect page upon successfull login.
    **Template**

    :template:`registration/registration.html`
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'],
                                            form.cleaned_data['password'])
            #user.is_active = False
            user.save()
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            next = request.POST.get('next', "/")
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    # Redirect to a success page.
                    return redirect(next)
            """activation = Activation(username=user.username, time=datetime.datetime.now())
            activation.save()
            if user is not None:
                subject, from_email, to_email = "CEOS Datacube Account Activation", "admin@ceos-cube.org", [user.email]

                msg = EmailMessage()
                msg['From'] = from_email
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.set_content('')
                # It is possible to use msg.add_alternative() to add HTML content too
                html_content = ""
                activation_url = settings.BASE_HOST + "/accounts/" + str(activation.url) + "/activate"
                with open('/home/' + settings.LOCAL_USER +
                          '/Datacube/data_cube_ui/static/assets/media/email_template.html') as f:
                    for line in f:
                        if (line == "\t\t\tAVAILABLE_TOOLS\n"):
                            for app in Application.objects.all():
                                html_content += "<li>" + app.application_name + "</li>"
                        elif (line == "\t\t\tAVAILABLE_AREAS\n"):
                            for area in Area.objects.all():
                                html_content += "<li>" + area.area_name + "</li>"
                        elif ("HOME_URL" in line):
                            html_content += line.replace("HOME_URL", settings.BASE_HOST)
                        else:
                            html_content += line
                        if 'str' in line:
                            break
                html_content = html_content.replace("ACTIVATION_URL", activation_url)
                msg.add_alternative(html_content, subtype='html')
                # Attaching content:
                fp = open('/home/' + settings.LOCAL_USER + '/Datacube/data_cube_ui/static/assets/media/banner.png',
                          'rb')
                att = MIMEImage(fp.read())  # Or use MIMEImage, etc
                fp.close()
                # The following line is to control the filename of the attached file
                att.add_header('Content-Disposition', 'attachment', filename='banner.png')
                msg.make_mixed()  # This converts the message to multipart/mixed
                msg.attach(att)  # Don't forget to convert the message to multipart first!

                # Sending the email:
                with smtplib.SMTP('localhost') as s:
                    s.send_message(msg)

                form = LoginForm()
                form.cleaned_data = {}
                form.add_error(NON_FIELD_ERRORS, _("Activate your account using the url that has been emailed to you and log in."))
                context = {
                    'title': _("Log in"),
                    'form': form,
                }
                return render(request, 'registration/login.html', context)"""

        context = {
            'title': _("Registration"),
            'form': form,
        }
        return render(request, 'registration/registration.html', context)

    else:
        context = {'title': _("Registration"), 'form': RegistrationForm(),}
        if request.GET:
            next = request.POST.get('next', "/")
            if request.user.is_authenticated():
                return redirect(next)
            context['next'] = next
        return render(request, 'registration/registration.html', context)


def login(request):
    """
    Navigates to the login page of the application.  Note this is used as the POST for submitting
    a request to log in as well as the initial landing page.

    **Context**

    ``message``
        An error message in the event username and/or password is incorrect.
    ``next``
        The redirect page upon successfull login.

    **Template**

    :template:`registration/login.html`
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        #the form will never be invalid in this case.
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            next = request.POST.get('next', "/")
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    # Redirect to a success page.
                    return redirect(next)
                else:
                    form.add_error(NON_FIELD_ERRORS, _("Please activate your account using the link found in the registration email."))
                    # Return a 'disabled account' error message
                    context = {
                        'title': _("Log in"),
                        'form': form,
                        'message': _("Please activate your account using the link found in the registration email.")
                    }
                    return render(request, 'registration/login.html', context)
        form.add_error(NON_FIELD_ERRORS, _("Please enter a correct username and password combination."))
        form.add_error('username', _(""))
        form.add_error('password', _(""))
        # Return an 'invalid login' error message.
        context = {
            'title': _("Log in"),
            'form': form,
            'message': _("Please enter a correct username and password combination.")
        }
        return render(request, 'registration/login.html', context)
    else:
        context = {'title': _("Log in"), 'form': LoginForm() }
        if request.GET:
            next = request.GET.get('next', "/")
            if request.user.is_authenticated():
                return redirect(next)
            context['next'] = next
        return render(request, 'registration/login.html', context)


def logout(request):
    """
    Logout view that redirects the user to the home page.

    **Context**

    **Template**

    """
    auth_logout(request)
    return redirect('home')
