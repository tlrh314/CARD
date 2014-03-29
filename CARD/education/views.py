from django.shortcuts import render, redirect
from django.views import generic

from registration.views import _RequestPassingFormView
from registration.models import RegistrationProfile
from django.http import HttpResponseForbidden

from education.models import Student, Course, Lecture
from education.forms import AttendanceForm

import logging
from collections import defaultdict

logger = logging.getLogger('registration')

class IndexView(generic.ListView):
    template_name = 'education/student_index.html'
    context_object_name = 'latest_course_list'

    def get_queryset(self):
        # all students for a course
        #course = Course.objects.get(pk=xxxx)
        #course.student.all()
        student = Student.objects.get(pk=self.request.user.id)
        return student.StudentCourses.all()
        #return Course.objects.order_by('name')[:5]

class CourseView(generic.DetailView):
    model = Course
    pk_url_kwarg = 'course_pk'
    template_name = 'education/student_course.html'

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
        context = super(AdminCourseView, self).get_context_data(**kwargs)
        current_course = Course.objects.get(id=self.kwargs.get("course_pk"))
        context['course'] = current_course
        attendance = defaultdict(dict)
        for student in current_course.student.all():
            for abbreviation, fullname in Lecture.TYPES:
                attendance[student.username][abbreviation] = 0
            attendance[student.username]['total'] = 0
            for lecture in student.LectureStudents.all():
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

class AttendanceView(_RequestPassingFormView):
    """
    Base class for Student attendance registration views.

    """
    disallowed_url = 'education:attendance_disallowed'
    form_class = AttendanceForm
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    success_url = None
    template_name = 'education/attendance_form.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Check that lecture attendance registration is allowed before even
        bothering to dispatch or do other processing.
        """

        if not self.attendance_allowed(request):
            return redirect(self.disallowed_url)
        return super(AttendanceView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, request, form):
        # write to the database, also write to DataNose
        attending_student  = self.mark_as_attending(request, **form.cleaned_data)
        success_url = self.get_success_url(request, attending_student)

        # success_url may be a simple string, or a tuple providing the
        # full argument set for redirect(). Attempting to unpack it
        # tells us which one it is.
        try:
            to, args, kwargs = success_url
            return redirect(to, *args, **kwargs)
        except ValueError:
            return redirect(success_url)

    def attendance_allowed(self, request):
        """
        Override this to enable/disable user registration, either
        globally or on a per-request basis.

        """
        return True

    def mark_as_attending(self, request, **cleaned_data):
        """
        Implement user-registration logic here. Access to both the
        request and the full cleaned_data of the registration form is
        available here.

        """
        raise NotImplementedError
