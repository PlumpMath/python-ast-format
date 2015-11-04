from indent_io import IndentIO
from cStringIO import StringIO
from pyast import *
import pytest

ast_output_tests = [

(Const(0), "0"),
(Const('Hello'), "'Hello'"),
(Const(True), 'True'),
(Const(4.2), '4.2'),

(Var("x"), "x"),
(Var("_hello"), "_hello"),

(BinOp(Const(4), '+', Const(2)),
    "(4 + 2)"),
(BinOp(BinOp(Const(4), '+', Const(2)), '<', Const(7)),
    "((4 + 2) < 7)"),

(Pass(), "pass"),

(Assign(Var('x'), Const(4)), "x = 4"),

(While(Const(True), [Pass()]),
"""while True:
    pass"""),

(While(BinOp(Const(4), '==', Const(1)),
    [While(Const(False),
        [RValStatement(Const(True)),
         RValStatement(Const(4))])]),
"""while (4 == 1):
    while False:
        True
        4"""),

(For(Var('x'), Const(4), [Pass()]),
"""for x in 4:
    pass"""),

(For(Var('x'), Const(4), [Pass(), RValStatement(Const(False))]),
"""for x in 4:
    pass
    False"""),

]

ast_no_validate_tests = [

        Var(4),
        Var("def"),
        Var("5eep"),
        Var("list?"),

        Const(BinOp(Const(4), '+', Const(2))),

        Const(Pass()),

        Assign(Const(4), Const(5)),

        While(Pass(), Pass()),

        # Need to wrap the statement in RValStatement:
        While(Const(True), [Const(4)]),

        BinOp(Const(4), Const(5), Const(6)),

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


@pytest.mark.parametrize('ast', ast_no_validate_tests)
def test_no_validate(ast):
    with pytest.raises(ValidationError):
        ast.check()


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
