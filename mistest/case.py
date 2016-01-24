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

import os
import subprocess
from tap import TestLine
from xml.etree.ElementTree import Element
from test import Test,TestResult,TestExecutionResult

class CaseNotExecutable(Exception):
    """Test case is not executable"""
    pass


class CaseExecutionResult(TestExecutionResult):
    """The result of a test case execution run"""

    def __init__(self, case):
        TestExecutionResult.__init__(self, case)
        self.tap_list = []

    def __len__(self):
        if self.planned == None:
            return 0
        else:
            return self.planned

    def __getitem__(self, key):
        try:
            if key > (len(self) + 1) or key < 1:
                raise IndexError()
        except:
            raise IndexError()

        for tap in self.tap_list:
            if isinstance(tap, TestLine):
                if key == tap.number:
                    return tap

        # If not all tests in the case were run.
        return None

    def __iter__(self):
        for tap in self.tap_list:
            if isinstance(tap, TestLine):
                yield tap

    def append(self, tap):
        self.tap_list.append(tap)


class CaseInconsistentPlan(Exception):
    """Test case has inconsisten plane"""
    pass

class CaseTestLineAggregate(Tap):
    """A TAP test line aggregate

    Contains an ok which is either True or False,
    a number which is the test number in the sequence,
    a description and a directive and directive description."""

    def __init__(self, number, test_lines):
        """Initialize by aggregating the test lines

        Some aggregation is deffered such as creating string representations."""
        self.number = number
        self.test_lines = test_lines
        self.description = None
        self.directive = None

        self.ok = True
        skip_count = 0
        todo_count = 0
        for line in test_lines:
            # A single not ok makes everything not ok
            if line.ok == False:
                self.ok = False

            # Accumulate directives
            if line.directive == "TODO":
                todo_count += 1

            if line.directive == "SKIP":
                skip_count += 1

        if todo_count == len(test_lines):
            self.directive = "TODO"
        elif skip_count == len(test_lines):
            self.directive = "SKIP"

    def __str__(self):
        test_line = ("ok" if self.ok else "not ok") + " " + str(self.number)

        if self.description:
            test_line += " - " + self.description

        if self.directive:
            test_line += " # " + self.directive

            if self.directive_description:
                test_line += " " + self.directive_description

        return test_line

    def junit(self):
        element = Element('testcase')
        element.attrib['name'] = str(self)

        if not self.ok:
            failed = Element('failure')
            element.append(failed)

        return element


class CaseResult(TestResult):
    """The aggregated result of a test case"""

    def __init__(self, case, execution_results):
        TestResult.__init__(self, case)
        self.tap_aggregate_list = []
        self.execution_results = execution_results

    def __len__(self):
        if len(self.execution_results) == 0:
            return 0

        planned = self.execution_results[0].planned
        for result in self.execution_results:
            if result.planned != planned:
                raise CaseInconsistentPlan()

        return planned

    def __getitem__(self, key):
        try:
            if key > (len(self) + 1) or key < 1:
                raise IndexError()
        except:
            raise IndexError()

        if len(self.tap_aggregate_list) != len(self):
            for i in range(1, len(self) + 1):
                test_lines = [ result[i] for result in self.execution_results ]
                test_lines_aggregate = CaseTestLineAggregate(i, test_lines)
                self.tap_aggregate_list.append(test_lines_aggregate)

        return self.tap_aggregate_list[key - 1]

    def junit(self):
        element = Element('testsuite')
        element.attrib['name'] = self.test.junit_name()
        for i in range(1, len(self) + 1):
            element.append(self[i].junit())

        return element

    def append(self, execution_result):
        self.execution_results.append(execution_result)

class Case(Test):
    """A test case

    Will fork and execute a provided test case, parsing the stdout during
    execution."""

    def __init__(self, file, parent, sequence, arguments=[], environment=None, name=None):

        Test.__init__(self)

        if not os.path.isfile(file):
            raise CaseNotExecutable("No such test case " + file)
        if not os.access(file, os.X_OK):
            raise CaseNotExecutable("Test case not executable " + file)

        if not name:
            name = file

        self.file = file
        self.arguments = arguments
        self.environment = environment
        self.name = name
        self.popen = None
        self.parent = parent
        self.execution_results = []
        self.sequence = sequence

    def generate_result(self):
        self.result = CaseResult(self, self.execution_results)
        return self.result

    def __call__(self, parser, resource):

        command = [ self.file ] + self.arguments

        popen = subprocess.Popen(command, stdout=subprocess.PIPE,
                                 env=self.environment)

        # Set the parser input stream
        parser = parser(popen.stdout)
        result = CaseExecutionResult(self)

        # Create a tap Diagnostic to inform which test case has started
        yield Diagnostic("Running test case: \"" + self.name + "\" on " + resource)

        try:
            for tap_output in parser:

                # Handle plans
                if isinstance(tap_output, Plan):
                    result.planned = tap_output.number

                # Accumulate output in counters
                if isinstance(tap_output, TestLine):
                    result.ran += 1
                    if tap_output.ok:
                        result.ok += 1
                    else:
                        result.not_ok += 1

                    if tap_output.directive:
                        if tap_output.directive == "TODO":
                            result.todo += 1
                        if tap_output.directive == "SKIP":
                            result.skip += 1

                result.append(tap_output)

                yield tap_output

        except Exception as e:
            result.failed = str(e)

        self.execution_results.append(result)

        yield result

    def __str__(self):
        return self.file

    def junit_name(self):
        junit_name = ""

        parent_junit_name = self.parent.junit_name()
        if parent_junit_name:
            junit_name += parent_junit_name + '.'

        # Add a numbering onto the tests to retain order
        digits = len(str(len(self.parent)))
        digits += 1
        count_str = str(self.sequence).zfill(digits)

        basename = os.path.basename(self.file)
        basename = basename[0:basename.find('.')]
        junit_name += count_str + '_' + basename

        return junit_name


    def __iter__(self):
        for execution_result in self.execution_results:
            yield execution_result

    def __len__(self):
        return len(self.execution_results)

def looks_like_a_case(file):
    if os.access(file, os.X_OK):
        return True
    else:
        return False

# Self test by forking off a child which will print the test output.
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "child":
        print(sys.argv[2].strip())
        quit()

    def __run_self_test(tap_str):
        case = Case(["python3.3", __file__, "child", tap_str])
        case.execute()


    # Test 1
    plan = __run_self_test("1..4 # all of them\nok\nok\nok\nok")

    ok2 = __run_self_test("1..1\n" \
                            "ok 1\n" \
                            "ok 2\n")

    not_ok3 = __run_self_test("1..3\n" \
                                "ok 1 Hello\n" \
                                "ok 2 drat\n" \
                                "not ok Sometimes\n")

    ok_todo = __run_self_test("ok # ToDo the directive")

    not_ok_skip = __run_self_test("not ok # skip")

    not_tap = __run_self_test("a wtf")

    numbering_error = __run_self_test("ok\n" \
                                            "ok 3\n")
    plan_error = __run_self_test("1..1\n" \
                                       "ok\n" \
                                       "not ok\n")
    bail_out = __run_self_test("Bail out!")

