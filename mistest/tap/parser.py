import io
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
        ('description','exclusive'),

        )

    tokens = (
        'OK',
        'NOT',
        'NUMBER',
        'TEXT',
        'DIRECTIVE',
        )

    # Initial Tokens
    #t_PLAN = r'1..\d+'
    def t_OK(self, t):
        r'ok'
        self.lexer.begin('description')
        return t

    t_NOT = r'not'

    t_ignore = ' \t\r\n'

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)


    def t_description_NUMBER(self, t):
        r"""\s+\d+\s+"""
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t
    
    t_description_TEXT = r'[^#^\d][^#]+'
    t_description_DIRECTIVE = r'\#'
    t_description_ignore = '\r\n'

    def t_description_error(self, t):
        print("Illegal character '%s' in state description" % t.value[0])
        t.lexer.skip(1)

    #t_DIRECTIVE_SEP = r'#'
    #t_TODO = r'TODO'
    #t_SKIP = r'SKIP'

    def p_tap(self, p):
        """tap : ok number description"""
        print("tap", p[1], p[2], p[3])
        p[0] = p[1]

    def p_ok(self, p):
        """ok : OK"""
        print("an ok")
        p[0] = True

    def p_not_ok(self, p):
        """ok : NOT OK"""
        print("An not ok")
        p[0] = False

    def p_number(self, p):
        """number : NUMBER"""
        p[0] = p[1]

    def p_no_number(self, p):
        """number : """
        self.lexer.begin('description')
        p[0] = 1

    def p_description(self, p):
        """description : TEXT"""
        p[0] = p[1]

    def p_no_description(self, p):
        """description : """
        p[0] = ""

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
            print("parsing:'\n%s'" % line)
            self.lexer.begin('INITIAL')
            self.parser.parse(line)

if __name__ == '__main__':
    f = io.StringIO("ok 1\nnot ok\nok 3 Happy")
    p = Parser(f)
    p.parse()
