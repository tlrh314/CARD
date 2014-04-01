from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'CARD.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'ivoauth/callback', 'registration.views.ivoauth_callback'),
    url(r'ivoauth/$', 'registration.views.ivoauth', name='ivoauth'),
    url(r'^logout', 'registration.views.logout_user', name='logout'),
    url(r'^courses/', include('education.urls',namespace="education"))
)
