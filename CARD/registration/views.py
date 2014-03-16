"""
Views which allow users to create and activate accounts.

"""
from django.shortcuts import redirect, render_to_response
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
#from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseBadRequest, HttpResponseNotFound
from django.contrib.auth import authenticate,login

from registration import signals
from registration.forms import RegistrationForm

import re
import json
import logging

from urllib import urlencode
from urllib2 import urlopen, HTTPError

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
        external_id = "surfconext/" + attributes["saml:sp:NameID"]["Value"]
        email = attributes["urn:mace:dir:attribute-def:mail"][0]
#        person_set = Person.objects.filter(external_id=external_id)
        # TODO what if a person with same name/email exists?
        # 1. Ask for confirmation
        # 2. Notify admin?
        # 3. Send email
#        if not person_set.exists():
#            person = Person()
#            person.UvANetID = attributes["urn:mace:dir:attribute-def:uid"][0]
#            #surname = attributes["urn:mace:dir:attribute-def:sn"]
#            first_name = attributes["urn:mace:dir:attribute-def:givenName"]
#            person.name = attributes["urn:mace:dir:attribute-def:cn"][0]
#            #displayname = attributes["urn:mace:dir:attribute-def:displayName"]
#            person.email = email
#            person.external_id = external_id
#            logger.debug("Created new person '" + person.UvANetID + "'")
#        else:
#            person = person_set.get()
#        if not person.user:
#            user = User()
#            user.username = person.UvANetID
#            user.first_name = first_name
#            user.email = email
#            user.set_password(utils.id_generator(size=12))
#            user.save()
#            person.user = user
#            logger.debug("User '{}' linked to person '{}'".
#                         format(user, person))
#        user = person.user
#        person.save()
#        user = authenticate(username=user.username)
#        login(request, user)
#        logger.debug("Logged in user '{}'".format(user))
    else:
        logger.debug("Authentication failed")
    return HttpResponseRedirect('/')
    #return render_to_response('registration/ivoauth_callback.html', attributes)
    # Print content
    # html = "<html><body>%s.</body></html>" % content
    # return HttpResponse(html)

#def login_user(request):
#    username = password = redirect = ''
#    state = 'Not logged in'
#    if request.method == "POST" and request.is_ajax():
#        username = request.POST['username']
#        password = request.POST['password']
#        redirect = request.POST.get('next', '/')
#        user = authenticate(username=username, password=password)
#        if user is not None and user.is_active:
#            state = 'Logged in'
#            login(request, user)
#
#            # Check if redirecturl valid
#            if '//' in redirect and re.match(r'[^\?]*//', redirect):
#                redirect = LOGIN_REDIRECT_URL
#            data = json.dumps({'success': True,
#                               'redirect': redirect})
#        else:
#            data = json.dumps({'success': False,
#                               'redirect': redirect})
#        return HttpResponse(data, mimetype='application/json')
#    return HttpResponseBadRequest()
#
#def logout_user(request):
#    logout(request)
#    return HttpResponseRedirect('/')
