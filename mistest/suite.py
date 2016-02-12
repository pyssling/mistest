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

import yaml
import os
import case
from xml.etree.ElementTree import Element
from test import Test, TestResult, TestExecutionResult


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
            if not result.ok:
                self.ok = False

    def __str__(self):
        return (("ok" if self.ok else "not ok") + " " +
                str(self.suite.sequence) + " - " + str(self.suite))

    def junit(self):
        element = Element('testsuite')

        # Only add a name if we are not the top level suite
        # which is for all intents and purposes anonymous
        if self.suite.parent:
            element.attrib['name'] = self.suite.junit_name()

        for result in self.test_results:
            element.append(result.junit())

        return element


class Directives:
    """Suite or test case directives"""

    def __init__(self, directives_list):
        pass


class Suite(Test):
    """A test suite parser

    Will read a test suite and generate a corresponding
    object.

    Suites have directives: ordered, un-ordered or concurrent
    Suites can have dependencies: Depends: with relative path
    Test cases can have arguments, a list appended
    Test cases can have a name, a single string.
    """

    def __init__(self, name, parent=None, sequence=None):

        Test.__init__(self)

        self.name = name
        self.directives = []
        self.test_list = []
        self.parent = parent
        self.sequence = sequence
        self.ordering = 'sequential'

    def __eq__(self, other):
        return (self.name == other.name and
                self.dependencies == other.dependencies and
                self.directives == self.directives and
                self.test_list == self.test_list and
                self.ordering == self.ordering)

    def append_test(self, test):
        self.test_list.append(test)

    def set_ordering(self, ordering):
        self.ordering = ordering

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
        test_results = [test.generate_result() for test in self.test_list]
        self.result = SuiteResult(self, test_results)
        return self.result

    def __call__(self, parser, resource):
        """Run the test suite

        Executing one test case at a time and yielding each result.
        Retain the hierarchy of suites and cases by only saving
        the exection results from tests and suites inside the current
        suite.
        """
        execution_result = SuiteExecutionResult(self)

        for test in self:
            for result in test(parser, resource):
                try:
                    if result.test in self.test_list:
                        execution_result.append(result)
                except:
                    pass

                yield(result)

        yield(execution_result)

    def __iter__(self):
        for test in self.test_list:
            # Only suites have ordering
            try:
                if test.ordering == 'any':
                    for suite_test in test:
                        yield suite_test
            except AttributeError:
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


class SuiteParseException(Exception):
    """Failed to create a suite instance"""
    pass


class SubSuiteException(Exception):
    """Failed to parse an included suite"""
    pass


def validate_ordering(ordering):
    if not isinstance(ordering, str):
        raise SuiteParseException("Expected a scalar string as ordering")
    if not ordering.lower() in ['sequential', 'any']:
        raise SuiteParseException("Unknown ordering " + ordering)
    return ordering.lower()


def parse_yaml_tests(yaml_tests, dir, parent, sequence, dependencies=[]):
    """
    Parse a list of tests from the parsed yaml

    dir is the directory containing the tests
    parent is the parent suite
    sequence is the number of the test within the suite
    """

    if not isinstance(yaml_tests, list):
        raise SuiteParseException("Expected a list of tests")

    tests = []

    for test in yaml_tests:

        arguments = None

        # Tests are either a single entry in yaml, or they are multiple entries
        # inside a dict where the key is the path to the test-case.
        if isinstance(test, str):
            pass
        elif isinstance(test, dict):
            test_dict = test
            test, parameters = test_dict.popitem()
            if 'arguments' in parameters:
                arguments = parameters['arguments'].split(' ')

        else:
            raise SuiteParseException("Unexpected test format")

        test = os.path.normpath(dir + "/" + test)

        if looks_like_a_suite(test):
            tests.append(parse_yaml_suite(test, parent, sequence,
                                          dependencies))
        elif case.looks_like_a_case(test):
            tests.append(case.Case(test, parent, sequence, arguments,
                                   dependencies))
        else:
            raise SuiteParseException(test + " does not appear to be a \
                                      case or a suite")

        sequence = sequence + 1

    return (tests, sequence)


def parse_yaml_suite(file, parent, sequence, dependencies=[]):
    """
    Parse a yaml suite recursively.

    parent is the parent suite,
    sequence is the number of the test within the parent suite
    """

    dir = os.path.dirname(file)
    tests = []
    child_sequence = 1

    suite = Suite(file, parent, sequence)

    suite_dict = yaml.safe_load(open(file))

    # lowercase all the keys
    for key in suite_dict.keys():
        suite_dict[key.lower()] = suite_dict.pop(key)

    if 'ordering' in suite_dict:
        suite.ordering = validate_ordering(suite_dict.pop('ordering'))

    if 'dependencies' in suite_dict:
        # Dependencies are always parsed without any dependencies of their own.
        (suite_dependencies, child_sequence) = \
            parse_yaml_tests(suite_dict.pop('dependencies'), dir, suite,
                             child_sequence)
        # The total dependency list for a suite is always that of the suite
        # and that of the parent.
        dependencies += suite_dependencies

    if 'tests':
        (tests, child_sequence) = \
            parse_yaml_tests(suite_dict.pop('tests'),
                             dir, suite, child_sequence, dependencies)

    if len(suite_dict) != 0:
        raise SuiteParseException("Unknown elements in suite: ",
                                  map(str, suite_dict.keys()))

    if not tests:
        raise SuiteParseException("Suite did not contain any tests")

    for test in tests:
        suite.append_test(test)

    for dep in dependencies:
        suite.append_dep(dep)

    return suite
