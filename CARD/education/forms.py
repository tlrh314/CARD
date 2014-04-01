from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _

from education.models import Course, Lecture, Student

import logging

from urllib import urlencode
from urllib2 import urlopen, HTTPError, build_opener

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
            " contain at most 10 alphanumeric characters."})
    # Using Lecture class, we can and Lecture.course, thus, Course.student
    lecture_pk = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        # Fixed the issue that clean_<field> does not raise errors until after
        # clean has returned: check if UvANetID is in cleaned_data.
        cleaned_data = super(RegisterAttendanceForm, self).clean()
        try:
            UvANetID = cleaned_data['UvANetID']
        except KeyError:
            return cleaned_data
        lecture_pk = cleaned_data['lecture_pk']
        coure, lecture, student = None, None, None
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
        # The Lecture exists, therefore the Course exists.
        course = Course.objects.get(id=lecture.course.pk)
        # The passed parameters are valid; now handle registering attendance.
        try:
            student = Student.objects.get(\
                    username__iexact=UvANetID)
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
            # Not a boolean. Return value is 'true' or 'false'
            enrolled = self.datanose_enrolled(UvANetID, course)
            if enrolled == 'true':
                # create Student; surfConnextID = None
                # add Student to Course.Student
                # add to Lecture.Attending
                raise forms.ValidationError(
                        _('%(UvANetID)s enrolled for %(course)s at DN'),
                        code = 'invalid',
                        params = {'UvANetID': UvANetID,\
                                'course': course },
                        )
            elif enrolled == 'false':
                raise forms.ValidationError(
                        _('%(UvANetID)s not enrolled for %(course)s at DN'),
                        code = 'invalid',
                        params = {'UvANetID': UvANetID,\
                                'course': course },
                        )
            else:
                raise forms.ValidationError(
                        _('Unexpected DN return: %(enrolled)s'),
                        code = 'invalid',
                        params = {'enrolled': enrolled },
                        )
        return cleaned_data


    def datanose_enrolled(self, UvANetID, course):
        get_data = [('courseID', course.dataNoseID), ('studentID', UvANetID)]

        try:
            url = DN_WEBSERVICE_URL + '/enrolment/?' + urlencode(get_data)
            enrolled  = build_opener().open(url).read()
            if enrolled:
                logger.debug('DataNose Webservice request successful: '\
                        + str(UvANetID) + ' enrolled for ' + str(course))
            else:
                logger.debug('DataNose Webservice request successful: '\
                        + str(UvANetID)+ ' not enrolled for '+str(course))
            return enrolled
        except HTTPError:
            logger.error('Invalid url')
            logger.debug('DataNose Webservice request failed!')

        return None
