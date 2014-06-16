import io
import re
import ply.lex as lex
import ply.yacc as yacc

# Tap output classes
class Plan:
    """A TAP plan

    Contains the number of planned tests as well
    as a possible diagnostic of the Diagnostic class"""

    number = 0
    diagnostic = None

    def __init__(self, number, diagnostic):
        self.type = 'plan'
        self.number = number
        self.diagnostic = diagnostic

    def __str__(self):
        plan = "1.." + str(self.number)
        if self.diagnostic:
            plan += " # " + str(self.diagnostic)

        return plan

class TestLine:
    """A TAP test line

    Contains the an ok which is either True or False,
    a number which is the test number in the sequence,
    a description and a directive and directive description."""

    ok = True
    number = 0
    description = "A nice little test"
    directive = "TODO"
    directive_description = "Improve niceness"

    def __init__(self, ok, number, description, \
                 directive, directive_description):
        self.type = 'test_line'
        self.ok = ok
        self.number = number
        self.description = description
        self.directive = directive
        self.directive_description = directive_description

    def __str__(self):
        test_line = ("ok" if self.ok else "not ok") + " " + str(self.number)

        if self.description:
            test_line += " " + self.description

        if self.directive:
            test_line += " # " + self.directive

            if self.directive_description:
                test_line += " " + self.directive_description

        return test_line

class Diagnostic:
    """A TAP diagnostic

    Typically a comment from the test case relating progress information."""

    diagnostic = "A comment relating progress"

    def __init__(self, diagnostic):
        self.type = 'diagnostic'
        self.diagnostic = diagnostic

    def __str__(self):
        return "# " + self.diagnostic

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

    planned_number = None
    test_number = 0
    input_stream = None

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
            p[0] = { 'directive' : p[2].upper(), 'description' : p[3] }
        else:
            p[0] = { 'directive' : None, 'description' : None }

    def p_error(self, p):
        print("the output:'" + self.lexer.lexdata + "'")
        raise NotTapError(self.lexer.lexdata.rstrip())

    def __init__(self, input_stream):
        self.input_stream = input_stream
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self)
        self.test_number = 0

    def __iter__(self):
        for line in self.input_stream:
            self.lexer.begin('INITIAL')
            try:
                line = line.decode("utf-8")
            except:
                pass
            yield self.parser.parse(line)

        if self.planned_number and self.test_number < self.planned_number:
            raise PlanError("Number of executed tests (" + str(self.test_number)
                            + ") less than the number of planned (" +
                            str(self.planned_number) + ")")


if __name__ == '__main__':

    def __run_self_test(tap_str):
        f = io.StringIO(tap_str)
        p = Parser(f)
        last_tap = None
        for tap in p:
            last_tap = tap

        return last_tap

    # Test 1
    plan = __run_self_test("1..0 # all of them\n")
    assert plan.number == 0
    assert plan.diagnostic == "all of them"

    ok2 = __run_self_test("1..2\n" \
                            "ok 1\n" \
                            "ok 2\n")
    assert ok2.ok == True
    assert ok2.number == 2
    assert ok2.description == None
    assert ok2.directive == None
    assert ok2.directive_description == None

    not_ok3 = __run_self_test("1..3\n" \
                                "ok 1 Hello\n" \
                                "ok 2 drat\n" \
                                "not ok Sometimes\n")
    assert not_ok3.ok == False
    assert not_ok3.number == 3
    assert not_ok3.description == "Sometimes"
    assert not_ok3.directive == None
    assert not_ok3.directive_description == None

    ok_todo = __run_self_test("ok # ToDo the directive")

    assert ok_todo.ok == True
    assert ok_todo.number == 1
    assert ok_todo.description == None
    assert ok_todo.directive == "TODO"
    assert ok_todo.directive_description == "the directive"

    not_ok_skip = __run_self_test("not ok # skip")

    assert not_ok_skip.ok == False
    assert not_ok_skip.number == 1
    assert not_ok_skip.description == None
    assert not_ok_skip.directive == "SKIP"
    assert not_ok_skip.directive_description == None

    try:
        not_tap = __run_self_test("a wtf")
    except NotTapError:
        pass

    try:
        numbering_error = __run_self_test("ok\n" \
                                            "ok 3\n")
    except NumberingError:
        pass


    try:
        plan_error = __run_self_test("1..1\n" \
                                       "ok\n" \
                                       "not ok\n")
    except PlanError:
        pass

    try:
        bail_out = __run_self_test("Bail out!")
    except BailOutError:
        pass
