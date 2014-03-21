from django.shortcuts import render
from django.views import generic
from django.contrib.auth.decorators import permission_required

from education.models import Student, Course, Lecture

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
