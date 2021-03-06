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

import os
import logging

logger = logging.getLogger('weblate')


def get_root_dir():
    '''
    Returns Weblate root dir.
    '''
    curdir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(curdir, '..'))


def is_running_git():
    '''
    Checks whether we're running inside Git checkout.
    '''
    return os.path.exists(os.path.join(get_root_dir(), '.git'))

# Weblate version
VERSION = '1.6'

# Are we running git
RUNNING_GIT = is_running_git()
GIT_RELEASE = False

# Grab some information from git
if RUNNING_GIT:
    try:
        import git
        # Describe current checkout
        GIT_VERSION = git.Repo(get_root_dir()).git.describe()

        # Check if we're close to release tag
        parts = GIT_VERSION.split('-')
        GIT_RELEASE = (len(parts) <= 2 or int(parts[2]) < 20)
        del parts

        # Mark version as devel if it is
        if not GIT_RELEASE:
            VERSION += '-dev'
    except (ImportError, git.exc.GitCommandError):
        # Import failed or git has troubles reading
        # repo (eg. swallow clone)
        RUNNING_GIT = False


def get_doc_url(page, anchor=''):
    '''
    Return URL to documentation.
    '''
    # Should we use tagged release or latest version
    if RUNNING_GIT and not GIT_RELEASE:
        version = 'latest'
    else:
        version = 'weblate-%s' % VERSION
    # Generate URL
    url = 'http://weblate.readthedocs.org/en/%s/%s.html' % (version, page)
    # Optionally append anchor
    if anchor != '':
        url += '#%s' % anchor

    return url
