from django.conf.urls import patterns, url

from processlogin import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^login', views.login_user, name='login'),
    url(r'^logout', views.logout_user, name='logout'),
    url(r'ivoauth/callback', views.ivoauth_callback, name='ivoauth_callback'),
    url(r'ivoauth$', views.ivoauth, name='ivoauth'),
)
