from django.conf.urls import patterns, include, url
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.simple import direct_to_template

from registration.views import activate
from registration.views import register

from accounts.forms import RegistrationForm

admin.autodiscover()

handler404 = 'trans.views.not_found'

js_info_dict = {
    'packages': ('weblate',),
}

admin.site.index_template = 'admin/custom-index.html'

urlpatterns = patterns('',
    url(r'^$', 'trans.views.home'),
    url(r'^projects/$', 'django.views.generic.simple.redirect_to', {'url': '/'}),
    url(r'^projects/(?P<project>[^/]*)/$', 'trans.views.show_project'),

    url(r'^dictionaries/(?P<project>[^/]*)/$', 'trans.views.show_dictionaries'),
    url(r'^dictionaries/(?P<project>[^/]*)/(?P<lang>[^/]*)/$', 'trans.views.show_dictionary'),
    url(r'^dictionaries/(?P<project>[^/]*)/(?P<lang>[^/]*)/upload/$', 'trans.views.upload_dictionary'),
    url(r'^dictionaries/(?P<project>[^/]*)/(?P<lang>[^/]*)/delete/$', 'trans.views.delete_dictionary'),
    url(r'^dictionaries/(?P<project>[^/]*)/(?P<lang>[^/]*)/edit/$', 'trans.views.edit_dictionary'),

    url(r'^projects/(?P<project>[^/]*)/(?P<subproject>[^/]*)/$', 'trans.views.show_subproject'),
    url(r'^projects/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/$', 'trans.views.show_translation'),
    url(r'^projects/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/translate/$', 'trans.views.translate'),
    url(r'^projects/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/download/$', 'trans.views.download_translation'),
    url(r'^projects/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/upload/$', 'trans.views.upload_translation'),
    url(r'^projects/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/auto/$', 'trans.views.auto_translation'),

    url(r'^commit/(?P<project>[^/]*)/$', 'trans.views.commit_project'),
    url(r'^commit/(?P<project>[^/]*)/(?P<subproject>[^/]*)/$', 'trans.views.commit_subproject'),
    url(r'^commit/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/$', 'trans.views.commit_translation'),

    url(r'^update/(?P<project>[^/]*)/$', 'trans.views.update_project'),
    url(r'^update/(?P<project>[^/]*)/(?P<subproject>[^/]*)/$', 'trans.views.update_subproject'),
    url(r'^update/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/$', 'trans.views.update_translation'),

    url(r'^push/(?P<project>[^/]*)/$', 'trans.views.push_project'),
    url(r'^push/(?P<project>[^/]*)/(?P<subproject>[^/]*)/$', 'trans.views.push_subproject'),
    url(r'^push/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/$', 'trans.views.push_translation'),

    url(r'^languages/$', 'trans.views.show_languages'),
    url(r'^languages/(?P<lang>[^/]*)/$', 'trans.views.show_language'),

    url(r'^checks/$', 'trans.views.show_checks'),
    url(r'^checks/(?P<name>[^/]*)/$', 'trans.views.show_check'),
    url(r'^checks/(?P<name>[^/]*)/(?P<project>[^/]*)/$', 'trans.views.show_check_project'),
    url(r'^checks/(?P<name>[^/]*)/(?P<project>[^/]*)/(?P<subproject>[^/]*)/$', 'trans.views.show_check_subproject'),

    url(r'^hooks/update/(?P<project>[^/]*)/(?P<subproject>[^/]*)/$', 'trans.api.update_subproject'),
    url(r'^hooks/update/(?P<project>[^/]*)/$', 'trans.api.update_project'),
    url(r'^hooks/github/$', 'trans.api.github_hook'),

    url(r'^exports/stats/(?P<project>[^/]*)/(?P<subproject>[^/]*)/$', 'trans.api.export_stats'),

    url(r'^js/get/(?P<checksum>[^/]*)/$', 'trans.views.get_string'),
    url(r'^js/ignore-check/(?P<check_id>[0-9]*)/$', 'trans.views.ignore_check'),
    url(r'^js/i18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    url(r'^js/config/$', 'trans.views.js_config'),
    url(r'^js/similar/(?P<unit_id>[0-9]*)/$', 'trans.views.get_similar'),
    url(r'^js/other/(?P<unit_id>[0-9]*)/$', 'trans.views.get_other'),
    url(r'^js/dictionary/(?P<unit_id>[0-9]*)/$', 'trans.views.get_dictionary'),
    url(r'^js/git/(?P<project>[^/]*)/$', 'trans.views.git_status_project'),
    url(r'^js/git/(?P<project>[^/]*)/(?P<subproject>[^/]*)/$', 'trans.views.git_status_subproject'),
    url(r'^js/git/(?P<project>[^/]*)/(?P<subproject>[^/]*)/(?P<lang>[^/]*)/$', 'trans.views.git_status_translation'),

    # Admin interface
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/report/$', 'trans.admin_views.report'),
    url(r'^admin/', include(admin.site.urls)),

    # Auth
    url(r'^accounts/register/$', register, {
            'form_class': RegistrationForm,
            'extra_context': {'title': _('User registration')}},
            name='weblate_register'),
    url(r'^accounts/register/complete/$',
        direct_to_template,
        {
            'template': 'registration/registration_complete.html',
            'extra_context': {'title': _('User registration')},
        },
        name='registration_complete'),
    url(r'^accounts/activate/(?P<activation_key>\w+)/$',
        activate,
        {'extra_context': {'title': _('Account activation')}},
        name='registration_activate'),
    url(r'^accounts/login/$',
        auth_views.login,
        {
            'template_name': 'registration/login.html',
            'extra_context': {'title': _('Login')},
        },
        name='auth_login'),
    url(r'^accounts/logout/$',
        auth_views.logout,
        {
            'template_name': 'registration/logout.html',
            'extra_context': {'title': _('Logged out')},
        },
        name='auth_logout'),
    url(r'^accounts/password/change/$',
        auth_views.password_change,
        {'extra_context': {'title': _('Change password')}},
        name='auth_password_change'),
    url(r'^accounts/password/change/done/$',
        auth_views.password_change_done,
        {'extra_context': {'title': _('Password changed')}},
        name='auth_password_change_done'),
    url(r'^accounts/password/reset/$',
        auth_views.password_reset,
        {'extra_context': {'title': _('Password reset')}},
        name='auth_password_reset'),
    url(r'^accounts/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.password_reset_confirm,
        {'extra_context': {'title': _('Password reset')}},
        name='auth_password_reset_confirm'),
    url(r'^accounts/password/reset/complete/$',
        auth_views.password_reset_complete,
        {'extra_context': {'title': _('Password reset')}},
        name='auth_password_reset_complete'),
    url(r'^accounts/password/reset/done/$',
        auth_views.password_reset_done,
        {'extra_context': {'title': _('Password reset')}},
        name='auth_password_reset_done'),
    url(r'^accounts/profile/', 'accounts.views.profile'),

    url(r'^contact/', 'accounts.views.contact'),
    url(r'^about/$', 'trans.views.about'),

    # Media files
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': './media'}),
)