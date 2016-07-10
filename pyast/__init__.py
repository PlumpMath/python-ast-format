from abc import ABCMeta, abstractmethod
import re

from .indent_io import IndentIO


class ValidationError(Exception):
    pass


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


def _output_arglist(out, args, kwargs, starargs, starstarkwargs):
    kwargs = [[k, '=', v] for (k, v) in kwargs]
    result = list(args) + list(kwargs)
    if starargs is not None:
        result.append(["*", starargs])
    if starstarkwargs is not None:
        result.append(["**", starstarkwargs])
    _output(out, '(', _intersperse(', ', result), ')')


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
    _check(
        isinstance(value, cls),
        'Value %r is not of type %s' % (value, cls.__name__))


def _check_block(value):
    _check(
        len(value) >= 1, 'At least one statement is required within a block.')
    for stmt in value:
        _check_type(stmt, Statement)
        stmt.check()


def _check_rval(value):
    _check_type(value, Expr)
    _check(value.rval, "%r is not an R-value." % value)


def _check_lval(value):
    _check_type(value, Expr)
    _check(value.lval, "%r is not an L-Value." % value)


def _check_id(name):
    _check(
        re.match(ident_pattern, name), '%r is not a valid identifier.' % name)
    _check(name not in keywords, '%r is keyword.')


class Ast(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def write_to(self, out):
        pass  # pragma: no cover

    @abstractmethod
    def check(self):
        pass  # pragma: no cover


class Statement(Ast):
    pass


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


class Def(Statement):
    def __init__(self,
                 name,
                 args=(),
                 default_args=(),
                 star=None,
                 starstar=None,
                 body=()):
        self.name = name
        self.args = args
        self.default_args = default_args
        self.star = star
        self.starstar = starstar
        self.body = body

    def check(self):
        _check_id(self.name)
        ids = set()
        for k in self.args:
            _check_id(k)
            _check(k not in ids, "Duplicate argument: %r" % k)
            ids.add(k)
        for k, v in self.default_args:
            _check_id(k)
            _check(k not in ids, "Duplicate argument: %r" % k)
            ids.add(k)
            _check_rval(v)
        for k in self.star, self.starstar:
            if k is None:
                continue
            _check_id(k)
            _check(k not in ids, "Duplicate argument: %r" % k)
            ids.add(k)
        _check_block(self.body)

    def write_to(self, out):
        _output(out, "def ", self.name)
        _output_arglist(out, self.args, self.default_args, self.star,
                        self.starstar)
        _output(out, ':\n')
        _output_block(out, self.body)


class Const(Expr):

    rval = True

    def __init__(self, value):
        self.value = value

    def write_to(self, out):
        out.write(repr(self.value))

    def check(self):
        _check(
            type(self.value) in (bool, float, int, str, unicode),
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
        _output(out, self.callable)
        _output_arglist(out, self.args, self.kwargs, self.starargs,
                        self.starstarkwargs)

    def check(self):
        _check_rval(self.callable)
        for a in self.args:
            _check_rval(a)
        for (k, v) in self.kwargs:
            _check_rval(v)
            _check_id(k)
        if self.starargs is not None:
            _check_rval(self.starargs)
        if self.starstarkwargs is not None:
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


class Class(Statement):
    def __init__(self, name, bases, body):
        self.name = name
        self.bases = bases
        self.body = body

    def write_to(self, out):
        _output(out, 'class ', self.name, '(')
        _output(out, _intersperse(', ', self.bases))
        _output(out, '):\n')
        _output_block(out, self.body)

    def check(self):
        Var(self.name).check()
        for b in self.bases:
            _check_rval(b)
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
        _check(
            re.match(ident_pattern, self.name),
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
