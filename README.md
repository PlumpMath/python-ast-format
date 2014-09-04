This is the beginnings of a python library for constructing abstract
syntax trees for python source, and outputting the corresponding textual
source code. It's possible to use the standard library's `ast` module to
generate python code dynamically, but it's also possible to segfault
python; the module is really meant to be an implementation detail.

This is very incomplete, and I make no promises to finish it - I'm
publishing it so I don't lose it. There is a module that deals with the
indentation issues fairly nicely that is itself already usable.
