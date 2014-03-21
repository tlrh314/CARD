from django.conf.urls import patterns, url

from education import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>\d+)/$', views.DetailView.as_view(),name='detail'),
    url(r'^admin$', views.AdminIndexView.as_view(),name='admin_index'),
    url(r'^admin/(?P<pk>\d+)/$',\
      views.AdminDetailView.as_view(),name='admin_detail'),
)
