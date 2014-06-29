#!/usr/bin/python

import case
import suite
import argparse
import os
import sys

parser = argparse.ArgumentParser(description='Execute a mistest run.')

parser.add_argument('resource', nargs='*', help='A test resource.')
parser.add_argument('separator', nargs='?', metavar='-',
                    choices=['-'], help='Resource and test separator')
parser.add_argument('test', nargs='+', help='A suite or test case.')

args = parser.parse_args()

# The resource/suite division is a fake, python will accumulate all values
# but the last in resource, so post-parsing is needed.
resources_and_tests = args.resource + args.test
top_level_suite = suite.Suite(name="Top level suite")

if '-' in resources_and_tests:
    resources = resources_and_tests[0:resources_and_tests.index('-')]
    for test in resources_and_tests[resources_and_tests.index('-') + 1:]:
        try:
            if suite.looks_like_a_suite(test) or case.looks_like_a_case(test):
                top_level_suite.append(test)
            else:
                sys.exit(test + " does not appear to be a"
                         " test case or suite")
        except Exception as e:
            sys.exit("Error while parsing " + test + ": " + str(e))

else:
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

for test in top_level_suite:
    test.execute()
