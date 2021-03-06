from django.shortcuts import render, redirect, render_to_response
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext
from django.utils import timezone

from registration.views import _RequestPassingFormView
from registration.models import RegistrationProfile

from education.models import Student, Course, Lecture, Barcode
from education.forms import RegisterAttendanceForm, XlsInputForm

from CARD.settings import TYPES

import logging
from collections import defaultdict
import xlwt, xlrd
import string, random
from datetime import datetime, date

logger = logging.getLogger(__name__)

LECTURES_REQUIRED = 25

class IndexView(generic.ListView):
    template_name = 'education/student_index.html'
    context_object_name = 'latest_course_list'

    def get_queryset(self):
        student = Student.objects.get(pk=self.request.user.id)
        return student.StudentCourses.all()

class CourseView(generic.DetailView):
    model = Course
    pk_url_kwarg = 'course_pk'
    template_name = 'education/student_course.html'

    def get_context_data(self, **kwargs):
        # Initialize
        context = super(CourseView, self).get_context_data(**kwargs)
        current_course = Course.objects.get(id=self.kwargs.get("course_pk"))
        progress = 0

        # Calculate the attendance for all lectures in this course.
        lecture_list = Lecture.objects.filter(course_id=current_course.id).\
                order_by('-date')
        for lecture in lecture_list:
            attending_list = lecture.attending.all()
            for attending in attending_list:
                context['lecture'] = attending
                if self.request.user.username == attending.username:
                    progress += 1

        # Set visited, total and the percentage progress for progressbar.
        profile = RegistrationProfile.objects.get(user_id=\
                self.request.user)
        offset = profile.offset
        context['offset'] = offset
        context['visited'] = progress + offset
        context['total_lectures'] = LECTURES_REQUIRED
        progress = 100*float(progress+offset)/LECTURES_REQUIRED
        context['progress'] = progress

        return context

class LectureView(generic.DetailView):
    model = Lecture
    pk_url_kwarg = 'lecture_pk'
    template_name = 'education/student_lecture.html'

class AdminIndexView(generic.ListView):
    template_name = 'education/admin_index.html'
    context_object_name = 'all_course_list'

    def get_queryset(self):
        return Course.objects.all

# lecture.attending.through.objects.all() ?
class AdminCourseView(generic.DetailView):
    model = Course
    pk_url_kwarg = 'course_pk'
    template_name = 'education/admin_course.html'

    def get_student_offset(student):
        if not isinstance(student, Student):
            return None
        try:
            profile = RegistrationProfile.objects.get(user_id=student)
            offset = profile.offset
        except:
            offset = None
        return offset

    def get_context_data(self, **kwargs):
        # Initialize the context: set up the lectures and the TYPES.
        context = super(AdminCourseView, self).get_context_data(**kwargs)
        course = Course.objects.get(id=self.kwargs.get("course_pk"))
        context['lectures'] = Lecture.objects.filter(\
                course_id=course.id).order_by('-date')
        context['TYPES'] = TYPES

        return context

class AdminLectureList(generic.ListView):
    template_name = 'education/admin_lecture_overview.html'
    context_object_name = 'all_lecture_list'

    def get_queryset(self):
        return Lecture.objects.order_by('-date')

class AdminLectureView(generic.DetailView):
    model = Lecture
    pk_url_kwarg = 'lecture_pk'
    template_name = 'education/admin_lecture.html'

    def get_context_data(self, **kwargs):
        # Initialize the context and set up the current_course.
        context = super(AdminLectureView, self).get_context_data(**kwargs)

        total = 0
        lecture = Lecture.objects.get(id=self.kwargs.get("lecture_pk"))
        for student in lecture.attending.all():
            total += 1
        context['total'] = total

        return context

class AdminStudentView(generic.DetailView):
    model = Student
    pk_url_kwarg = 'student_pk'
    template_name = 'education/admin_student.html'

    def get_context_data(self, **kwargs):
        # Initialize the context and set up the current_course.
        context = super(AdminStudentView, self).get_context_data(**kwargs)
        student = Student.objects.get(id=self.kwargs.get("student_pk"))
        profile = RegistrationProfile.objects.get(user_id=student)
        context['offset'] = profile.offset
        context['student'] = student

        # Initialize 2D array with keys UvANetID and type of Lecture.
        status = defaultdict(dict)
        attended = {}
        progress = {}
        course_list = []
        for course in student.StudentCourses.all():
            course_list.append(course)
            number_attended = profile.offset
            for lecture in Lecture.objects.filter(course_id=course.id):
                if lecture.in_future():
                    status[course.id][lecture.id] = ('info', 'Future')
                elif student in lecture.attending.all():
                    status[course.id][lecture.id] = ('success', 'Present')
                    number_attended += 1
                else:
                    status[course.id][lecture.id] = ('danger', 'Absent')
            attended[course.id] = number_attended
            progress[course.id] = (100*float(number_attended)\
                    /LECTURES_REQUIRED)

        context['course_list'] = course_list
        context['status'] = status
        context['attended'] = attended
        context['total_lectures'] = LECTURES_REQUIRED
        context['progress'] = progress

        return context

class RegisterAttendance(generic.FormView):
    template_name = 'education/register_attendance.html'
    form_class = RegisterAttendanceForm
    succes_url = None

    # Quick and dirty fix: pass lecture_pk to template, then shove in form
    # trough a hidden field. There ought to be a more elegant solution.
    def get_context_data(self, **kwargs):
        context = super(RegisterAttendance, self).get_context_data(**kwargs)
        lecture_pk = self.kwargs.get("lecture_pk")
        context['lecture'] = lecture_pk
        context['lect']= Lecture.objects.get(pk=lecture_pk)
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(self.request)
        context['site'] = site
        return context

    # Upon succes the form's cleaned data is available. Use to send message.
    def form_valid(self,form):
        cleaned_data = form.cleaned_data
        usr = cleaned_data['UvANetID']
        try:
            student = Student.objects.get(username__iexact=usr)
            logger.debug("ShowName: Student '{}' found for ".format(student) + \
                    "UvANetID '{}'.".format(usr))
            name = student.first_name + ' ' + student.last_name
            if name == ' ':
                name = usr
                logger.debug("UvANetID: '{}' has empty name.".format(name))
        except Student.DoesNotExist:
            name = "Name Unknown"
            logger.debug("ShowName: Student '{}' not found.".format(usr))
            try:
                profile = RegistrationProfile.objects.get(other_id__iexact=usr)
                logger.debug("ShowName: profile '{}' found for"\
                        .format(profile.user) + "UvANetID '{}'.".format(usr))
                student = Student.objects.get(id=profile.user_id)
                name = student.first_name + ' ' + student.last_name
            except RegistrationProfile.DoesNotExist:
                name = "Name Unknown"
                logger.debug("ShowName: profile '{}' not found.".format(usr))
        lecture = Lecture.objects.get(id=cleaned_data['lecture_pk'])

        msg = '<span class="glyphicon glyphicon-ok"></span> '+\
                '%(UvANetID)s is now registered as attending %(lect)s.' % \
                { 'UvANetID': usr, 'lect': lecture } +\
                '<br><h1>%(name)s</h1>' % { 'name' : name }
        messages.add_message(self.request, messages.SUCCESS, msg)
        return redirect(self.get_success_url())


    # Upon success, return to the form itself.
    def get_success_url(self):
        return self.request.get_full_path()

# Helper functions to generate column names (A-Z, AA-ZZ, etc) for Excel
def base_26_gen(x):
    if x == 0: yield x
    while x > 0:
        yield x % 26
        x //= 26

def base_26_chr(x):
    return ''.join(string.uppercase[i] for i in reversed(list(base_26_gen(x))))

def get_excel_col_names(x):
    # fails for aa, ab, .., az because a is treated as a zero
    col_names = [base_26_chr(x) for x in range(x)]

    # add aa, ab, .., az in the utmost ugly way possible.
    aa_trough_az = ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', \
            'AJ', 'AK', 'AL', 'AM', 'AN', 'AO', 'AP', 'AQ', 'AR', 'AS',\
            'AT', 'AU', 'AV', 'AW', 'AX', 'AY', 'AZ']
    if x < 26:
        result = col_names[0:x+1]
    elif x < 52:
        result = col_names[0:26] + aa_trough_az[0:(x-25)]
    else:
        result = col_names[0:26] + aa_trough_az + col_names[26:x-25]
    return result

# Error with non-authenticated users (timeout). Perhaps examine
# https://djangosnippets.org/snippets/1768/ for a fix?
@user_passes_test(lambda u: u.is_superuser)
def save_to_xls(request, course_pk):
    """
        Requires xlwt and helper functions base_26_chr (thus base_26_chr).

        This function enables exporting a xls database of the course attendance
        data. The format used is the current format used for Orientatie.
        Note that there is an 'off-by-one' due to xlwt's count starts at row 0,
        whereas Excel starts at row 1.
    """

    course = Course.objects.get(id=course_pk)
    xls = xlwt.Workbook(encoding='utf8')
    sheet = xls.add_sheet('CARD Data')

    # Define custom styles.
    plain = xlwt.Style.default_style
    borders = xlwt.easyxf(\
            'borders: top thin, right thin, bottom  thin, left thin;')
    bold = xlwt.easyxf('font: bold on;')
    boldborders = xlwt.easyxf('font: bold on;'+ \
        'borders: top thin, right thin, bottom  thin, left thin;')
    datetime_style = xlwt.easyxf(num_format_str='[$-413]d/mmm;@',\
            strg_to_parse='borders: top thin, right thin, bottom  thin,'+\
            ' left thin; font: bold on;')
    #date_style = xlwt.easyxf(num_format_str='dd/mm/yyyy')

    # Create header.
    sheet.write(0, 0, 'Aanwezigheidsregistratie %s' % course.name, \
            style=bold)
    sheet.write(1, 0, '1= aanwezig 0= afwezig', style=plain)

    sheet.write(2, 0, 'Student ID' , style=boldborders)
    sheet.write(2, 1, 'UvANetID' , style=boldborders)
    sheet.write(2, 2, 'First Name' , style=boldborders)
    sheet.write(2, 3, 'Last Name' , style=boldborders)
    sheet.write(2, 4, 'Email' , style=boldborders)
    sheet.write(2, 5, 'Programme' , style=boldborders)
    sheet.write(2, 6, 'Vorig jaar aanwezig' , style=boldborders)
    row = 3
    col = 7
    header = False;
    for student in course.student.all():
        #  Insert student details. Data according to current Orientatie format.
        try:
            profile = RegistrationProfile.objects.get(user_id=student)
            sheet.write(row, 0, profile.other_id, style=borders)
            sheet.write(row, 5, profile.programme , style=borders)
            sheet.write(row, 6, profile.offset , style=borders)
        except RegistrationProfile.DoesNotExist:
            pass # Perhaps catch this error in a more elegant way.
        sheet.write(row, 1, student.username , style=borders)
        sheet.write(row, 2, student.first_name , style=borders)
        sheet.write(row, 3, student.last_name , style=borders)
        sheet.write(row, 4, student.email , style=borders)

        # Insert student attendance data: 1 for attending, 0 for absent.
        col = 7
        for lecture in Lecture.objects.filter(course_id=course.id)\
                .order_by('date'):
            if not header:
                date = timezone.make_naive(lecture.date,\
                        timezone.get_default_timezone())
                sheet.write(2, col, date , style=datetime_style)
            attending = lecture.attending.all()
            if student in attending: val = 1
            else: val = 0
            sheet.write(row, col, val, style=borders)
            col += 1
        header = True
        row += 1

    # Create sum function for total per-lecture count.
    col_names = get_excel_col_names(col)
    for i in range(7, col):
        sheet.write(row+2, i, xlwt.Formula('SUM(%(ncol)s4:%(ncol)s%(myRow)s)'\
                % { 'ncol': col_names[i], 'myRow': row}),style=plain)

    # Create sum function for total per-student count.
    sheet.write(2, col, 'Total', style=boldborders)
    for i in range(3, row):
        sheet.write(i, col, xlwt.Formula('SUM(G%(myRow)s:%(ncol)s%(myRow)s)'\
                % { 'ncol': col_names[col-1], 'myRow': i+1}),style=plain)
    # Create sum function for total attended count
    sheet.write(row+2, col, xlwt.Formula('SUM(G%(myRow)s:%(ncol)s%(myRow)s)'\
            % { 'myRow': row+3, 'ncol':col_names[col-1] }), style=plain)

    # Return a response that allows to download the xls-file.
    fname = u'CARD Data %(course)s tm %(now)s.xls' % { \
            'course': course.name, \
            'now' : datetime.now().strftime("%s" % ("%d %b %Y")) \
            }
    response = HttpResponse(mimetype='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="%s"' % (fname)
    xls.save(response)
    return response

def quick_validate(sheet):
    valid, msg = True, ''
    if sheet.cell_value(2,0) != 'Student ID':
        msg += 'A3 invalid. '
        valid = False
    if sheet.cell_value(2,1) != 'UvANetID':
        msg += 'B3 invalid. '
        valid = False
    if sheet.cell_value(2,2) != 'First Name':
        msg += 'C3 invalid. '
        valid = False
    if  sheet.cell_value(2,3) != 'Last Name':
        msg += 'D3 invalid. '
        valid = False
    if sheet.cell_value(2,4) != 'Email':
        msg += 'E3 invalid. '
        valid = False
    if sheet.cell_value(2,5) != 'Programme':
        msg += '3F invalid. '
        valid = False
    if sheet.cell_value(2,6) != 'Vorig jaar aanwezig':
        msg += '3G invalid. '
        valid = False

    return valid, msg


@user_passes_test(lambda u: u.is_superuser)
def save_lectures_to_xls(request, course_pk):
    """
        Requires xlwt and helper functions base_26_chr (thus base_26_chr).

        This function enables exporting a xls database of the lecture
        descriptions.
        Note that there is an 'off-by-one' due to xlwt's count starts at row 0,
        whereas Excel starts at row 1.
    """

    course = Course.objects.get(id=course_pk)
    xls = xlwt.Workbook(encoding='utf8')
    sheet = xls.add_sheet('CARD Lecture Descriptions')

    # Define custom styles.
    plain = xlwt.Style.default_style
    borders = xlwt.easyxf(\
            'borders: top thin, right thin, bottom  thin, left thin;')
    bold = xlwt.easyxf('font: bold on;')
    boldborders = xlwt.easyxf('font: bold on;'+ \
        'borders: top thin, right thin, bottom  thin, left thin;')
    datetime_style = xlwt.easyxf(num_format_str='[$-413]d/mmm;@',\
            strg_to_parse='borders: top thin, right thin, bottom  thin,'+\
            ' left thin; font: bold on;')
    #date_style = xlwt.easyxf(num_format_str='dd/mm/yyyy')

    # Create header.
    sheet.write(0, 0, 'Lecture Description %s' % course.name, \
            style=bold)

    sheet.write(2, 0, 'Date' , style=boldborders)
    sheet.write(2, 1, 'Lecturer' , style=boldborders)
    sheet.write(2, 2, 'Title' , style=boldborders)
    sheet.write(2, 3, 'Description' , style=boldborders)
    # sheet.write(2, 4, '# Students attended' , style=boldborders)
    row = 3
    for lecture in Lecture.objects.filter(course_id=course.id)\
            .order_by('date'):
        date = timezone.make_naive(lecture.date,\
                timezone.get_default_timezone())
        sheet.write(row, 0, date , style=datetime_style)
        sheet.write(row, 1, lecture.lecturers, style=datetime_style)
        sheet.write(row, 2, lecture.title, style=datetime_style)
        sheet.write(row, 3, lecture.abstract, style=datetime_style)
        # sheet.write(row, 4, lecture.attending, style=datetime_style)
        row += 1

    # Return a response that allows to download the xls-file.
    fname = u'CARD Lecture Descriptions %(course)s tm %(now)s.xls' % { \
            'course': course.name, \
            'now' : datetime.now().strftime("%s" % ("%d %b %Y")) \
            }
    response = HttpResponse(mimetype='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="%s"' % (fname)
    xls.save(response)
    return response

def add_import_data(request, sheet, datemode, course_pk):
    """
    Rows contain per-student information.
    Row 0, 1 and 2 are the header; 2 contains column names.

    A3 trough G3 contains per-student variables. H3 - col(end of row-1)3
    contains the lecture information. The last column is the total attendance.

    Row nrows contains the sum-functions for per-lecture averages.
    There are 2 whitelines between the last entry and the averages.

    Assume quick-validation did not find weird stuff and the excel sheet is
    valid. Also, remember the off-by one for xlrd and Excel row numbering.
    """

    # Firstly, create the lectures. Note that we only know the date w/o the year!
    logger.debug("Now running add_import_data.")
    logger.debug("Datemode: '{}'.".format(datemode))
    for col_nr in range(7, sheet.ncols-1):
        raw_date = sheet.cell_value(2, col_nr)
        logger.debug("Raw date: '{}'.".format(raw_date))
        date = datetime(*xlrd.xldate_as_tuple(raw_date, datemode))
        logger.debug("Converted date: '{}'.".format(date))
        title = 'Lecture ' + str(col_nr-6)
        slug = 'IIFPSVV62015-' + str(col_nr-6)
        try:
            lecture = Lecture.objects.get(date__exact=date)
            logger.debug("Found lecture '{}'.".format(lecture))
        except Lecture.DoesNotExist:
            lecture = Lecture.objects.create_lecture(course_pk, date, \
                    title, 'R', slug)
            lecture.save()
            logger.debug("Created lecture '{}'.".format(lecture))
    logger.debug("All lectures exist, or created.")

    if Site._meta.installed:
        site = Site.objects.get_current()
    else:
        site = RequestSite(request)
    chars = string.ascii_uppercase+string.digits
    # Secondly, get or create the students and add the data known from Excel.
    for row_nr in range(3, sheet.nrows-3):
        # Get or create student. Add data to student/profile.
        other_id = unicode(sheet.cell_value(row_nr, 0)).split('.')[0]
        UvANetID = unicode(sheet.cell_value(row_nr, 1)).split('.')[0]
        # Student login will work with UvANetID's, but registration will
        # use the other_id. All students started before Sept '10 may have
        # Student ID's that differ from their UvANetID. Thanks to SIS...
        try:
            student = Student.objects.get(username__exact=UvANetID)
            logger.debug("Found student '{}'.".format(student))
        except Student.DoesNotExist:
            # User does not exist, create new user.
            email = sheet.cell_value(row_nr, 4)
            password = ''.join(random.choice(chars) for x in range(12))
            first_name = sheet.cell_value(row_nr, 2)
            last_name = sheet.cell_value(row_nr, 3)
            surfConnextID = 'excel/None'
            new_user = RegistrationProfile.objects.create_active_user(UvANetID, \
                    email, password, first_name, last_name, surfConnextID, site)
            profile = RegistrationProfile.objects.get(user_id=new_user)
            profile.other_id = other_id
            profile.programme = sheet.cell_value(row_nr, 5)
            profile.offset = sheet.cell_value(row_nr, 6)
            profile.save()
            student = Student.objects.get(pk=new_user.id)
            logger.debug("Created student '{}'.".format(student))
        course = Course.objects.get(pk=course_pk)
        logger.debug("StudentCourses '{}'.".format(student.StudentCourses.all()))
        if course not in student.StudentCourses.all():
            student.StudentCourses.add(course_pk)
            student.save()
            logger.debug("Course '{}' not in ".format(course)+\
                    "StudentCourses of '{}'; added.".format(student))

        # Lastly, add the attendance of known Lectures to known Students.
        # It might be wise to loop for cols for row to save queries?
        for col_nr in range(7, sheet.ncols-1):
            raw_date = sheet.cell_value(2, col_nr)
            date = datetime(*xlrd.xldate_as_tuple(raw_date, datemode))
            lecture = Lecture.objects.get(date__exact=date)
            status = sheet.cell_value(row_nr, col_nr)
            if status == 1:
                lecture.attending.add(student)
                logger.debug("Student '{}' ".format(student) +\
                        "now attending '{}'.".format(lecture))
                lecture.save()
            elif status == 0:
                logger.debug("Student '{}' ".format(student) +\
                        "did not attend '{}'.".format(lecture))

    logger.debug("All students exist or created. All attendance registered.")


@user_passes_test(lambda u: u.is_superuser)
@csrf_protect
def read_from_xls(request, course_pk):
# https://stackoverflow.com/questions/3665379/django-and-xlrd-reading-from-memory/3665672#3665672

    """
        Requires xlrd and helper functions base_26_chr (thus base_26_chr).

        This function enables importing a xls database of the course attendance
        data. The format used is the current format used for Orientatie.
        Note that there is an 'off-by-one' due to xlrd's count starts at row 0,
        whereas Excel starts at row 1.

        Be cautious in using this function as unexpected behaviour may occur!
    """

    backup_url = reverse('education:export', kwargs={'course_pk': course_pk})
    text = '<span class= "glyphicon glyphicon-floppy-save"></span> Export'
    msg = '<span class="glyphicon glyphicon-warning-sign"></span> '+\
                'Warning! Importing overwrites the current database. ' + \
                'Be sure to <a href="%s">%s</a> first!' % \
                (backup_url, text)
    messages.add_message(request, messages.WARNING, msg)
    msg = '<span class="glyphicon glyphicon-warning-sign"></span> '+\
                'Warning! Make sure the Excel file has the same format as ' + \
                'the exported file!'
    messages.add_message(request, messages.WARNING, msg)
    if request.method == 'POST':
        form = XlsInputForm(request.POST, request.FILES)
        if form.is_valid():
            input_excel = request.FILES['input_excel']
            book = xlrd.open_workbook(file_contents=input_excel.read())
            sheet = book.sheet_by_index(0)

            # Quick and dirty fix: validation of row 3.
            valid, msg = quick_validate(sheet)
            if valid:
                try:
                    add_import_data(request, sheet, book.datemode, course_pk)
                    msg = '<span class="glyphicon glyphicon-ok"></span> '+\
                            'Import successfull!'
                    messages.add_message(request, messages.SUCCESS, msg)
                except Exception as e:
                    # logger.error(e)
                    logger.exception("Error in import function:")
                    msg = '<span class="glyphicon glyphicon-flash"></span> '+\
                            'Import failed due to unknown reasons.'+\
                            'The data may have been compromised, mail admin!'
                    messages.add_message(request, messages.ERROR, msg)

            else:
                tmp = msg
                msg = '<span class="glyphicon glyphicon-flash"></span> '+\
                        'Import failed: ' + msg
                messages.add_message(request, messages.ERROR, msg)

            # This should eventually redirect / render_to_response to
            # admin_course. Simply changing results in course_pk not passed.
            return HttpResponseRedirect(reverse('education:admin_course', \
                    kwargs={'course_pk': course_pk}))
    else:
        form = XlsInputForm()

    return render_to_response('education/import_excel.html', {'form': form},\
            context_instance=RequestContext(request))

    #html = "<html><body>%s </body></html>" % user
    #return HttpResponse(html)

from CARD.settings import STATIC_ROOT
class Barcode(generic.ListView):
    model = Barcode
    template_name = 'education/barcode.html'
    #pk_url_kwarg = 'course_pk'

    def get_context_data(self, **kwargs):
        context = super(Barcode, self).get_context_data(**kwargs)
        # Symbology-specific arrays

        context['barcode'] = generate_code39(self.kwargs.get("value"))
        context['value'] = self.kwargs.get("value")


        return context

# http://notionovus.com/blog/code-39-barcode-biscuits/
def generate_code39(value):
    code39_binary = {
        '0':'1010001110111010','1':'1110100010101110','2':'1011100010101110',\
        '3':'1110111000101010','4':'1010001110101110','5':'1110100011101010',\
        '6':'1011100011101010','7':'1010001011101110','8':'1110100010111010',\
        '9':'1011100010111010','A':'1110101000101110','B':'1011101000101110',\
        'C':'1110111010001010','D':'1010111000101110','E':'1110101110001010',\
        'F':'1011101110001010','G':'1010100011101110','H':'1110101000111010',\
        'I':'1011101000111010','J':'1010111000111010','K':'1110101010001110',\
        'L':'1011101010001110','M':'1110111010100010','N':'1010111010001110',\
        'O':'1110101110100010','P':'1011101110100010','Q':'1010101110001110',\
        'R':'1110101011100010','S':'1011101011100010','T':'1010111011100010',\
        'U':'1110001010101110','V':'1000111010101110','W':'1110001110101010',\
        'X':'1000101110101110','Y':'1110001011101010','Z':'1000111011101010',\
        '-':'1000101011101110','.':'1110001010111010',' ':'1000111010111010',\
        '$':'1000100010001010','/':'1000100010100010','+':'1000101000100010', \
        '%':'1010001000100010','*':'1000101110111010'
    }

    #strCode39 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%*"

    strText = "value"
    strRaw = ""
    for i in range(len(strText)):
        strRaw += code39_binary[strText[i].upper()];

    return strRaw
