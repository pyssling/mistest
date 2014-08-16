import logging
import os
import subprocess
import tap

class CaseNotExecutable(Exception):
    """Test case is not executable"""
    pass

class CaseExecutionResult:
    """The result of a test case execution run"""

    def __init__(self):
        self.planned = None
        self.run = 0
        self.ok = 0
        self.skip = 0
        self.todo = 0
        self.failure = None

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

    def __generate_args(self, directives):
        arguments = []

        if self.directives and self.directives.arguments:
            arguments.append(self.directives.arguments)

        if directives:
            arguments.append(directives.arguments)

        return arguments

    def __generate_results(self, stream, result_queue, streaming):
        parser = tap.Parser(stream)

        result = CaseExecutionResult()

        try:
            for tap_output in parser:
                if isinstance(tap_output, tap.Plan):
                    if streaming and result.planned:
                        result_queue.put(result)
                        result = CaseExecutionResult()

                    result.planned = tap_output.number

                if streaming and not result.planned:
                    result.failed = "No plan at start of streaming test case"
                    result_queue.put(result)
                    return

                if isinstance(tap_output, tap.TestLine):
                    result.run += 1
                    if tap_output.ok:
                        result.ok += 1
                    if tap_output.directive:
                        if tap_output.directive == "TODO":
                            result.todo += 1
                        if tap_output.directive == "SKIP":
                            result.skip += 1

                print(tap_output)

        except Exception as e:
            result.failed = str(e)

        result_queue.put(result)

    def __call__(self, result_queue, directives=None):

        arguments = self.__generate_args(directives)

        command = [ self.file ] + arguments

        popen = subprocess.Popen(command, stdout=subprocess.PIPE)

        self.__generate_results(popen.stdout, result_queue, False)

    def __str__(self):
        return self.file

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

