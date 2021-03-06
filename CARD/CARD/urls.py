from django.conf.urls import patterns, include, url

from django.contrib import admin
import admin_auth
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'CARD.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^courses/', include('education.urls',namespace="education"))
)
