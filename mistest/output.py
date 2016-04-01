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

from .tap import Tap
from .case import CaseExecutionResult
from xml.etree.ElementTree import Element,ElementTree

class Output:
    """The output class

    Handles output, both during execution and during post-processing"""

    def __init__(self):
        self.immediate = True
        self.prefix_with_resource = False
        self.junit_xml = None

    def set_immediate(self, immediate):
        self.immediate = immediate

    def set_prefix_with_resource(self, prefix):
        self.prefix_with_resource = prefix
    def set_junit_xml(self, junit_xml):
        self.junit_xml = junit_xml

    def format_result(self, result):
        output_str = ""

        if self.prefix_with_resource:
            output_str += str(result.resource) + " : "

        output_str += str(result)

        return output_str

    def __call__(self, result):

        if self.immediate and isinstance(result, Tap):
            print(self.format_result(result))
        elif not self.immediate and isinstance(result, CaseExecutionResult):
            for tap in result:
                print(self.format_result(tap))

        if isinstance(result, CaseExecutionResult):
            print(self.format_result(result))

    def output_junit_xml(self, suite):
        element = Element('testsuites')
        element.append(suite.junit())
        tree = ElementTree(element)
        tree.write(self.junit_xml)

    def output_execution_summary(self, suite):
        print("# Execution summary: ")
#        print("# Ran: " + str(suite.total) + " Passed: " + str(suite.passed) + \
#            " Skipped: " + str(suite.skipped) + " Failed: " + str(suite.failed))

    def postprocess(self, result):
        self.output_execution_summary(result)
        if self.junit_xml:
            self.output_junit_xml(result)

