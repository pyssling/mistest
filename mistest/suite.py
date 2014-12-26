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
from test import *

class SuiteExecutionResult(TestExecutionResult):
    """The result of a test case execution run"""

    def __init__(self, suite):
        TestExecutionResult.__init__(self, suite)
        self.suite = suite

    def append(self, execution_result):
        self.execution_results.append(execution_result)

class SuiteResult(TestResult):
    """The aggregated result of a test suite"""

    def __init__(self, suite, test_results):
        TestResult.__init__(self, suite)
        self.suite = suite
        self.test_results = test_results

        for result in test_results:
            if result.ok == False:
                self.ok = False

    def __str__(self):
        test_line = ("ok" if self.ok else "not ok") + " " + str(self.number)

        if self.description:
            test_line += " - " + self.description

        if self.directive:
            test_line += " # " + self.directive

            if self.directive_description:
                test_line += " " + self.directive_description

    def junit(self):
        element = Element('testsuite')

        # Only add a name if we are not the top level suite
        # which is for all intents and purposes anonymous
        if self.suite.parent:
            element.attrib['name'] = self.suite.junit_name()

        for result in self.test_results:
            element.append(result.junit())

        return element


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

class Suite(Test):
    """A test suite parser

    Will read a test suite and generate a corresponding
    object."""

    def __init__(self, file=None, sequence=None, parent=None, stream=None, name=None):

        Test.__init__(self)

        self.dependencies = []
        self.directives = []
        self.test_list = []
        self.parent = parent
        self.sequence = sequence

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
                self.test_list.append(Suite(self.dir + "/" + test,
                                            sequence=len(self.test_list) + 1,
                                            parent=self))
            except Exception as e:
                raise SubSuiteException(str(e))
        else:
            self.test_list.append(case.Case(self.dir + "/" + test,
                                            sequence=len(self.test_list) + 1,
                                            parent=self))

    def junit_name(self):
        # This is an aesthetic decision, do not include the top level
        # suite in junit output.
        if not self.parent:
            return None

        junit_name = ""

        if self.parent:
            parent_junit_name = self.parent.junit_name()
            if parent_junit_name:
                junit_name += parent_junit_name + '.'

        # Add a numbering onto the tests to retain order
        digits = len(str(len(self.parent)))
        digits += 1
        count_str = str(self.sequence).zfill(digits)

        basename = os.path.basename(self.name)
        basename = basename[0:basename.find('.')]
        junit_name += count_str + '_' + basename

        return junit_name

    def generate_result(self):
        test_results = [ test.generate_result() for test in self.test_list ]
        self.result = SuiteResult(self, test_results)
        return self.result

    def __call__(self, parser):
        """Run the test suite

        Executing one test case at a time and yielding each result.
        Retain the hierarchy of suites and cases by only saving
        the exection results from tests and suites inside the current
        suite.
        """
        execution_result = SuiteExecutionResult(self)

        for test in self:
            for result in test(parser):
                try:
                    if result.test in self.test_list:
                        execution_result.append(result)
                except:
                    pass

                yield(result)

    def __iter__(self):
        for test in self.test_list:
            if isinstance(test, Suite):
                for suite_test in test:
                    yield suite_test
            else:
                yield test

    def __len__(self):
        return len(self.test_list)

    def __str__(self):
        return self.name

def looks_like_a_suite(file):
    if file.endswith(".yaml") and os.path.isfile(file):
        return True
    else:
        return False
