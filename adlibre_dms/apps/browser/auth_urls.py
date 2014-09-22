# Authentication urls
from django.conf.urls import patterns, url

urlpatterns = patterns('django.contrib.auth.views',
    url(
        r'^password/reset/$',
        'password_reset',
        {'post_reset_redirect': '/user/password/reset/done/'},
        name='pwd_reset'
    ),
    (r'^password/reset/done/$', 'password_reset_done'),
    (
        r'^password/reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'password_reset_confirm',
        {'post_reset_redirect': '/user/password/done/'}
    ),
    (r'^password/done/$', 'password_reset_complete'),
)