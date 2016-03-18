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

import io
import re
import ply.lex as lex
import ply.yacc as yacc
from xml.etree.ElementTree import Element
import unittest


class Tap:
    pass


# Tap output classes
class Plan(Tap):
    """A TAP plan

    Contains the number of planned tests as well
    as a possible diagnostic of the Diagnostic class"""

    def __init__(self, number, diagnostic=None):
        self.number = number
        self.diagnostic = diagnostic

    def __str__(self):
        plan = "1.." + str(self.number)
        if self.diagnostic:
            plan += " # " + str(self.diagnostic)

        return plan

    def __eq__(self, other):
        return (self.number == other.number and
                self.diagnostic == other.diagnostic)

    def junit(self):
        element = Element('system-err')
        return element


class TestLine(Tap):
    """A TAP test line

    Contains the an ok which is either True or False,
    a number which is the test number in the sequence,
    a description and a directive and directive description."""

    def __init__(self, ok, number, description=None,
                 directive=None, directive_description=None):
        self.ok = ok
        self.number = number
        self.description = description
        self.directive = directive
        self.directive_description = directive_description

    def __str__(self):
        test_line = ("ok" if self.ok else "not ok") + " " + str(self.number)

        if self.description:
            test_line += " - " + self.description

        if self.directive:
            test_line += " # " + self.directive

            if self.directive_description:
                test_line += " " + self.directive_description

        return test_line

    def __eq__(self, other):
        return (self.ok == other.ok and
                self.number == other.number and
                self.description == other.description and
                self.directive == other.directive and
                self.directive_description == other.directive_description)

    def junit(self):
        element = Element('testcase')
        element.attrib['name'] = str(self)

        if not self.ok:
            failed = Element('failure')
            element.append(failed)

        return element


class Diagnostic(Tap):
    """A TAP diagnostic

    Typically a comment from the test case relating progress information."""

    def __init__(self, diagnostic):
        self.diagnostic = diagnostic

    def __str__(self):
        return "# " + self.diagnostic

    def junit(self):
        element = Element('system-out')

        return element


# Tap error classes
class NumberingError(Exception):
    """Raised when tests are not executed with the correct ordering"""
    pass


class BailOutError(Exception):
    """Raised when a 'Bail out!' occurs"""

    def __init__(self, description=None):
        self.description = description

    def __str__(self):
        bail_out_line = "Bail out!"
        if self.description:
            bail_out_line += " " + self.description

        return bail_out_line


class NotTapError(Exception):
    """Non-TAP input was encountered"""

    def __init__(self, non_tap):
        self.non_tap = non_tap

    def __str__(self):
        return "Non-TAP input was encountered: \"" + self.non_tap + "\""


class PlanError(Exception):
    """The number of tests did not match the plan"""
    pass


# Tap parser
class Parser:
    """A TAP Parser module

    A TAP - Test Anything Protocol - parser intended for parsing the ouput
    from test cases during execution.

    Parameters
    ----------
    input_stream : Input IO stream from which TAP is to be parsed.
    """

    states = (
        ('description', 'exclusive'),
        ('directive', 'exclusive'),
        ('text', 'exclusive'),
        )

    tokens = (
        'PLAN',
        'OK',
        'NOT',
        'BAIL',
        'OUT',
        'NUMBER',
        'DASH',
        'TEXT',
        'HASH',
        'TODO',
        'SKIP',
        )

    # Initial tokens
    def t_PLAN(self, t):
        r'1..\d+'
        match = re.match('1..(\d+)', t.value)
        t.value = int(match.group(1))
        return t

    def t_OK(self, t):
        r'ok'
        self.lexer.begin('description')
        return t

    t_NOT = r'not'

    def t_HASH(self, t):
        r'\#'
        self.lexer.begin('text')
        return t

    t_BAIL = r'[Bb][Aa][Ii][Ll]'

    def t_OUT(self, t):
        r'[Oo][Uu][Tt]!'
        self.lexer.begin('text')
        return t

    t_ignore = ' \t\r\n'

    def t_error(self, t):
        raise NotTapError(t.lexer.lexdata.strip())

    # Description tokens
    def t_description_NUMBER(self, t):
        r'[ \t]\d+[ \t]*'
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0

        return t

    t_description_DASH = r'-'

    t_description_TEXT = r'[^#^\d^\-][^#^\r^\n]+'

    def t_description_HASH(self, t):
        r'[ \t]*\#'
        self.lexer.begin('directive')
        return t

    t_description_ignore = '\r\n'

    def t_description_error(self, t):
        raise NotTapError(t.lexer.lexdata.strip())

    # Directive tokens
    def t_directive_TODO(self, t):
        r'[Tt][Oo][Dd][Oo]'
        self.lexer.begin('text')
        return t

    def t_directive_SKIP(self, t):
        r'[Ss][Kk][Ii][Pp]'
        self.lexer.begin('text')
        return t

    t_directive_ignore = ' \r\n'

    def t_directive_error(self, t):
        raise NotTapError(t.lexer.lexdata.strip())

    # Text tokens
    t_text_TEXT = "[^\r^\n]+"

    t_text_ignore = '\r\n'

    def t_text_error(self, t):
        print("Illegal character '%s' in state description" % t.value[0])
        t.lexer.skip(1)

    # Grammar
    def p_tap(self, p):
        """tap : plan
               | diagnostic
               | test_line"""
        p[0] = p[1]

    def p_bail_out(self, p):
        """tap : BAIL OUT
               | BAIL OUT TEXT"""
        if len(p) == 3:
            raise BailOutError()
        elif len(p) == 4:
            raise BailOutError(p[3].strip())

    def p_tap_error(self, p):
        """tap : error"""
        raise NotTapError(self.lexer.lexdata.strip())

    def p_plan(self, p):
        """plan : PLAN
                | PLAN diagnostic"""

        if self.planned_number:
            raise NotTapError("Duplicate plan")

        self.planned_number = p[1]

        if self.test_number > self.planned_number:
            raise PlanError("Number of planned tests (" +
                            str(self.planned_number) + ") exceeded")

        if len(p) == 2:
            p[0] = Plan(self.planned_number, None)
        elif len(p) == 3:
            p[0] = Plan(self.planned_number, p[2].diagnostic)

    def p_diagnostic(self, p):
        """diagnostic : HASH TEXT"""
        p[0] = Diagnostic(p[2].strip())

    def p_test_line(self, p):
        """test_line : ok number dash description directive"""
        p[0] = TestLine(p[1], p[2], p[4],
                        p[5]['directive'], p[5]['description'])

    def p_ok(self, p):
        """ok : OK
              | NOT OK"""
        if p[1] == "ok":
            p[0] = True
        elif p[1] == "not":
            p[0] = False

    def p_number(self, p):
        """number : NUMBER
                  | """

        self.test_number = self.test_number + 1

        if self.planned_number and self.test_number > self.planned_number:
                raise PlanError("Number of planned tests (" +
                                str(self.planned_number) + ") exceeded")

        if len(p) > 1:

            if p[1] != self.test_number:
                raise NumberingError("Unexpected test number " + str(p[1]) +
                                     " expecting " + str(self.test_number))
            p[0] = p[1]
        else:
            p[0] = self.test_number

    def p_dash(self, p):
        """dash : DASH
                | """
        pass

    def p_description(self, p):
        """description : TEXT
                       | """
        if len(p) > 1:
            p[0] = p[1].strip()
        else:
            p[0] = None

    def p_directive(self, p):
        """directive : HASH TODO description
                     | HASH SKIP description
                     | """
        if len(p) > 3:
            p[0] = {'directive': p[2].upper(), 'description': p[3]}
        else:
            p[0] = {'directive': None, 'description': None}

    def p_error(self, p):
        if p is None:
            raise NotTapError('<empty-line>')
        else:
            raise NotTapError(p.value)

    def __init__(self):
        self.lexer = lex.lex(module=self, debug=0)
        self.parser = yacc.yacc(module=self, debug=0)

    def __call__(self, input_stream):
        self.input_stream = input_stream
        self.planned_number = None
        self.test_number = 0

        return self

    def __iter__(self):
        for line in self.input_stream:
            self.lexer.begin('INITIAL')
            try:
                line = line.decode("utf-8")
            except:
                pass
            yield self.parser.parse(line, lexer=self.lexer, debug=0)

        if self.planned_number and self.test_number < self.planned_number:
            raise PlanError("Number of executed tests (" +
                            str(self.test_number)
                            + ") less than the number of planned (" +
                            str(self.planned_number) + ")")


class TestParser(unittest.TestCase):

    def run_parser(self, tap_str):
        f = io.StringIO(tap_str)
        p = Parser()
        p(f)
        last_tap = None
        for tap in p:
            last_tap = tap

        return last_tap

    def test_plan(self):
        plan = self.run_parser("1..0 # all of them\n")
        self.assertEqual(plan.number, 0)
        self.assertEqual(plan.diagnostic, "all of them")

    def test_2_ok(self):
        ok2 = self.run_parser("1..2\n"
                              "ok 1\n"
                              "ok 2\n")
        self.assertTrue(ok2.ok)
        self.assertEqual(ok2.number, 2)
        self.assertIsNone(ok2.description)
        self.assertIsNone(ok2.directive)
        self.assertIsNone(ok2.directive_description)

    def test_3_nok(self):
        not_ok3 = self.run_parser("1..3\n"
                                  "ok 1 Hello\n"
                                  "ok 2 drat\n"
                                  "not ok Sometimes\n")
        self.assertFalse(not_ok3.ok)
        self.assertEqual(not_ok3.number, 3)
        self.assertEqual(not_ok3.description, "Sometimes")
        self.assertIsNone(not_ok3.directive)
        self.assertIsNone(not_ok3.directive_description)

    def test_todo(self):
        ok_todo = self.run_parser("ok # ToDo the directive")

        self.assertTrue(ok_todo.ok)
        self.assertEqual(ok_todo.number, 1)
        self.assertIsNone(ok_todo.description)
        self.assertEqual(ok_todo.directive, "TODO")
        self.assertEqual(ok_todo.directive_description, "the directive")

    def test_skip(self):
        not_ok_skip = self.run_parser("not ok # skip")

        self.assertFalse(not_ok_skip.ok)
        self.assertEqual(not_ok_skip.number, 1)
        self.assertIsNone(not_ok_skip.description)
        self.assertEqual(not_ok_skip.directive, "SKIP")
        self.assertIsNone(not_ok_skip.directive_description)

    def test_not_tap(self):
        with self.assertRaises(NotTapError):
            self.run_parser("a wtf")

    def test_numbering_error(self):
        with self.assertRaises(NumberingError):
            self.run_parser("ok\n"
                            "ok 3\n")

    def test_plan_error(self):
        with self.assertRaises(PlanError):
            self.run_parser("1..1\n"
                            "ok\n"
                            "not ok\n")

    def test_bail_out(self):
        with self.assertRaises(BailOutError):
            self.run_parser("Bail out!")

    def test_empty_line(self):
        with self.assertRaises(NotTapError):
            self.run_parser("\n")

if __name__ == '__main__':

    unittest.main()
