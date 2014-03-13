# https://stackoverflow.com/questions/2164069/best-way-to-make-djangos-login-required-the-default
# https://djangosnippets.org/snippets/966/
# http://www.finalconcept.com.au/article/view/django-creating-a-custom-middlewar e-component

from django.conf import settings
from django.http import HttpResponseRedirect

import re

class RequireLoginMiddleware(object):
    """
    Middleware component that wraps the login_required decorator around
    matching URL patterns. To use, add the class to MIDDLEWARE_CLASSES and
    define LOGIN_REQUIRED_URLS, LOGIN_REQUIRED_URLS_EXCEPTIONS and optionally
    LOGIN_URL in your settings.py. For example:
    ------
    LOGIN_REQUIRED_URLS = (
        r'/topsecret/(.*)$',
    )
    LOGIN_REQUIRED_URLS_EXCEPTIONS = (
        r'/topsecret/login(.*)$',
        r'/topsecret/logout(.*)$',
    )
    LOGIN_URL = '/login/'
    ------
    LOGIN_REQUIRED_URLS is where you define URL patterns; each pattern must
    be a valid regex.

    LOGIN_REQUIRED_URLS_EXCEPTIONS is, conversely, where you explicitly
    define any exceptions (like login and logout URLs).

    LOGIN_URL is where you define custom login urls. Leaving it blanck means
    '/accounts/login' is used by default.
    """

    def __init__(self):
        self.exceptions = tuple(re.compile(url) for url in \
                settings.LOGIN_REQUIRED_URLS_EXCEPTIONS)
        self.required = tuple(re.compile(url) for url in \
                settings.LOGIN_REQUIRED_URLS)
        self.require_login_path = \
                getattr(settings, 'LOGIN_URL', '/accounts/login/')

    def process_request(self, request):
        # Check if the required middleware auth classes are enabled.
        assert hasattr(request, 'user'), "RequireLoginMiddleware " + \
                "requires authentication middleware to be installed. Edit " +\
                "MIDDLEWARE_CLASSES setting to insert "+\
                "'django.contrib.auth.middleware.AuthenticationMiddleware'." +\
                "If that doesn't work, ensure TEMPLATE_CONTEXT_PROCESSORS " +\
                "setting includes 'django.core.context_processors.auth'."

        # First off, exempt the login path from required password login.
        if self.require_login_path == request.path:
            return None

        # An exception match should immediately return None.
        for url in self.exceptions:
            if url.match(request.path):
                return None

        # Any url that requires login should return a redirect to login page.
        for url in self.required:
            if url.match(request.path) and request.user.is_anonymous():
                return HttpResponseRedirect('%s?next=%s' % \
                        (self.require_login_path, request.path))

        # Explicitly return None for all non-matching requests
        return None
