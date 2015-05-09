from indent_io import IndentIO
from cStringIO import StringIO
from pyast import *
import pytest

ast_output_tests = [

(While(BinOp(Const(4), '==', Const(1)),
    [While(Const(False),
        [Const(True),
         Const(4)])]),
"""while (4 == 1):
    while False:
        True
        4"""),

(For('x', Const(4), [Pass()]),
"""for x in 4:
    pass"""),

]

@pytest.mark.parametrize('ast,output', ast_output_tests)
def test_output(ast, output):
    ast.check()
    outbuf = StringIO()
    outio = IndentIO(outbuf)
    ast.write_to(outio)
    outbuf.seek(0)
    # We strip whitespace off of the actual output here; Otherwise we will often
    # get trailing whitespace on an empty line, which is weird to look at here
    # given that it matters semantically for the tests, and it doesn't affect
    # the python semantics, so we don't care.
    assert outbuf.read().strip() == output


def test_indent_io():
    outbuf = StringIO()
    io = IndentIO(outbuf)

    io.write('%d\n' % io.level)
    with io.indent():
        io.write('%d\n' % io.level)
        with io.indent():
            io.write('%d-' % io.level)
            io.write('%d\n' % io.level)
            with io.indent():
                io.write('%d\n' % io.level)
            io.write('%d\n' % io.level)
        io.write('%d\n' % io.level)
    io.write('%d\n' % io.level)

    outbuf.seek(0)
    assert outbuf.read() ==\
"""0
    1
        2-2
            3
        2
    1
0
"""
