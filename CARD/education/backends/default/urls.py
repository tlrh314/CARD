"""
URLconf for education Student attendance registration.

If the default behavior of these views is acceptable to you, simply
use a line like this in your root URLconf to set up the default URLs
for education:

    (r'^education/', include('education.backends.default.urls')),

If you'd like to customize education behavior, feel free to set up
your own URL patterns for these views instead.

"""

from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from education.backends.default.views import AttendanceView
from education.forms import AttendanceForm
from education import views

urlpatterns = patterns('',
        #url(r'^attendance/$',AttendanceView.as_view(form_class=\
        #        AttendanceForm), name='attendance_register'),
        #url(r'^attendance/closed/$',
        #    TemplateView.as_view(template_name='attendance/attendance_closed.html'),
        #    name='attendance_disallowed'),
        url(r'^$', views.IndexView.as_view(), name='index'),
        url(r'^(?P<pk>\d+)/$', views.DetailView.as_view(),name='detail'),
        url(r'^admin$', views.AdminIndexView.as_view(),name='admin_index'),
        url(r'^admin/(?P<pk>\d+)/$',\
                views.AdminDetailView.as_view(),name='admin_detail'),
        )
