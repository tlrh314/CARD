from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _

from education.models import Course, Lecture, Student

import json
import logging

from urllib import urlencode
from urllib2 import urlopen, HTTPError

from xml.dom import minidom
#from django.utils import simplejson as json

from CARD.settings import DN_WEBSERVICE_URL

logger = logging.getLogger('education')

class AttendanceForm(forms.Form):
    """
    Form for registering a student as attending a Lecture

    Validates that the requested Student is enrolled for the Course.

    If the Student is not yet in the database, the student should be added.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """

    required_css_class = 'required'

    username = forms.RegexField(regex=r'^[\w]+$', label=_("UvANetID"),\
            max_length=10, error_messages={'invalid': "This field may"+\
            " contain only letters and numbers."})

    def user_exists(self):
        """
        Validate that the username is alphanumeric and exists in database,
        also check if the user is enrolled on DataNose for the course.

        """
        existing = Student.objects.filter(username__iexact=\
                self.cleaned_data['username'])
        post_data = [('courseID', xxxx), ('studentID', yyyy)]

        try:
            # http://pastebin.com/8ZrdzNwT
            url = DN_WEBSERVICE_URL + "/enrolment" + urlencode(post_data)
            result = urlfetch.fetch(url,'','get');
            dom = minidom.parseString(result.content)
            json = simplejson.load(json)
            #content = simplejson.load(minidom.parseString(\
            #        urlopen(DN_WEBSERVICE_URL + "/enrolment", \
            #        urlencode(post_data)).read().content)
        except HTTPError:
            logger.error("Invalid url")
            return HttpResponseBadRequest()

        if content["boolean"] == "true":
            logger.debug("DataNose Webservice request successful: "\
                    +str(xxxx)+" enrolled for "+str(yyyy))
            enrolled = True
        elif content["boolean"] == "false":
            logger.debug("DataNose Webservice request successful: "\
                    +str(xxxx)+" not enrolled for "+str(yyyy))
            enrolled = False
        else:
            logger.debug("DataNose Webservice request failed!")
            return HttpResponseBadRequest()

        if not enrolled:
            raise forms.ValidationError(_("This Student is not enrolled "+\
                    "for this course"))
        elif not existing.exists():
            logger.debug(str(xxxx)+" is not yet in database.")
            #try:
            #    # create user
            #    logger.debug(str(xxxx)+" has been added to database.")
            #except bla:
            #    logger.debug(str(xxxx)+" adding to database failed")
        else:
            return self.cleaned_data['username']
