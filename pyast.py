from abc import ABCMeta, abstractmethod

class ValidationError(Exception): pass

def _output(out, *args):
    for item in args:
        if hasattr(item, 'write_to'):
            item.write_to(out)
        elif isinstance(item, basestring):
            out.write(item)
        else:
            _output(out, *item)


def _check(cond, msg):
    if not cond:
        raise ValidationError(msg)


def _check_type(value, cls):
    _check(isinstance(value, cls),
           'Value %r is not of type %s' % (value, cls.__name__))


def _check_block(value):
    _check(len(value) >= 1,
           'At least one statement is required within a block.')
    for stmt in value:
        _check_type(stmt, Statement)
        stmt.check()


class Ast(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def write_to(self, out):
        pass

    @abstractmethod
    def check(self):
        pass

class Statement(Ast): pass
class Expr(Statement): pass

class Const(Expr):

    def __init__(self, value):
        self.value = value

    def write_to(self, out):
        out.write(repr(self.value))

    def check(self):
        _check(type(self.value) in (bool, float, int, str, unicode),
               '%r (type %s) is not a valid Const' %
                   (self.value, str(type(self.value))))


class While(Statement):

    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def write_to(self, out):
        _output(out, 'while ', self.condition, ':\n')
        with out.indent():
            for stmt in self.body:
                _output(out, stmt, '\n')

    def check(self):
        _check_type(self.condition, Expr)
        self.condition.check()
        _check_block(self.body)

class For(Statement):

    def __init__(self, var, seq, body):
        self.var = var
        self.seq = seq
        self.body = body

    def write_to(self, out):
        _output(out, 'for ', self.var, ' in ', self.seq, ':\n')
        with out.indent():
            for stmt in self.body:
                _output(out, stmt, '\n')

    def check(self):
        # TODO: check `self.var`.
        _check_type(self.seq, Expr)
        _check_block(self.body)


class Pass(Statement):

    def write_to(self, out):
        out.write('pass')

    def check(self):
        return True


class BinOp(Expr):

    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def write_to(self, out):
        _output(out, '(', self.lhs, ' ', self.op, ' ', self.rhs, ')')

    def check(self):
        _check_type(self.lhs, Expr)
        _check_type(self.rhs, Expr)
        _check_type(self.op, basestring)

if __name__ == '__main__':
    from indent_io import IndentIO
    import sys
    out = IndentIO(sys.stdout)

    stmt = While(BinOp(Const(4), '==', Const(1)),
       [While(Const(False),
          [Const(True),
           Const(4)])])
    stmt.check()
    stmt = For('x', Const(4), [Pass()])
    stmt.check()
    stmt.write_to(out)
