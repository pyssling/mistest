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


class TestResult:
    """A test result template class

    A general form for other test result classes to inherit."""

    def __init__(self, test, planned=None, ran=0, ok=0, not_ok=0, skip=0,
                 todo=0, failed=None):
        """Initialize the TestExecutionResult

        Initialization takes as argument the test that created the result."""
        self.test = test
        self.planned = planned
        self.ran = ran
        self.ok = ok
        self.not_ok = not_ok
        self.skip = skip
        self.todo = todo
        self.failed = failed

    def __str__(self):
        result = "# "
        if self.failed:
            return "# Failed: " + str(self.failed)

        if self.planned is not None:
            result += "planned: " + str(self.planned) + " "
        result += "ran: " + str(self.ran) + " "
        result += "ok: " + str(self.ok) + " "
        result += "skip: " + str(self.skip) + " "
        result += "todo: " + str(self.todo) + " "
        return result

    def __eq__(self, other):
        return (self.test == other.test and
                self.planned == other.planned and
                self.ran == other.ran and
                self.ok == other.ok and
                self.not_ok == other.not_ok and
                self.skip == other.skip and
                self.todo == other.todo and
                self.failed == other.failed)


class TestExecutionResult(TestResult):
    """A test execution result template class

    A general form for other test execution result classes to inherit.
    Multiple TestExecutionResults may exist for each test"""


class Test:
    """A test template class

    A general form for other test classes to inherit"""

    def __init__(self):
        self.dependencies = []

    def __eq__(self, other):
        return self.dependencies == other.dependencies

    def append_dep(self, test):
        if not test in self.dependencies:
            self.dependencies.append(test)
