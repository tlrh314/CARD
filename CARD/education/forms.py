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

class RegisterAttendanceForm(forms.Form):
    """
    Form to add UvANetID (-> Student.username) to Lecture.attending.
    Valdiation requires:
        if UvANetID exists:
            if UvANetID in Course.Students.all(): add to Lecture.attending
        elif requested Student is enrolled for the Course at DataNose:
            create Student; surfConnextID = None
            add Student to Course.Student
            add to Lecture.Attending
        else: raise forms.ValueError
    """

    required_css_class = 'required'

    UvANetID = forms.RegexField(regex=r'^[\w]+$', label=_("UvANetID"),\
            max_length=10, error_messages={'invalid': "This field may"+\
            " contain only letters and numbers."})
    # Using Lecture class, we can and Lecture.course, thus, Course.student
    lecture_pk = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        lecture_pk = self.cleaned_data['lecture_pk']
        lecture, student = None, None
        if not lecture_pk:
            raise forms.ValidationError("Error: lecture_pk not provided.")
        try:
            lecture = Lecture.objects.get(id=lecture_pk)
        except Lecture.DoesNotExist:
            raise forms.ValidationError(
                    _('Lecture %(pk)s does not exist'),
                    code = 'invalid',
                    params={'pk': lecture_pk},
                    )
        # The passed parameters are valid; now handle registering attendance.
        try:
            student = Student.objects.get(\
                    username__iexact=self.cleaned_data['UvANetID'])
            # The Lecture exists, therefore the Course exists.
            course = Course.objects.get(id=lecture.course.pk)
            if course in student.StudentCourses.all():
                if student in lecture.attending.all():
                    raise forms.ValidationError(
                             _('%(UvANetID)s is already attending %(lecture)s'),
                             code='invalid',
                             params={'UvANetID': student.username,\
                                     'lecture' : lecture },
                             )
                else:
                    lecture.attending.add(student)
                    lecture.save()
        except Student.DoesNotExist:
            if self.datanose_enrolled(self.cleaned_data['UvANetID'], course):
                # create Student; surfConnextID = None
                # add Student to Course.Student
                # add to Lecture.Attending
                raise forms.ValidationError(
                        _('%(UvANetID)s enrolled for %(course)s at DN'),
                        code = 'invalid',
                        params = {'UvANetID': student.username,\
                                'course': course },
                        )
            else:
                raise forms.ValidationError(
                        _('%(UvANetID)s not enrolled for %(course)s'),
                        code = 'invalid',
                        params = {'UvANetID': student.username,\
                                'course': course },
                        )

    def datanose_enrolled(self, UvANetID, course):
        post_data = [('courseID', course.dataNoseID), ('studentID', UvANetID)]

        try:
            # http://pastebin.com/8ZrdzNwT
            url = DN_WEBSERVICE_URL + '/enrolment' + urlencode(post_data)
            result = urlfetch.fetch(url,'','get');
            dom = minidom.parseString(result.content)
            json = simplejson.load(json)
            #content = simplejson.load(minidom.parseString(\
            #        urlopen(DN_WEBSERVICE_URL + '/enrolment', \
            #        urlencode(post_data)).read().content)
        except HTTPError:
            logger.error('Invalid url')
            return HttpResponseBadRequest()

        if content['boolean'] == 'true':
            logger.debug('DataNose Webservice request successful: '\
                    + str(UvANetID) + ' enrolled for ' + str(course))
            enrolled = True
        elif content['boolean'] == 'false':
            logger.debug('DataNose Webservice request successful: '\
                    + str(UvANetID)+ ' not enrolled for '+str(course))
            enrolled = False
        else:
            logger.debug('DataNose Webservice request failed!')
            return HttpResponseBadRequest()

        if not enrolled:
            raise forms.ValidationError(_("This Student is not enrolled "+\
                    "for this course"))

        return False
