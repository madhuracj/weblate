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

from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse

from trans.models import Translation, Dictionary
from lang.models import Language
from trans.util import get_site_url
from trans.forms import WordForm, DictUploadForm, LetterForm
from trans.views.helper import get_project
import weblate

import csv


def show_dictionaries(request, project):
    obj = get_project(request, project)
    dicts = Translation.objects.filter(
        subproject__project=obj
    ).values_list('language', flat=True).distinct()

    return render_to_response('dictionaries.html', RequestContext(request, {
        'title': _('Dictionaries'),
        'dicts': Language.objects.filter(id__in=dicts),
        'project': obj,
    }))


@login_required
@permission_required('trans.change_dictionary')
def edit_dictionary(request, project, lang):
    prj = get_project(request, project)
    lang = get_object_or_404(Language, code=lang)
    word = get_object_or_404(
        Dictionary,
        project=prj,
        language=lang,
        id=request.GET.get('id')
    )

    if request.method == 'POST':
        form = WordForm(request.POST)
        if form.is_valid():
            word.source = form.cleaned_data['source']
            word.target = form.cleaned_data['target']
            word.save()
            return HttpResponseRedirect(reverse(
                'show_dictionary',
                kwargs={'project': prj.slug, 'lang': lang.code}
            ))
    else:
        form = WordForm(
            initial={'source': word.source, 'target': word.target}
        )

    return render_to_response('edit_dictionary.html', RequestContext(request, {
        'title': _('%(language)s dictionary for %(project)s') %
        {'language': lang, 'project': prj},
        'project': prj,
        'language': lang,
        'form': form,
    }))


@login_required
@permission_required('trans.delete_dictionary')
def delete_dictionary(request, project, lang):
    prj = get_project(request, project)
    lang = get_object_or_404(Language, code=lang)
    word = get_object_or_404(
        Dictionary,
        project=prj,
        language=lang,
        id=request.POST.get('id')
    )

    word.delete()

    return HttpResponseRedirect(reverse(
        'show_dictionary',
        kwargs={'project': prj.slug, 'lang': lang.code})
    )


@login_required
@permission_required('trans.upload_dictionary')
def upload_dictionary(request, project, lang):
    prj = get_project(request, project)
    lang = get_object_or_404(Language, code=lang)

    if request.method == 'POST':
        form = DictUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                count = Dictionary.objects.upload(
                    prj,
                    lang,
                    request.FILES['file'],
                    form.cleaned_data['method']
                )
                if count == 0:
                    messages.warning(
                        request,
                        _('No words to import found in file.')
                    )
                else:
                    messages.info(
                        request,
                        _('Imported %d words from file.') % count
                    )
            except Exception as e:
                messages.error(
                    request,
                    _('File upload has failed: %s' % unicode(e))
                )
        else:
            messages.error(request, _('Failed to process form!'))
    else:
        messages.error(request, _('Failed to process form!'))
    return HttpResponseRedirect(reverse(
        'show_dictionary',
        kwargs={'project': prj.slug, 'lang': lang.code}
    ))


def download_dictionary_ttkit(export_format, prj, lang, words):
    '''
    Translate-toolkit builder for dictionary downloads.
    '''
    # Use translate-toolkit for other formats
    if export_format == 'po':
        # Construct store
        from translate.storage.po import pofile
        store = pofile()

        # Export parameters
        mimetype = 'text/x-po'
        extension = 'po'
        has_lang = False

        # Set po file header
        store.updateheader(
            add=True,
            language=lang.code,
            x_generator='Weblate %s' % weblate.VERSION,
            project_id_version='%s (%s)' % (lang.name, prj.name),
            language_team='%s <%s>' % (
                lang.name,
                get_site_url(reverse(
                    'show_dictionary',
                    kwargs={'project': prj.slug, 'lang': lang.code}
                )),
            )
        )
    else:
        # Construct store
        from translate.storage.tbx import tbxfile
        store = tbxfile()

        # Export parameters
        mimetype = 'application/x-tbx'
        extension = 'tbx'
        has_lang = True

    # Setup response and headers
    response = HttpResponse(mimetype='%s; charset=utf-8' % mimetype)
    filename = 'glossary-%s-%s.%s' % (prj.slug, lang.code, extension)
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    # Add words
    for word in words.iterator():
        unit = store.UnitClass(word.source)
        if has_lang:
            unit.settarget(word.target, lang.code)
        else:
            unit.target = word.target
        store.addunit(unit)

    # Save to response
    store.savefile(response)

    return response


def download_dictionary(request, project, lang):
    '''
    Exports dictionary into various formats.
    '''
    prj = get_project(request, project)
    lang = get_object_or_404(Language, code=lang)

    # Parse parameters
    export_format = None
    if 'format' in request.GET:
        export_format = request.GET['format']
    if not export_format in ['csv', 'po', 'tbx']:
        export_format = 'csv'

    # Grab all words
    words = Dictionary.objects.filter(
        project=prj,
        language=lang
    ).order_by('source')

    # Translate toolkit based export
    if export_format in ('po', 'tbx'):
        return download_dictionary_ttkit(export_format, prj, lang, words)

    # Manually create CSV file
    response = HttpResponse(mimetype='text/csv; charset=utf-8')
    filename = 'dictionary-%s-%s.csv' % (prj.slug, lang.code)
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    writer = csv.writer(response)

    for word in words.iterator():
        writer.writerow((
            word.source.encode('utf8'), word.target.encode('utf8')
        ))

    return response


def show_dictionary(request, project, lang):
    prj = get_project(request, project)
    lang = get_object_or_404(Language, code=lang)

    if (request.method == 'POST'
            and request.user.has_perm('trans.add_dictionary')):
        form = WordForm(request.POST)
        if form.is_valid():
            Dictionary.objects.create(
                project=prj,
                language=lang,
                source=form.cleaned_data['source'],
                target=form.cleaned_data['target']
            )
        return HttpResponseRedirect(request.get_full_path())
    else:
        form = WordForm()

    uploadform = DictUploadForm()

    words = Dictionary.objects.filter(
        project=prj, language=lang
    ).order_by('source')

    limit = request.GET.get('limit', 25)
    page = request.GET.get('page', 1)

    letterform = LetterForm(request.GET)

    if letterform.is_valid() and letterform.cleaned_data['letter'] != '':
        words = words.filter(
            source__istartswith=letterform.cleaned_data['letter']
        )
        letter = letterform.cleaned_data['letter']
    else:
        letter = ''

    paginator = Paginator(words, limit)

    try:
        words = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        words = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        words = paginator.page(paginator.num_pages)

    return render_to_response('dictionary.html', RequestContext(request, {
        'title': _('%(language)s dictionary for %(project)s') %
        {'language': lang, 'project': prj},
        'project': prj,
        'language': lang,
        'words': words,
        'form': form,
        'uploadform': uploadform,
        'letterform': letterform,
        'letter': letter,
    }))
