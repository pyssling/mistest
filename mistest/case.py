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

import logging
import os
import subprocess
from tap import *
from xml.etree.ElementTree import Element
from test import *

class CaseNotExecutable(Exception):
    """Test case is not executable"""
    pass

class CaseExecutionResult(TestExecutionResult):
    """The result of a test case execution run"""

    def __init__(self, case):
        TestExecutionResult.__init__(self, case)
        self.case = case
        self.tap_list = []

    def __iter__(self):
        for tap in self.tap_list:
            yield tap

    def append(self, tap):
        self.tap_list.append(tap)

    def __str__(self):
        result = "# "
        if self.failed:
            return "# failed: " + str(self.failed)

        if self.planned is not None:
            result += "planned: " + str(self.planned) + " "
        result += "ran: " + str(self.ran) + " "
        result += "ok: " + str(self.ok) + " "
        result += "not ok: " + str(self.not_ok) + " "
        result += "skip: " + str(self.skip) + " "
        result += "todo: " + str(self.todo)
        return result


class Case(Test):
    """A test case

    Will fork and execute a provided test case, parsing the stdout during
    execution."""

    def __init__(self, file, sequence, parent, directives=None):

        Test.__init__(self)

        if not os.path.isfile(file):
            raise CaseNotExecutable("No such test case " + file)
        if not os.access(file, os.X_OK):
            raise CaseNotExecutable("Test case not executable " + file)

        self.file = file
        self.directives = directives
        self.popen = None
        self.parent = parent
        self.execution_results = []
        self.sequence = sequence

    def __generate_args(self, directives):
        arguments = []

        if self.directives and self.directives.arguments:
            arguments.append(self.directives.arguments)

        if directives:
            arguments.append(directives.arguments)

        return arguments

    def __call__(self, parser, directives=None):

        arguments = self.__generate_args(directives)

        command = [ self.file ] + arguments

        popen = subprocess.Popen(command, stdout=subprocess.PIPE)

        # Set the parser input stream
        parser = parser(popen.stdout)
        result = CaseExecutionResult(self)

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

    def junit(self):
        element = Element('testsuite')
        element.attrib['name'] = self.junit_name()
        if len(self) == 1:
            for tap in self.execution_results[0]:
                if isinstance(tap, TestLine):
                    element.append(tap.junit())

        return element

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

