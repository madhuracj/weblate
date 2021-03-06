# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2013 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <http://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.http import Http404
from django.db.models import Count

from trans.models import Unit, Check
from trans.checks import CHECKS
from trans.views.helper import get_project, get_subproject


def show_checks(request):
    '''
    List of failing checks.
    '''
    allchecks = Check.objects.filter(
        ignore=False
    ).values('check').annotate(count=Count('id'))
    return render_to_response('checks.html', RequestContext(request, {
        'checks': allchecks,
        'title': _('Failing checks'),
    }))


def show_check(request, name):
    '''
    Details about failing check.
    '''
    try:
        check = CHECKS[name]
    except KeyError:
        raise Http404('No check matches the given query.')

    checks = Check.objects.filter(
        check=name, ignore=False
    ).values('project__slug').annotate(count=Count('id'))

    return render_to_response('check.html', RequestContext(request, {
        'checks': checks,
        'title': check.name,
        'check': check,
    }))


def show_check_project(request, name, project):
    '''
    Show checks failing in a project.
    '''
    prj = get_project(request, project)
    try:
        check = CHECKS[name]
    except KeyError:
        raise Http404('No check matches the given query.')
    units = Unit.objects.none()
    if check.target:
        langs = Check.objects.filter(
            check=name, project=prj, ignore=False
        ).values_list('language', flat=True).distinct()
        for lang in langs:
            checks = Check.objects.filter(
                check=name, project=prj, language=lang, ignore=False
            ).values_list('checksum', flat=True)
            res = Unit.objects.filter(
                checksum__in=checks,
                translation__language=lang,
                translation__subproject__project=prj,
                translated=True
            ).values(
                'translation__subproject__slug',
                'translation__subproject__project__slug'
            ).annotate(count=Count('id'))
            units |= res
    if check.source:
        checks = Check.objects.filter(
            check=name,
            project=prj,
            language=None,
            ignore=False
        ).values_list(
            'checksum', flat=True
        )
        for subproject in prj.subproject_set.all():
            lang = subproject.translation_set.all()[0].language
            res = Unit.objects.filter(
                checksum__in=checks,
                translation__language=lang,
                translation__subproject=subproject
            ).values(
                'translation__subproject__slug',
                'translation__subproject__project__slug'
            ).annotate(count=Count('id'))
            units |= res

    return render_to_response('check_project.html', RequestContext(request, {
        'checks': units,
        'title': '%s/%s' % (prj.__unicode__(), check.name),
        'check': check,
        'project': prj,
    }))


def show_check_subproject(request, name, project, subproject):
    '''
    Show checks failing in a subproject.
    '''
    subprj = get_subproject(request, project, subproject)
    try:
        check = CHECKS[name]
    except KeyError:
        raise Http404('No check matches the given query.')
    units = Unit.objects.none()
    if check.target:
        langs = Check.objects.filter(
            check=name,
            project=subprj.project,
            ignore=False
        ).values_list(
            'language', flat=True
        ).distinct()
        for lang in langs:
            checks = Check.objects.filter(
                check=name,
                project=subprj.project,
                language=lang,
                ignore=False
            ).values_list('checksum', flat=True)
            res = Unit.objects.filter(
                translation__subproject=subprj,
                checksum__in=checks,
                translation__language=lang,
                translated=True
            ).values(
                'translation__language__code'
            ).annotate(count=Count('id'))
            units |= res
    source_checks = []
    if check.source:
        checks = Check.objects.filter(
            check=name, project=subprj.project,
            language=None,
            ignore=False
        ).values_list('checksum', flat=True)
        lang = subprj.translation_set.all()[0].language
        res = Unit.objects.filter(
            translation__subproject=subprj,
            checksum__in=checks,
            translation__language=lang
        ).count()
        if res > 0:
            source_checks.append(res)
    return render_to_response(
        'check_subproject.html',
        RequestContext(request, {
            'checks': units,
            'source_checks': source_checks,
            'anychecks': len(units) + len(source_checks) > 0,
            'title': '%s/%s' % (subprj.__unicode__(), check.name),
            'check': check,
            'subproject': subprj,
        })
    )
