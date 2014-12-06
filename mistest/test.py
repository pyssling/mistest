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

class TestExecutionResult:
    """An execution result template class

    A general form for other test execution result classes to inherit.
    Multiple TestExecutionResults may exist for each test"""

    def __init__(self, test):
        """Initialize the TestExecutionResult

        Initialization takes as argument the test that created the result."""
        self.test = test
        self.planned = None
        self.ran = 0
        self.ok = 0
        self.not_ok = 0
        self.skip = 0
        self.todo = 0
        self.failed = None

class Test:
    """A test template class

    A general form for other test classes to inherit"""

    def __init__(self):
        """Initialize the Test

        Create variables common to all tests."""

        self.planned = None
        self.ran = 0
        self.ok = 0
        self.not_ok = 0
        self.skip = 0
        self.todo = 0
        self.failed = None
