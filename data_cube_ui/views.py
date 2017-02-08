# Copyright 2016 United States Government as represented by the Administrator
# of the National Aeronautics and Space Administration. All Rights Reserved.
#
# Portion of this code is Copyright Geoscience Australia, Licensed under the
# Apache License, Version 2.0 (the "License"); you may not use this file
# except in compliance with the License. You may obtain a copy of the License
# at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# The CEOS 2 platform is licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.shortcuts import render, redirect
from django.template import loader, RequestContext
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.forms.forms import NON_FIELD_ERRORS

from email.message import EmailMessage
import smtplib

from .forms import SubmitFeedbackForm
from .models import Application, ToolInfo

def home(request):
    """
    Navigates to the home page of the application.

    **Context**

    **Template**

    :template:`home/index.html`
    """

    context = {

    }
    return render(request, 'index.html', context)

@login_required
def region_selection(request, app_id):
    application = Application.objects.get(application_id=app_id)
    tool_info = application.toolinfo_set.all().order_by('id')
    areas = application.areas.all()
    context = {
        'app': app_id,
        'tool_descriptions': tool_info,
        'areas': areas
    }
    return render(request, 'region_selection.html', context)

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        form = SubmitFeedbackForm(request.POST)
        if form.is_valid():
            msg = EmailMessage()
            msg['From'] = "admin@ceos-cube.org"
            msg['To'] = settings.ADMIN_EMAIL
            msg['Subject'] = form.cleaned_data.get('feedback_reason')

            msg.set_content("Feedback sent from user: " + request.user.email + "\n" + form.cleaned_data.get('feedback'))

            with smtplib.SMTP('localhost') as s:
                s.send_message(msg)

        form = SubmitFeedbackForm()
        form.cleaned_data = {}
        form.add_error(NON_FIELD_ERRORS, 'Feedback was successfuly submitted.  Thank you for your comments')

        context = {'title': "Feedback", 'form':form, 'wide':True}
        return render(request, 'submit_feedback.html', context)

    else:
        context = {'title': "Feedback", 'form': SubmitFeedbackForm(), 'wide':True}
        if request.GET:
            next = request.GET.get('next', "/")
            if request.user.is_authenticated():
                return redirect(next)
            context['next'] = next
        return render(request, 'submit_feedback.html', context)
