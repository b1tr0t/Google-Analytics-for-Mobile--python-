from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^track/$', 'ga_app.views.track', name='webcube_home'),
)