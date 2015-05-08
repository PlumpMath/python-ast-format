from indent_io import IndentIO
from cStringIO import StringIO
from pyast import *
import pytest

output_tests = [

(While(BinOp(Const(4), '==', Const(1)),
    [While(Const(False),
        [Const(True),
         Const(4)])]),
"""while (4 == 1):
    while False:
        True
        4
    
"""),

(For('x', Const(4), [Pass()]),
"""for x in 4:
    pass
"""),

]

@pytest.mark.parametrize('ast,output', output_tests)
def test_output(ast, output):
    ast.check()
    outbuf = StringIO()
    outio = IndentIO(outbuf)
    ast.write_to(outio)
    outbuf.seek(0)
    assert outbuf.read() == output
