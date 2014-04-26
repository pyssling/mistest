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

    # Token names
    tokens = (
        'OK',
        'NOT',
        'NUMBER',
        )

    # Tokens
    #t_PLAN = r'1..\d+'
    t_OK = r'ok'
    t_NOT = r'not'

    def t_NUMBER(self, t):
        r"""\d+"""
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t


    #t_DESCRIPTION = r'[^#]*'
    #t_DIRECTIVE_SEP = r'#'
    #t_TODO = r'TODO'
    #t_SKIP = r'SKIP'

    t_ignore = ' \t\r\n'

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def p_tap(self, p):
        """tap : ok number"""
        print("tap", p[1], p[2])
        p[0] = p[1]

    def p_ok(self, p):
        """ok : OK"""
        print("an ok")
        p[0] = p[1]

    def p_not_ok(self, p):
        """ok : NOT OK"""
        print("An not ok")
        p[0] = p[1]

    def p_number(self, p):
        """number : NUMBER"""
        p[0] = p[1]

    def p_no_number(self, p):
        """number : """
        p[0] = 1

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
            self.parser.parse(line)

if __name__ == '__main__':
    f = io.StringIO("ok 1\nnot ok\n")
    p = Parser(f)
    p.parse()
