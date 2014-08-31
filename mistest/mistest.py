#!/usr/bin/python
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

import argparse
import copy
import os
import sys
import case
import suite
from scheduler import *
from output import Output

def parse_separated(resources_and_tests):
    top_level_suite = suite.Suite(name="Top level suite", top_level_suite=True)
    resources = resources_and_tests[0:resources_and_tests.index('-')]

    for test in resources_and_tests[resources_and_tests.index('-') + 1:]:
        try:
            if suite.looks_like_a_suite(test) or case.looks_like_a_case(test):
                top_level_suite.append(test)
            else:
                sys.exit(test + " does not appear to be a test case or suite")
        except Exception as e:
                sys.exit("Error while parsing " + test + ": " + str(e))

    return (resources, top_level_suite)

def parse_unseparated(resources_and_tests):
    top_level_suite = suite.Suite(name="Top level suite", top_level_suite=True)
    resources = []

    args_are_resources = True
    for test_or_resource in resources_and_tests:

        # Test for suites or test cases.
        try:
            if suite.looks_like_a_suite(test_or_resource) \
                    or case.looks_like_a_case(test_or_resource):
                top_level_suite.append(test_or_resource)
                args_are_resources = False
            elif args_are_resources:
                resources.append(test_or_resource)
            else:
                sys.exit(test_or_resource + " does not appear to be a"
                         " test case or suite")
        except Exception as e:
            sys.exit("Error while parsing " + test_or_resource + ": " + str(e))

    return (resources, top_level_suite)

def parse_mistest_args(argv):

    parser = argparse.ArgumentParser(description='Execute a mistest run.')

    parser.add_argument('resource', nargs='*', help='A test resource.')
    parser.add_argument('separator', nargs='?', metavar='-',
                        choices=['-'], help='Resource and test separator')
    parser.add_argument('test', nargs='+', help='A suite or test case.')
    parser.add_argument('--immediate-output', action='store_true',
                        help='Print output immediately, even during parallel execution')
    parser.add_argument('--junit-xml', '-j', help='Generate a junit xml file')


    args = parser.parse_args(argv[1:])

    # The resource/suite division is a fake, python will accumulate all values
    # but the last in resource, so post-parsing is needed.
    resources_and_tests = args.resource + args.test

    if '-' in resources_and_tests:
        (resources, top_level_suite) = parse_separated(resources_and_tests)
    else:
        (resources, top_level_suite) = parse_unseparated(resources_and_tests)

    output = Output()

    if len(resources) < 1:
        resources.append("local")

    if len(resources) > 1:
        output.set_prefix_with_resource(True)

    if args.junit_xml:
        output.set_junit_xml(args.junit_xml)

    if args.immediate_output:
        output.set_immediate(True)

    return (resources, top_level_suite, output)


# Main function
(resources, top_level_suite, output) = parse_mistest_args(sys.argv)
schedule_tests(resources, top_level_suite, output)
output.postprocess(top_level_suite)
