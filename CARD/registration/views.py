"""
Views which allow users to create and activate accounts.

"""
from django.shortcuts import redirect, render_to_response
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
#from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseBadRequest, HttpResponseNotFound
from django.contrib.auth import login, logout, authenticate

from registration import signals
from registration.forms import RegistrationForm
from registration.models import RegistrationProfile
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site

import re
import json
import logging
import string, random

from urllib import urlencode
from urllib2 import urlopen, HTTPError

from django.contrib.auth.models import User

from CARD.settings import LOGIN_REDIRECT_URL, IVOAUTH_TOKEN, IVOAUTH_URL

logger = logging.getLogger('registration')

class _RequestPassingFormView(FormView):
    """
    A version of FormView which passes extra arguments to certain
    methods, notably passing the HTTP request nearly everywhere, to
    enable finer-grained processing.

    """
    def get(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class(request)
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class(request)
        form = self.get_form(form_class)
        if form.is_valid():
            # Pass request to form_valid.
            return self.form_valid(request, form)
        else:
            return self.form_invalid(form)

    def get_form_class(self, request=None):
        return super(_RequestPassingFormView, self).get_form_class()

    def get_form_kwargs(self, request=None, form_class=None):
        return super(_RequestPassingFormView, self).get_form_kwargs()

    def get_initial(self, request=None):
        return super(_RequestPassingFormView, self).get_initial()

    def get_success_url(self, request=None, user=None):
        # We need to be able to use the request and the new user when
        # constructing success_url.
        return super(_RequestPassingFormView, self).get_success_url()

    def form_valid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_valid(form)

    def form_invalid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_invalid(form)


class RegistrationView(_RequestPassingFormView):
    """
    Base class for user registration views.

    """
    disallowed_url = 'registration_disallowed'
    form_class = RegistrationForm
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    success_url = None
    template_name = 'registration/registration_form.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Check that user signup is allowed before even bothering to
        dispatch or do other processing.

        """
        if not self.registration_allowed(request):
            return redirect(self.disallowed_url)
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, request, form):
        new_user = self.register(request, **form.cleaned_data)
        success_url = self.get_success_url(request, new_user)

        # success_url may be a simple string, or a tuple providing the
        # full argument set for redirect(). Attempting to unpack it
        # tells us which one it is.
        try:
            to, args, kwargs = success_url
            return redirect(to, *args, **kwargs)
        except ValueError:
            return redirect(success_url)

    def registration_allowed(self, request):
        """
        Override this to enable/disable user registration, either
        globally or on a per-request basis.

        """
        return True

    def register(self, request, **cleaned_data):
        """
        Implement user-registration logic here. Access to both the
        request and the full cleaned_data of the registration form is
        available here.

        """
        raise NotImplementedError


class ActivationView(TemplateView):
    """
    Base class for user activation views.

    """
    http_method_names = ['get']
    template_name = 'registration/activate.html'

    def get(self, request, *args, **kwargs):
        activated_user = self.activate(request, *args, **kwargs)
        if activated_user:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated_user,
                                        request=request)
            success_url = self.get_success_url(request, activated_user)
            try:
                to, args, kwargs = success_url
                return redirect(to, *args, **kwargs)
            except ValueError:
                return redirect(success_url)
        return super(ActivationView, self).get(request, *args, **kwargs)

    def activate(self, request, *args, **kwargs):
        """
        Implement account-activation logic here.

        """
        raise NotImplementedError

    def get_success_url(self, request, user):
        raise NotImplementedError


def ivoauth(request):
    callback_url = str(request.build_absolute_uri("ivoauth/callback")) + \
        "/?ticket={#ticket}"
    post_data = [('token', IVOAUTH_TOKEN), ('callback_url', callback_url)]
    try:
        content = json.loads(urlopen(IVOAUTH_URL + "/ticket",
                             urlencode(post_data)).read())
    except HTTPError:
        logger.error("Invalid url")
        return HttpResponseBadRequest()

    if content["status"] == "success":
        logger.debug("IVO authentication successful")
        return HttpResponseRedirect(IVOAUTH_URL + "/login/" +
                                    content["ticket"])
    else:
        logger.debug("IVO authentication failed")
    return HttpResponseBadRequest()


def ivoauth_callback(request):
    ticket = request.GET.get("ticket", "")
    if not ticket:
        logger.error("no ticket")
    url = IVOAUTH_URL + "/status"
    post_data = [('token', IVOAUTH_TOKEN), ('ticket', ticket)]
    try:
        content = urlopen(url, urlencode(post_data)).read()
    except HTTPError:
        logger.error("Invalid url")
        return HttpResponseBadRequest()

    content = json.loads(content)
    if content["status"] == "success":
        logger.debug("Authentication successful")
        attributes = content["attributes"]
        UvANetID = attributes["urn:mace:dir:attribute-def:uid"][0]
        try:
            # User exists, log in.
            user = authenticate(username=UvANetID)
            login(request, user)
            logger.debug("Logged in user '{}'".format(user))
        except:
            # User does not exist, create new user.
            username = attributes["urn:mace:dir:attribute-def:uid"][0]
            email = attributes["urn:mace:dir:attribute-def:mail"][0]
            chars = string.ascii_uppercase+string.digits
            password = ''.join(random.choice(chars) for x in range(12))
            first_name = attributes["urn:mace:dir:attribute-def:givenName"][0]
            last_name = attributes["urn:mace:dir:attribute-def:cn"][0]
            surfConnextID = "surfconext/" + attributes["saml:sp:NameID"]["Value"]
            if Site._meta.installed:
                site = Site.objects.get_current()
            else:
                site = RequestSite(request)
            user = RegistrationProfile.objects.create_active_user(username, \
                    email, password, first_name, last_name, surfConnextID, site)
            logger.debug("Created new user '" + user.username+ "'")

            user = authenticate(username=user.username)
            login(request, user)
            logger.debug("Logged in user '{}'".format(user))
    else:
        logger.debug("Authentication failed")
    return HttpResponseRedirect('/')
    #html = "<html><body>%s </body></html>" % user
    #return HttpResponse(html)

def logout_user(request):
    logout(request)
    return HttpResponseRedirect('https://auth.innovatievooronderwijs.nl/logout')
