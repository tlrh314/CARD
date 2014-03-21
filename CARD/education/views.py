from django.shortcuts import render
from django.views import generic

from education.models import Student, Course, Lecture

class IndexView(generic.ListView):
    template_name = 'education/index.html'
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
    template_name = 'education/detail.html'
