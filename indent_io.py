

class IndentIO(object):

    def __init__(self, output,  indent='    ', newline='\n'):
        self.output = output
        self.indent_str = indent
        self.newline = newline
        self.level = 0
        self.on_new_line = True

    def write(self, text):
        lines = text.split(self.newline)
        lines = [[self.indent_str * self.level, line, self.newline]
                 for line in lines]

        lines[-1][-1] = ''
        if not self.on_new_line:
            lines[0][0] = ''

        self.on_new_line = (lines[-1][1] == '')
        if self.on_new_line:
            lines.pop()
        for line in lines:
            for chunk in line:
                self.output.write(chunk)

    def indent(self):
        return self._Block(self)

    class _Block(object):

        def __init__(self, io):
            self.io = io

        def __enter__(self):
            self.io.level += 1

        def __exit__(self, typ, value, traceback):
            self.io.level -= 1

# testing
if __name__ == '__main__':
    import sys
    io = IndentIO(sys.stdout)

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
