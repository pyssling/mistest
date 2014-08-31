#
# Copyright 2014 Nils Carlson
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

import io
import yaml
import os
import case
from xml.etree.ElementTree import Element

class SuiteParseException(Exception):
    """Failed to create a suite instance"""
    pass

class SubSuiteException(Exception):
    """Failed to parse an included suite"""
    pass

class Directives:
    """Suite or test case directives"""

    def __init__(self, directives_list):
        pass

class Suite:
    """A test suite parser

    Will read a test suite and generate a corresponding
    object."""

    def __init__(self, file=None, stream=None, name=None, suite=None,
                 top_level_suite=False):

        self.dependencies = []
        self.directives = []
        self.test_list = []
        self.suite = suite
        self.top_level_suite = top_level_suite

        if name:
            self.name = name
            self.dir = os.curdir
        elif file:
            self.name = os.path.relpath(file)
            self.dir = os.path.dirname(self.name)
            stream = open(file)

        if stream:
            suite = yaml.safe_load(stream)
        else:
            suite = {}

        if 'Dependencies' in suite:
            self.dependencies = suite['Dependencies']

        if 'Directives' in suite:
            self.directives = suite['Directives']

        if suite:
            if not 'Suite' in suite:
                raise SuiteParseException("No suite declaration in suite")

            for test in suite['Suite']:
                if isinstance(test, dict):
                    test, directives = test.popitem()
                self.append(test)

    def append(self, test):
        if test.endswith('.yaml'):
            try:
                self.test_list.append(Suite(self.dir + "/" + test, suite=self))
            except Exception as e:
                raise SubSuiteException(str(e))
        else:
            self.test_list.append(case.Case(self.dir + "/" + test, suite=self))

    def junit(self):
        element = Element('testsuite')

        if not self.top_level_suite:
            element.attrib['name'] = self.junit_name()

        for test in self.test_list:
            element.append(test.junit())

        return element

    def junit_name(self):
        # This is an aesthetic decision, do not include the top level
        # suite in junit output.
        if self.top_level_suite:
            return None

        junit_name = ""

        if self.suite:
            parent_junit_name = self.suite.junit_name()
            if parent_junit_name:
                junit_name += parent_junit_name + "."

        junit_name += self.name.replace('.','_')
        return junit_name

    def __iter__(self):
        for test in self.test_list:
            if isinstance(test, Suite):
                for suite_test in test:
                    yield suite_test
            else:
                yield test

    def __str__(self):
        return self.name

def looks_like_a_suite(file):
    if file.endswith(".yaml") and os.path.isfile(file):
        return True
    else:
        return False
