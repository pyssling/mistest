import io
import yaml
import os
import case

class SuiteParseException(Exception):
    """Failed to create a suite instance"""
    pass

class SubSuiteException(Exception):
    """Failed to parse an included suite"""
    pass

class Directives:
    """Suite or test case directives"""

    def __init__(self, directives_list):
        pass

class Suite:
    """A test suite parser

    Will read a test suite and generate a corresponding
    object."""

    def __init__(self, file=None, stream=None, name=None):

        self.dependencies = []
        self.directives = []
        self.test_list = []

        if name:
            self.name = name
            self.dir = os.curdir
        elif file:
            self.name = os.path.relpath(file)
            self.dir = os.path.dirname(self.name)
            stream = open(file)

        if stream:
            suite = yaml.safe_load(stream)
        else:
            suite = {}

        if 'Dependencies' in suite:
            self.dependencies = suite['Dependencies']

        if 'Directives' in suite:
            self.directives = suite['Directives']

        if suite:
            if not 'Suite' in suite:
                raise SuiteParseException("No suite declaration in suite")

            for test in suite['Suite']:
                if isinstance(test, dict):
                    test, directives = test.popitem()
                self.append(test)

    def append(self, test):
        if test.endswith('.yaml'):
            try:
                self.test_list.append(Suite(self.dir + "/" + test))
            except Exception as e:
                raise SubSuiteException(str(e))
        else:
            self.test_list.append(case.Case(self.dir + "/" + test))

    def __iter__(self):
        for test in self.test_list:
            if isinstance(test, Suite):
                for suite_test in test:
                    yield suite_test
            else:
                yield test

    def __str__(self):
        return self.name

def looks_like_a_suite(file):
    if file.endswith(".yaml") and os.path.isfile(file):
        return True
    else:
        return False
