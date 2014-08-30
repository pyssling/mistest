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
import tap
import executor

class CaseNotExecutable(Exception):
    """Test case is not executable"""
    pass

class CaseExecutionResult:
    """The result of a test case execution run"""

    def __init__(self, case):
        self.case = case
        self.planned = None
        self.run = 0
        self.ok = 0
        self.skip = 0
        self.todo = 0
        self.failed = None
        self.tap_list = []

    def put(self, tap):
        self.tap_list.append(tap)

    def __iter__(self):
        for tap in tap_list:
            yield tap

    def __str__(self):
        result = ""
        if self.failed:
            return "failed: " + str(self.failed)

        if self.planned is not None:
            result += "planned: " + str(self.planned) + " "
        result += "run: " + str(self.run) + " "
        result += "ok: " + str(self.ok) + " "
        result += "skip: " + str(self.skip) + " "
        result += "todo: " + str(self.todo) + " "
        return result

class Case:
    """A test case

    Will fork and execute a provided test case, parsing the stdout during
    execution."""

    def __init__(self, file, directives=None, suite=None, result_queue=None):
        if not os.path.isfile(file):
            raise CaseNotExecutable("No such test case " + file)
        if not os.access(file, os.X_OK):
            raise CaseNotExecutable("Test case not executable " + file)

        self.file = file
        self.directives = directives
        self.popen = None
        self.suite = None
        self.execution_results = []

    def __generate_args(self, directives):
        arguments = []

        if self.directives and self.directives.arguments:
            arguments.append(self.directives.arguments)

        if directives:
            arguments.append(directives.arguments)

        return arguments

    def __generate_results(self, stream, executor, streaming):

        parser = executor.parser(stream)
        result = CaseExecutionResult(self)

        try:
            for tap_output in parser:

                # Handle plans, must be at the start of streaming
                # testcases
                if isinstance(tap_output, tap.Plan):
                    if streaming and result.planned:
                        executor.put(result)
                        result = CaseExecutionResult()

                    result.planned = tap_output.number

                # A testcase that doesn't start with a plan during
                # streaming causes a failure.
                if streaming and not result.planned:
                    result.failed = "No plan at start of streaming test case"
                    executor.put(result)
                    return

                # Accumulate output in counters
                if isinstance(tap_output, tap.TestLine):
                    result.run += 1
                    if tap_output.ok:
                        result.ok += 1
                    if tap_output.directive:
                        if tap_output.directive == "TODO":
                            result.todo += 1
                        if tap_output.directive == "SKIP":
                            result.skip += 1

                # Send output to the executor (for possible immediate
                # output) and also to the result for post processing.
                executor.put(tap_output)
                result.put(tap_output)

        except Exception as e:
            result.failed = str(e)

        executor.put(result)

    def __call__(self, executor, directives=None):

        arguments = self.__generate_args(directives)

        command = [ self.file ] + arguments

        popen = subprocess.Popen(command, stdout=subprocess.PIPE)

        self.__generate_results(popen.stdout, executor, False)

    def __str__(self):
        return self.file

    def put(self, execution_result):
        self.execution_results.append(execution_result)

    def __iter__(self):
        for execution_result in execution_results:
            yield execution_result

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

