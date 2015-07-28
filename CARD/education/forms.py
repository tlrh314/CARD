from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _

from education.models import Course, Lecture, Student
from registration.models import RegistrationProfile

import logging
import string, random
from urllib import urlencode
from urllib2 import urlopen, HTTPError, build_opener
from os.path import splitext

from CARD.settings import DN_WEBSERVICE_URL

logger = logging.getLogger(__name__)
flash = '<span class="glyphicon glyphicon-flash"></span> '

class RegisterAttendanceForm(forms.Form):
    """
    Form to add UvANetID (-> Student.username) to Lecture.attending.
    Valdiation requires:
        if UvANetID exists or StudentID exists:
            if UvANetID in Course.Students.all(): add to Lecture.attending
        elif requested Student is enrolled for the Course at DataNose:
            create Student; surfConnextID = 'None'
            add Student to Course.Student
            add to Lecture.Attending
        else: raise forms.VaidationError
    """

    required_css_class = 'required'

    UvANetID = forms.RegexField(regex=r'^[\w]+$', label=_("UvANetID"),\
            max_length=10, error_messages={'invalid': "This field may"+\
            " contain at most 10 alphanumeric characters."})
    # Using Lecture class, we can and Lecture.course, thus, Course.student
    lecture_pk = forms.CharField(widget=forms.HiddenInput())
    site = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        logger.debug("Now running clean method of RegisterAttendanceForm.")

        # Fixed the issue that clean_<field> does not raise errors until after
        # clean has returned: check if UvANetID is in cleaned_data.
        cleaned_data = super(RegisterAttendanceForm, self).clean()
        try:
            UvANetID = cleaned_data['UvANetID']
            logger.debug("Raw input data: '{}'.".format(UvANetID))
            """
            When student is scanned by RFID-reader, id starts with '1'.
            The length is fixed to 9 digits. A studentID has 8 digits.
            If the UvANetID is used as StudentID it has leading 0's up to
            a number of 8 digits. This is NEDAP 9864830 specific behaviour!
            UvA Employee/HvA numbers should start with a leading 2, then 0's up
            to a fixed number of 9 digits to get the employee/studentID number.
            """
            if len(UvANetID) == 9 and UvANetID[0] == '1':
                UvANetID = UvANetID[1:] # remove the 1
                while UvANetID[0] == '0':
                    UvANetID = UvANetID[1:] # remove the leading 0's
            if len(UvANetID) == 9 and UvANetID[0] == '2':
                UvANetID = UvANetID[1:] # remove the 2
                while UvANetID[0] == '0':
                    UvANetID = UvANetID[1:] # remove the leading 0's
                logger.debug("ValidationError for '{}'.".format(UvANetID))
                raise forms.ValidationError(
                        _(flash+'ID %(id)s is possibly an employee number. '+\
                        'Please use your StudentID card for CARD.'),
                        code = 'invalid',
                        params={'id': UvANetID},
                        )
            logger.debug("Modified input data: '{}'.".format(UvANetID))
            cleaned_data['UvANetID'] = UvANetID
        except KeyError:
            logger.error("KeyError: UvANetID. Cleaned_data: '{}'".format(\
                    cleaned_data))
            return cleaned_data
        # Very ugly hack. We need to access the request?!!
        lecture_pk = cleaned_data['lecture_pk']
        site = cleaned_data['site']
        coure, lecture, student = None, None, None
        if not lecture_pk:
            # This should be dead code.
            logger.error("No lecture_pk provided.")
            raise forms.ValidationError(
                    _(flash+'Whops, the lecture_pk is not provided.'),
                    code = 'invalid'
                    )
        try:
            lecture = Lecture.objects.get(id=lecture_pk)
            logger.debug("Lecture: '{}' found.".format(lecture))

        except Lecture.DoesNotExist:
            logger.debug("Lecture with pk: '{}' not found.".format(lecture_pk))
            raise forms.ValidationError(
                    _(flash+'Lecture %(pk)s does not exist'),
                    code = 'invalid',
                    params={'pk': lecture_pk},
                    )
        # The Lecture exists, therefore the Course exists.
        course = Course.objects.get(id=lecture.course.pk)
        logger.debug("Course '{}' found.".format(course))
        # The passed parameters are valid; now handle registering attendance.
        try:
            student = Student.objects.get(\
                    username__iexact=UvANetID)
            logger.debug("Student '{}' found.".format(student))
        except Student.DoesNotExist:
            logger.debug("Student '{}' does not exist.".format(UvANetID))
            # Either this student is not in our local database yet,
            # or this student enrolled per or prior to september 2010.

            # If UvANetID != StudentID, we might have it on file in profile.
            try:
                profile = RegistrationProfile.objects.get(\
                        other_id__iexact=UvANetID)
                student = Student.objects.get(pk=profile.user_id)
                logger.debug("Profile found for UvANetID '{}' ".format(student)+\
                        "and StudentID '{}'.".format(profile.other_id))
            except RegistrationProfile.DoesNotExist:
                logger.debug("Student '{}' has no profile.".format(UvANetID))
                # Not a boolean. Return value is 'true' or 'false'.
                enrolled = self.datanose_enrolled(UvANetID, course)
                if enrolled == 'true':
                    # create Student; surfConnextID = 'None'
                    chars = string.ascii_uppercase+string.digits
                    password = ''.join(random.choice(chars) for x in range(12))
                    user = RegistrationProfile.objects.create_active_user(UvANetID,\
                            '', password, '', '', 'None', site)
                    # add Student to Course.student
                    student = Student.objects.get(username__iexact=user.username)
                    student.StudentCourses.add(course)
                    student.save()
                    # add Student to Lecture.attending
                    #lecture.attending.add(student)
                    lecture.save()
                    logger.debug("Student '{}' is enrolled ".format(UvANetID)+\
                            "at DataNose.")
                    logger.debug("Student '{}' is thus created".format(student)+\
                            ", added to '{}' ".format(course) + "and registered"+\
                            " as attending '{}'.".format(lecture))

                elif enrolled == 'false':
                    logger.debug("Student '{}' is not enrolled ".format(UvANetID)+\
                            "at DataNose for course '{}'".format(course))
                    sis = '<a href="http://www.sis.uva.nl">SIS</a>'
                    raise forms.ValidationError(
                            _(flash+'%(UvANetID)s is not enrolled for %(course)s '+\
                                    'at DataNose. Please enrol at %(SIS)s. ' +\
                                    '<br>Contact the coordinator now.'),
                            code = 'invalid',
                            params = {'UvANetID': UvANetID,\
                                    'course': course ,\
                                    'SIS': sis },
                            )
                else:
                    logger.debug("Bad DataNose return '{}'".format(enrolled) +\
                            "for '{}'".format(UvANetID))
                    raise forms.ValidationError(
                            _(flash+'Unexpected DataNose return: %(enrolled)s'),
                            code = 'invalid',
                            params = {'enrolled': enrolled },
                            )

        # This block handles registration of students on file.
        if course in student.StudentCourses.all():
            if student in lecture.attending.all():
                logger.debug("Student '{}' is already ".format(UvANetID)+\
                        "attending '{}'.".format(lecture))
                raise forms.ValidationError(
                         _(flash+'%(UvANetID)s is already attending %(lect)s'),
                         code='invalid',
                         params={'UvANetID': student.username,\
                                 'lect' : lecture },
                         )
            else:
                logger.debug("Student '{}' registered ".format(UvANetID) + \
                        "as attending '{}'.".format(lecture))
                lecture.attending.add(student)
                lecture.save()
        else:
            enrolled = self.datanose_enrolled(UvANetID, course)
            if enrolled == 'true':
                logger.debug("Student '{}' is now enrolled locally ".format(UvANetID) + \
                        "for course '{}'.".format(course))
                student.StudentCourses.add(course)
                student.save()
                logger.debug("Student '{}' registered ".format(UvANetID) + \
                        "as attending '{}'.".format(lecture))
                lecture.attending.add(student)
                lecture.save()
            else:
                logger.debug("Student '{}' not enrolled locally ".format(UvANetID) + \
                        "for course '{}'.".format(course))
                raise forms.ValidationError(
                        _(flash+'%(UvANetID)s is not enrolled for %(course)s '+\
                                'in CARD. Student also not enrolled at DataNose!'),
                        code = 'invalid',
                        params = {'UvANetID': UvANetID,\
                                'course': course, },
                        )
        # Alternatively, we can add the student to the course locally.
        # We could either check this at DataNose, or not.

        return cleaned_data

    def datanose_enrolled(self, UvANetID, course):
        get_data = [('courseID', course.dataNoseID), ('studentID', UvANetID)]

        try:
            url = DN_WEBSERVICE_URL + '/enrolment/?' + urlencode(get_data)
            enrolled  = build_opener().open(url).read()
            logger.debug("DataNose Webservice request successful for " + \
                    "'{}' at course ".format(UvANetID)+ "'{}'.".format(course))
            return enrolled
        except HTTPError:
            logger.error("DataNose Webservice request failed for " + \
                    "'{}' at course ".format(UvANetID)+ "'{}'.".format(course))

        return None

# https://stackoverflow.com/questions/3665379/django-and-xlrd-reading-from-memory/3665672#3665672
IMPORT_FILE_TYPES = ['.xls', ]
class XlsInputForm(forms.Form):
    input_excel = forms.FileField(required= True, \
            label= u"Press browse, select file, then press Upload.")

    def clean_input_excel(self):
        input_excel = self.cleaned_data['input_excel']
        extension = splitext( input_excel.name )[1]

        if not (extension in IMPORT_FILE_TYPES):
            raise forms.ValidationError(
                    _('Filetype %(ext)s is not a valid Excel file. '+\
                    'Please make sure your input is an Excel file. '+\
                    'Note that Excel 2007 is NOT supported!'),
                    code = 'invalid',
                    params={'ext': extension},
                    )
        else:
            return input_excel
