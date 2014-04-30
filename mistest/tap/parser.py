import io
import re
import ply.lex as lex
import ply.yacc as yacc

class Parser:
    """A TAP Parser module

    A TAP - Test Anything Protocol - parser intended for parsing the ouput
    from test cases during execution.

    Parameters
    ----------
    input_stream : Input IO stream from which TAP shall be parsed.
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
        'NUMBER',
        'TEXT',
        'HASH',
        'TODO',
        'SKIP',
        )

    # Initial Tokens
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

    t_ignore = ' \t\r\n'

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Description Tokens
    def t_description_NUMBER(self, t):
        r'\s+\d+\s+'
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t
    
    t_description_TEXT = r'[^#^\d][^#]+'

    def t_description_HASH(self, t):
        r'\#'
        self.lexer.begin('directive')
        return t

    t_description_ignore = '\r\n'

    def t_description_error(self, t):
        print("Illegal character '%s' in state description" % t.value[0])
        t.lexer.skip(1)

    # Directive Tokens
    def t_directive_TODO(self, t):
        r'\s*[Tt][Oo][Dd][Oo]\s*'
        self.lexer.begin('text')
        return t

    def t_directive_SKIP(self, t):
        r'\s*[Ss][Kk][Ii][Pp]\s*'
        self.lexer.begin('text')
        return t

    t_directive_ignore = '\r\n'

    def t_directive_error(self, t):
        print("Illegal character '%s' in state description" % t.value[0])
        t.lexer.skip(1)

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
               | test_line
               | """

    def p_plan(self, p):
        """plan : PLAN"""
        print("plan", p[1])

    def p_plan_diagnostic(self, p):
        """plan : PLAN diagnostic"""

    def p_diagnostic(self, p):
        """diagnostic : HASH TEXT"""

    def p_test_line(self, p):
        """test_line : ok number description directive"""
        print("tap", p[1], p[2], p[3])
        p[0] = { 'ok' : p[1],
                 'number' : p[2],
                 'description' : p[3],
                 'directive' : p[4]['directive'],
                 'directive_description' : p[4]['description'],
                 }

    def p_ok(self, p):
        """ok : OK"""
        p[0] = True

    def p_not_ok(self, p):
        """ok : NOT OK"""
        p[0] = False

    def p_number(self, p):
        """number : NUMBER"""
        p[0] = p[1]

    def p_no_number(self, p):
        """number : """
        p[0] = 1

    def p_description(self, p):
        """description : TEXT"""
        p[0] = p[1]

    def p_no_description(self, p):
        """description : """
        p[0] = ""

    def p_directive(self, p):
        """directive : HASH TODO description
                     | HASH SKIP description"""
        p[0] = { 'directive' : p[2], 'description' : p[3] }

    def p_no_directive(self, p):
        """directive : """
        p[0] = { 'directive' : None, 'description' : '' }

    def p_error(self, p):
        print("Syntax error")
    
    def __init__(self, input_stream):
        self.input_stream = input_stream
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self)

    def parse(self):
        self.plan = None
        self.ok = 0
        self.not_ok = 0

        for line in f:
            self.lexer.begin('INITIAL')
            self.parser.parse(line)

if __name__ == '__main__':
    str = "1..4\n" \
        "ok 1\n \n" \
        "not ok\n" \
        "ok 3 Happy # TODO\n" \
        "# Well, this far, so good!"
    print("to parse:\n--------\n")
    print(str)
    print("-------\n")
    f = io.StringIO(str)
    p = Parser(f)
    p.parse()
