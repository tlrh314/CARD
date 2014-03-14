from django.shortcuts import render, get_object_or_404, redirect, \
    render_to_response
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseBadRequest, HttpResponseNotFound
from django.contrib.auth import authenticate,login, logout
from django.template import RequestContext, loader
#from django.core import serializers
#from django.core.mail import EmailMultiAlternatives

#import itertools
import re
import json
import logging

from pprint import pprint
from urllib import quote, urlencode
from urllib2 import urlopen, HTTPError

from CARD.settings import LOGIN_REDIRECT_URL, IVOAUTH_TOKEN, IVOAUTH_URL

logger = logging.getLogger('search')

from functools import wraps

# Might not be needed?
def person(request, pk):
    person = get_object_or_404(Person, id=pk)

    context = sorted_tags(person.tags.all())
    context['person'] = person
    context['syntax'] = SEARCH_SETTINGS['syntax'],
    context['next'] = person.get_absolute_url()
    return render(request, 'person.html', context)

def login_user(request):
    username = password = redirect = ''
    state = 'Not logged in'
    if request.method == "POST" and request.is_ajax():
        username = request.POST['username']
        password = request.POST['password']
        redirect = request.POST.get('next', '/')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            state = 'Logged in'
            login(request, user)

            # Check if redirecturl valid
            if '//' in redirect and re.match(r'[^\?]*//', redirect):
                redirect = LOGIN_REDIRECT_URL
            data = json.dumps({'success': True,
                               'redirect': redirect })
        else:
            data = json.dumps({'success': False,
                               'redirect': redirect })
        return HttpResponse(data, mimetype='application/json')
    return HttpResponseBadRequest()


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')


def ivoauth(request):
    callback_url = str(request.build_absolute_uri("ivoauth/callback")) + "/?ticket={#ticket}"
    post_data = [('token', IVOAUTH_TOKEN), ('callback_url', callback_url)]
    try:
        content = json.loads(urlopen(IVOAUTH_URL + "/ticket",
            urlencode(post_data)).read())
    except HTTPError:
        logger.error("Invalid url")
        return HttpResponseBadRequest()

    if content["status"] == "success":
        logger.debug("IVO authentication successful")
        return HttpResponseRedirect(IVOAUTH_URL + "/login/" + content["ticket"])
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

    if json.loads(content)["status"] == "success":
        logger.debug("Authentication successful")
        attributes = json.loads(content)["attributes"]
        email = attributes["urn:mace:dir:attribute-def:mail"][0]
        person_set = Person.objects.filter(email=email)
        if not person_set.exists():
            person = Person()
            person.handle = attributes["urn:mace:dir:attribute-def:uid"][0]
            surname = attributes["urn:mace:dir:attribute-def:sn"]
            first_name = attributes["urn:mace:dir:attribute-def:givenName"]
            person.name = attributes["urn:mace:dir:attribute-def:cn"][0]
            display_name = attributes["urn:mace:dir:attribute-def:displayName"]
            person.email = email
            logger.debug("Created new person '" + person.handle + "'")
        else:
            person = person_set.get()
        if not person.user:
            user = User()
            user.username = person.handle
            user.first_name = first_name
            user.email = email
            user.set_password(utils.id_generator(size=12))
            user.save()
            person.user = user
            logger.debug("User '{}' linked to person '{}'".format(user, person))
        user = person.user
        person.save()
        user = authenticate(username=user.username)
        login(request, user)
        logger.debug("Logged in user '{}'".format(user))
    else:
        logger.debug("Authentication failed")
    return HttpResponseRedirect('/')

def index(request):
    hank = "HankMoody"
    template = loader.get_template('processlogin/index.html')
    context = RequestContext(request, {'HANK!': hank,})
    return HttpResponse(template.render(context))
