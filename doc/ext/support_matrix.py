# Copyright (C) 2014 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
This provides a sphinx extension able to render the source/support-matrix.ini
file into the developer documentation.

It is used via a single directive in the .rst file

  .. support_matrix::

"""
import os

import six
import six.moves.configparser as config_parser
import sys

from docutils import nodes
from docutils.parsers import rst
from designate.backend.base import Backend
from designate.backend.agent_backend.base import AgentBackend
from sphinx.util.osutil import copyfile


class SupportMatrix(object):
    """Represents the entire support matrix for Nova virt drivers
    """

    def __init__(self):
        # List of SupportMatrixFeature instances, describing
        # all the features present in Nova virt drivers
        self.grades = []

        self.grade_names = {}
        self.grade_classes = {}

        # Dict of (name, SupportMatrixTarget) enumerating
        # all the hypervisor drivers that have data recorded
        # for them in self.features. The 'name' dict key is
        # the value from the SupportMatrixTarget.key attribute
        self.backends = {}


class SupportMatrixGrade(object):

    def __init__(self, key, title, notes, in_tree, css_class):
        self.key = key
        self.title = title
        self.notes = notes
        self.in_tree = in_tree
        self.css_class = css_class


class SupportMatrixBackend(object):

    def __init__(self, key, title, status,
                 maintainers=None, variations=None,
                 repository=None, type=None):
        self.key = key
        self.title = title
        self.type = type
        self.status = status
        self.maintainers = maintainers
        self.variations = variations
        self.repository = repository


class SupportMatrixDirective(rst.Directive):

    option_spec = {
        'support-matrix': unicode,
    }

    def run(self):
        matrix = self._load_support_matrix()
        return self._build_markup(matrix)

    def _load_support_matrix(self):
        """Reads the support-matrix.ini file and populates an instance
        of the SupportMatrix class with all the data.

        :returns: SupportMatrix instance
        """

        # SafeConfigParser was deprecated in Python 3.2
        if sys.version_info >= (3, 2):
            cfg = config_parser.ConfigParser()
        else:
            cfg = config_parser.SafeConfigParser()
        env = self.state.document.settings.env
        fname = self.options.get("support-matrix",
                                 "support-matrix.ini")
        rel_fpath, fpath = env.relfn2path(fname)
        with open(fpath) as fp:
            cfg.readfp(fp)

        # This ensures that the docs are rebuilt whenever the
        # .ini file changes
        env.note_dependency(rel_fpath)

        matrix = SupportMatrix()

        # The 'targets' section is special - it lists all the
        # hypervisors that this file records data for
        for item in cfg.options("backends"):
            if not item.startswith("backend-impl-"):
                continue

            # The driver string will optionally contain
            # a hypervisor and architecture qualifier
            # so we expect between 1 and 3 components
            # in the name
            key = item[13:]
            title = cfg.get("backends", item)
            name = key.split("-")

            try:
                status = cfg.get("backends.%s" % item, "status")
            except config_parser.NoOptionError:
                if cfg.get("backends.%s" % item, "type") == "xfr":
                    backend = Backend.get_driver(name[0])
                elif cfg.get("backends.%s" % item, "type") == "agent":
                    backend = AgentBackend.get_driver(name[0])
                status = backend.__backend_status__

            if len(name) == 1:
                backend = SupportMatrixBackend(
                    key, title, status, name[0])
            elif len(name) == 2:
                backend = SupportMatrixBackend(
                    key, title, status, name[0], variations=name[1])
            else:
                raise Exception("'%s' field is malformed in '[%s]' section" %
                                (item, "DEFAULT"))

            backend.in_tree = cfg.getboolean(
                "backends.%s" % item, "in-tree")
            backend.type = cfg.get(
                "backends.%s" % item, "type")
            backend.notes = cfg.get(
                "backends.%s" % item, "notes")
            backend.repository = cfg.get(
                "backends.%s" % item, "repository")
            backend.maintainers = cfg.get(
                "backends.%s" % item, "maintainers")

            matrix.backends[key] = backend

        grades = cfg.get("grades", "valid-grades")

        grades = grades.split(",")

        for grade in grades:
            title = cfg.get("grades.%s" % grade, "title")
            notes = cfg.get("grades.%s" % grade, "notes")
            in_tree = cfg.get("grades.%s" % grade, "in-tree")
            css_class = cfg.get("grades.%s" % grade, "css-class")

            matrix.grade_names[grade] = title
            matrix.grade_classes[grade] = css_class

            grade = SupportMatrixGrade(
                grade, title, notes, in_tree, css_class)

            matrix.grades.append(grade)

        return matrix

    def _build_markup(self, matrix):
        """Constructs the docutils content for the support matrix
        """
        content = []
        self._build_grade_listing(matrix, content)
        self._build_grade_table(matrix, content)
        self._build_backend_detail(matrix, content)
        return content

    def _build_backend_detail_table(self, backend, matrix):

        table = nodes.table()
        table.set_class("table")
        table.set_class("table-condensed")
        tgroup = nodes.tgroup(cols=2)
        tbody = nodes.tbody()

        for i in range(2):
            tgroup.append(nodes.colspec(colwidth=1))

        tgroup.append(tbody)
        table.append(tgroup)

        graderow = nodes.row()
        gradetitle = nodes.entry()
        gradetitle.append(nodes.strong(text="Grade"))
        gradetext = nodes.entry()
        class_name = "label-%s" % matrix.grade_classes[backend.status]
        status_text = nodes.paragraph(
            text=matrix.grade_names[backend.status])
        status_text.set_class(class_name)
        status_text.set_class("label")
        gradetext.append(status_text)
        graderow.append(gradetitle)
        graderow.append(gradetext)
        tbody.append(graderow)

        treerow = nodes.row()
        treetitle = nodes.entry()
        treetitle.append(nodes.strong(text="In Tree"))
        if bool(backend.in_tree):
            status = u"\u2714"
            intree = nodes.paragraph(text=status)
            intree.set_class("label")
            intree.set_class("label-success")

        else:
            status = u"\u2716"
            intree = nodes.paragraph(text=status)
            intree.set_class("label")
            intree.set_class("label-danger")
            status = u"\u2714"
        treetext = nodes.entry()
        treetext.append(intree)
        treerow.append(treetitle)
        treerow.append(treetext)
        tbody.append(treerow)

        maintrow = nodes.row()
        mainttitle = nodes.entry()
        mainttitle.append(nodes.strong(text="Maintainers"))
        mainttext = nodes.entry()
        mainttext.append(nodes.paragraph(text=backend.maintainers))
        maintrow.append(mainttitle)
        maintrow.append(mainttext)
        tbody.append(maintrow)

        reporow = nodes.row()
        repotitle = nodes.entry()
        repotitle.append(nodes.strong(text="Repository"))
        repotext = nodes.entry()
        repotext.append(nodes.paragraph(text=backend.repository))
        reporow.append(repotitle)
        reporow.append(repotext)
        tbody.append(reporow)

        noterow = nodes.row()
        notetitle = nodes.entry()
        notetitle.append(nodes.strong(text="Notes"))
        notetext = nodes.entry()
        notetext.append(nodes.paragraph(text=backend.notes))
        noterow.append(notetitle)
        noterow.append(notetext)
        tbody.append(noterow)

        return table

    def _build_backend_detail(self, matrix, content):

        detailstitle = nodes.subtitle(text="Backend Details")

        content.append(detailstitle)

        for key in six.iterkeys(matrix.backends):

            content.append(
                nodes.subtitle(text=matrix.backends[key].title))
            content.append(
                self._build_backend_detail_table(
                    matrix.backends[key],
                    matrix))

            content.append(nodes.line())

        return content

    def _build_grade_listing(self, matrix, content):

        summarytitle = nodes.subtitle(text="Grades")
        content.append(nodes.raw(text="Grades", attributes={'tagname': 'h2'}))
        content.append(summarytitle)
        table = nodes.table()
        table.set_class("table")
        table.set_class("table-condensed")
        grades = matrix.grades

        tablegroup = nodes.tgroup(cols=2)
        summarybody = nodes.tbody()
        summaryhead = nodes.thead()

        for i in range(2):
            tablegroup.append(nodes.colspec(colwidth=1))
        tablegroup.append(summaryhead)
        tablegroup.append(summarybody)
        table.append(tablegroup)
        content.append(table)

        header = nodes.row()
        blank = nodes.entry()
        blank.append(nodes.strong(text="Grade"))
        header.append(blank)

        blank = nodes.entry()
        blank.append(nodes.strong(text="Description"))
        header.append(blank)

        summaryhead.append(header)

        for grade in grades:
            item = nodes.row()
            namecol = nodes.entry()
            class_name = "label-%s" % grade.css_class
            status_text = nodes.paragraph(text=grade.title)
            status_text.set_class(class_name)
            status_text.set_class("label")
            namecol.append(status_text)
            item.append(namecol)

            notescol = nodes.entry()
            notescol.append(nodes.paragraph(text=grade.notes))
            item.append(notescol)

            summarybody.append(item)

        return content

    def _build_grade_table(self, matrix, content):

        summarytitle = nodes.subtitle(text="Backends -  Summary")
        summary = nodes.table()
        summary.set_class("table")
        summary.set_class("table-condensed")
        cols = len(list(six.iterkeys(matrix.backends)))
        cols += 2
        summarygroup = nodes.tgroup(cols=cols)
        summarybody = nodes.tbody()
        summaryhead = nodes.thead()

        for i in range(cols):
            summarygroup.append(nodes.colspec(colwidth=1))
        summarygroup.append(summaryhead)
        summarygroup.append(summarybody)
        summary.append(summarygroup)
        content.append(summarytitle)
        content.append(summary)

        header = nodes.row()
        blank = nodes.entry()
        blank.append(nodes.strong(text="Backend"))
        header.append(blank)

        blank = nodes.entry()
        blank.append(nodes.strong(text="Status"))
        header.append(blank)

        blank = nodes.entry()
        blank.append(nodes.strong(text="Type"))
        header.append(blank)

        blank = nodes.entry()
        blank.append(nodes.strong(text="In Tree"))
        header.append(blank)

        blank = nodes.entry()
        blank.append(nodes.strong(text="Notes"))
        header.append(blank)
        summaryhead.append(header)

        grades = matrix.grades
        impls = list(six.iterkeys(matrix.backends))
        impls.sort()
        for grade in grades:
            for backend in impls:
                if matrix.backends[backend].status == grade.key:
                    item = nodes.row()
                    namecol = nodes.entry()
                    namecol.append(
                        nodes.paragraph(text=matrix.backends[backend].title))
                    item.append(namecol)

                    statuscol = nodes.entry()
                    class_name = "label-%s" % grade.css_class
                    status_text = nodes.paragraph(text=grade.title)
                    status_text.set_class(class_name)
                    status_text.set_class("label")
                    statuscol.append(status_text)
                    item.append(statuscol)

                    typecol = nodes.entry()
                    type_text = nodes.paragraph(
                        text=matrix.backends[backend].type)
                    type_text.set_class("label")
                    type_text.set_class("label-info")
                    typecol.append(type_text)
                    item.append(typecol)

                    if bool(matrix.backends[backend].in_tree):
                        status = u"\u2714"
                        intree = nodes.paragraph(text=status)
                        intree.set_class("label")
                        intree.set_class("label-success")

                    else:
                        status = u"\u2716"
                        intree = nodes.paragraph(text=status)
                        intree.set_class("label")
                        intree.set_class("label-danger")

                    intreecol = nodes.entry()
                    intreecol.append(intree)
                    item.append(intreecol)

                    notescol = nodes.entry()
                    notescol.append(nodes.paragraph(
                        text=matrix.backends[backend].notes))
                    item.append(notescol)

                    summarybody.append(item)

        return content


def copy_assets(app, exception):
    assets = ['support-matrix.css', 'support-matrix.js']
    if app.builder.name != 'html' or exception:
        return
    app.info('Copying assets: %s' % ', '.join(assets))
    for asset in assets:
        dest = os.path.join(app.builder.outdir, '_static', asset)
        source = os.path.abspath(os.path.dirname(__file__))
        copyfile(os.path.join(source, 'assets', asset), dest)


def add_assets(app):
    app.add_stylesheet('support-matrix.css')
    app.add_javascript('support-matrix.js')


def setup(app):

    # Add all the static assets to our build during the early stage of building
    app.connect('builder-inited', add_assets)

    # This copies all the assets (css, js, fonts) over to the build
    # _static directory during final build.
    app.connect('build-finished', copy_assets)

    app.add_directive('support_matrix', SupportMatrixDirective)
