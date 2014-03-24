from django.shortcuts import render
from django.views import generic
from django.contrib.auth.decorators import permission_required
from django.views.generic.edit import FormView

from registration.views import _RequestPassingFormView

from education.models import Student, Course, Lecture
from education.forms import AttendanceForm

import logging

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

class DetailView(generic.DetailView):
    model = Course
    template_name = 'education/student_detail.html'

class AdminIndexView(generic.ListView):
    template_name = 'education/admin_index.html'
    context_object_name = 'all_course_list'

    def get_queryset(self):
        return Course.objects.all

class AdminDetailView(generic.DetailView):
    model = Course
    template_name = 'education/admin_detail.html'

  #def get_queryset(self):
    #course = Course.objects.get(pk=xxx)
    #return course.student.all()



class AttendanceView(_RequestPassingFormView):
    """
    Base class for Student attendance registration views.

    """
    disallowed_url = 'registration_disallowed'
    form_class = AttendanceForm
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    success_url = None
    template_name = 'education/attendance_form.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Check that user signup is allowed before even bothering to
        dispatch or do other processing.

        """
        if not self.registration_allowed(request):
            return redirect(self.disallowed_url)
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, request, form):
        # write to the database, also write to DataNose
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


