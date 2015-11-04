from abc import ABCMeta, abstractmethod
import re


from indent_io import IndentIO

class ValidationError(Exception): pass

ident_pattern = re.compile(r'^[_a-zA-Z][_a-zA-Z0-9]*$')
keywords = set([
    "and",
    "as",
    "assert",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "exec",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "not",
    "or",
    "pass",
    "print",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
])


def _output(out, *args):
    for item in args:
        if hasattr(item, 'write_to'):
            item.write_to(out)
        elif isinstance(item, basestring):
            out.write(item)
        else:
            _output(out, *item)


def _output_block(out, block):
    if not isinstance(out, IndentIO):
        out = IndentIO(out)
    with out.indent():
        for stmt in block:
            _output(out, stmt, '\n')


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


def _check_rval(value):
    _check_type(value, Expr)
    _check(value.rval, "%r is not an R-value." % value)


def _check_lval(value):
    _check_type(value, Expr)
    _check(value.lval, "%r is not an L-Value." % value)


class Ast(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def write_to(self, out):
        pass

    @abstractmethod
    def check(self):
        pass


class Statement(Ast): pass


class Expr(Ast):

    lval = False
    rval = False


class RValStatement(Statement):

    def __init__(self, value):
        self.value = value

    def check(self):
        _check_rval(self.value)

    def write_to(self, out):
        self.value.write_to(out)


class Const(Expr):

    rval = True

    def __init__(self, value):
        self.value = value

    def write_to(self, out):
        out.write(repr(self.value))

    def check(self):
        _check(type(self.value) in (bool, float, int, str, unicode),
               '%r (type %s) is not a valid Const' %
                   (self.value, str(type(self.value))))


class Call(Expr):

    def __init__(self, callable, args, kwargs, starargs, starstarkwargs):
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.starargs = starargs
        self.starstarkwargs = starstarkwargs

    def write_to(self, out):
        args = _intersperse(', ', self.args)
        kwargs = _intersperse(', ', [[k, '=', v] for (k, v) in self.kwargs])
        result = [args, kwargs]
        if self.starargs is not None:
            result.append(["*", self.starargs])
        if self.starstarkwargs is not None:
            result.append(["**", self.starstarkwargs])
        _output(out, self.callable, '(', _intersperse(', ', result), ')')

    def check(self):
        _check_rval(self.callable)
        for a in self.args:
            _check_rval(a)
        for (k, v) in self.kwargs:
            _check_rval(v)
            _check(re.match(ident_pattern, k),
                   '%r is not a valid identifier.' % k)
        if self.starargs is not None:
            _check_rval(self.starargs)
        if self.starstartkwargs is not None:
            _check_rval(self.starstarkwargs)


def _intersperse(sep, lst):
    if len(lst) != 0:
        yield lst[0]
        for item in lst[1:]:
            yield sep
            yield item


class Assign(Statement):

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def check(self):
        _check_lval(self.lhs)
        _check_rval(self.rhs)

    def write_to(self, out):
        _output(out, self.lhs, ' = ', self.rhs)


class While(Statement):

    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def write_to(self, out):
        _output(out, 'while ', self.condition, ':\n')
        _output_block(out, self.body)

    def check(self):
        _check_rval(self.condition)
        self.condition.check()
        _check_block(self.body)


class For(Statement):

    def __init__(self, lval, seq, body):
        self.lval = lval
        self.seq = seq
        self.body = body

    def write_to(self, out):
        _output(out, 'for ', self.lval, ' in ', self.seq, ':\n')
        _output_block(out, self.body)

    def check(self):
        _check_lval(self.lval)
        _check_rval(self.seq)
        _check_block(self.body)


class Pass(Statement):

    def write_to(self, out):
        out.write('pass')

    def check(self):
        return True


class Var(Expr):

    lval = True
    rval = True

    def __init__(self, name):
        self.name = name

    def check(self):
        _check_type(self.name, str)
        _check(re.match(ident_pattern, self.name),
               "%r is not a valid identifier." % self.name)
        _check(self.name not in keywords,
               "Variable name %r is a keyword." % self.name)

    def write_to(self, out):
        out.write(self.name)


class BinOp(Expr):

    rval = True

    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def write_to(self, out):
        _output(out, '(', self.lhs, ' ', self.op, ' ', self.rhs, ')')

    def check(self):
        _check_rval(self.lhs)
        _check_rval(self.rhs)
        _check_type(self.op, basestring)
