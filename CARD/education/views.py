from django.shortcuts import render, redirect
from django.views import generic
from django.contrib import messages
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site

from registration.views import _RequestPassingFormView
from registration.models import RegistrationProfile

from education.models import Student, Course, Lecture
from education.forms import RegisterAttendanceForm

import logging
from collections import defaultdict

logger = logging.getLogger('registration')

LECTURES_REQUIRED = 25

class IndexView(generic.ListView):
    template_name = 'education/student_index.html'
    context_object_name = 'latest_course_list'

    def get_queryset(self):
        # all students for a course
        #course = Course.objects.get(pk=xxxx)
        #course.student.all()
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
        for lecture in Lecture.objects.filter(course_id=current_course.id):
            for attending in lecture.attending.all():
                context['lecture'] = attending
                if self.request.user.username == attending.username:
                    progress += 1

        # Set visited, total and the percentage progress for progressbar.
        context['visited'] = progress
        context['total_lectures'] = LECTURES_REQUIRED
        progress = 100*float(progress)/LECTURES_REQUIRED
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

class AdminCourseView(generic.DetailView):
    model = Course
    pk_url_kwarg = 'course_pk'
    template_name = 'education/admin_course.html'

    def get_context_data(self, **kwargs):
        # Initialize the context and set up the current_course.
        context = super(AdminCourseView, self).get_context_data(**kwargs)
        current_course = Course.objects.get(id=self.kwargs.get("course_pk"))
        context['course'] = current_course

        # Initialize 2D array with keys UvANetID and type of Lecture.
        attendance = defaultdict(dict)
        for student in current_course.student.all():
            for abbreviation, fullname in Lecture.TYPES:
                attendance[student.username][abbreviation] = 0
            attendance[student.username]['total'] = 0

            # Calculate the attendance for all lectures in this course.
            for lecture in Lecture.objects.filter(course_id=current_course.id):
                if student in lecture.attending.all():
                    context['classification'] = lecture.classification
                    attendance[student.username][lecture.classification] += 1
                    attendance[student.username]['total'] += 1
        context['attendance'] = attendance

        return context
  #def get_queryset(self):
    #course = Course.objects.get(pk=xxx)
    #return course.student.all()

class AdminLectureView(generic.DetailView):
    model = Lecture
    pk_url_kwarg = 'lecture_pk'
    template_name = 'education/admin_lecture.html'

class RegisterAttendance(generic.FormView):
    template_name = 'education/register_attendance.html'
    form_class = RegisterAttendanceForm
    succes_url = None

    # Qiute the dirty fix: pass lecture_pk to template, then shove in form
    # trough a hidden field. There ought to be a more elegant solution.
    def get_context_data(self, **kwargs):
        context = super(RegisterAttendance, self).get_context_data(**kwargs)
        context['lecture'] = self.kwargs.get("lecture_pk")
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
        lecture = Lecture.objects.get(id=cleaned_data['lecture_pk'])

        #msg = '<span class="glyphicon glyphicon-ok"></span> '+\
        msg = '%s is now registered as attending %s' % (usr, lecture)
        messages.add_message(self.request, messages.SUCCESS, msg)
        return redirect(self.get_success_url())


    # Upon success, return to the form itself.
    def get_success_url(self):
        return self.request.get_full_path()
