from django.conf.urls import patterns, url

#from education.forms import AttendanceForm
from education import views

urlpatterns = patterns('',
        url(r'^$', views.IndexView.as_view(), name='index'),
        url(r'^(?P<course_pk>\d+)/$', views.CourseView.as_view(),name='course'),
        url(r'^(?P<course_pk>\d+)/lecture/(?P<lecture_pk>\d+)/$', \
                views.LectureView.as_view(),name='lecture'),
        url(r'^admin/$', views.AdminIndexView.as_view(),\
                name='admin_index'),
        url(r'^(?P<course_pk>\d+)/admin/$',\
                views.AdminCourseView.as_view(),name='admin_course'),
        url(r'^(?P<course_pk>\d+)/lecture/(?P<lecture_pk>\d+)/admin/$', \
                views.AdminLectureView.as_view(),name='admin_lecture'),
        url(r'^(?P<course_pk>\d+)/student/(?P<student_pk>\d+)/$', \
                views.AdminStudentView.as_view(),name='admin_student'),
        url(r'^(?P<course_pk>\d+)/lecture/(?P<lecture_pk>\d+)/register/$',\
                views.RegisterAttendance.as_view(),name='register_form'),
        url(r'(?P<course_pk>\d+)/export/$', views.save_to_xls, \
            name='export'),
        )
