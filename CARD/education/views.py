from django.shortcuts import render
from django.views import generic

from education.models import Course, Lecture

class IndexView(generic.ListView):
    template_name = 'education/index.html'
    context_object_name = 'latest_course_list'

    def get_queryset(self):
        """Return the last five published polls."""
        return Course.objects.order_by('name')[:5]

class DetailView(generic.DetailView):
    model = Course
    template_name = 'education/detail.html'
