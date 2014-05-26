import logging
import subprocess
import tap.parser

class ExecutionResult:
    """The result of an Executor run

    Will contain the result of an executor run"""

    planned = 0
    run = 0
    ok = 0
    skip = 0
    todo = 0

class Executor:
    """A testcase executor

    Will fork and execute a provided testcase, parsing the stdout during
    execution."""

    command = []
    popen = None

    def __init__(self, command, result_queue=None):
        self.command = command

    def execute(self):
        popen = subprocess.Popen(self.command, stdout=subprocess.PIPE)
        parser = tap.parser.Parser(popen.stdout)
        result = ExecutionResult()

        try:
            for tap_output in parser:

                if isinstance(tap_output, tap.parser.Plan):
                    result.planned = tap_output.number

                if isinstance(tap_output, tap.parser.TestLine):
                    result.run += 1
                    if tap_output.ok:
                        result.ok += 1
                    if tap_output.directive:
                        if tap_output.directive == "TODO":
                            result.todo += 1
                        if tap_output.directive == "SKIP":
                            result.skip += 1

                logging.info(tap_output)
        except Exception as e:
            logging.error(e)

# Self test by forking off a child which will print the test output.
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "child":
        print(sys.argv[2].strip())
        quit()

    def __run_self_test(tap_str):
        executor = Executor(["python3.3", __file__, "child", tap_str])
        executor.execute()


    # Test 1
    plan = __run_self_test("1..4 # all of them\n")

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

