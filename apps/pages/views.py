from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.core.mail import send_mail

from . import forms


def home(request):
    """
    Navigates to the home page of the application.

    **Context**

    **Template**

    :template:`home/index.html`
    """

    context = {}
    return render(request, 'index.html', context)


def workshop(request):
    """
    Navigates to the home page of the application.

    **Context**

    **Template**

    :template:`home/index.html`
    """

    context = {}
    return render(request, 'workshop.html', context)


@login_required
def submit_feedback(request):
    if request.method == 'POST':
        form = forms.SubmitFeedbackForm(request.POST)
        if form.is_valid():
            send_mail(
                form.cleaned_data.get('feedback_reason'),
                "Feedback sent from user: " + request.user.email + "\n" + form.cleaned_data.get('feedback'),
                'admin@ceos-cube.org', [settings.ADMIN_EMAIL],
                fail_silently=False)

        form = forms.SubmitFeedbackForm()
        form.cleaned_data = {}
        form.add_error(None, 'Feedback was successfuly submitted.  Thank you for your comments')

        context = {'title': "Feedback", 'form': form, 'wide': True}
        return render(request, 'submit_feedback.html', context)

    else:
        context = {'title': "Feedback", 'form': forms.SubmitFeedbackForm(), 'wide': True}
        if request.GET:
            next = request.GET.get('next', "/")
            if request.user.is_authenticated():
                return redirect(next)
            context['next'] = next
        return render(request, 'submit_feedback.html', context)
