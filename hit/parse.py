#!/usr/bin/env python2
'''
cat a.txt | ./parse.py
'''
import sys
import os
import re

import parser
def is_pystmt(text):
    try:
        return parser.suite(text)
    except SyntaxError as e:
        return None

def parse_regexp(text, regexp):
    m = re.match(regexp, text, re.S|re.M)
    return m and m.group(0) or ''

def parse_pystmt(text, regexp, py_tpl):
    c = parse_regexp(text, regexp)
    def antiquotes_escape(c): return re.sub('`([^`]+)`', 'xxx', c)
    return is_pystmt(py_tpl % (antiquotes_escape(c.strip()))) and c or ''

def get_attr(cmd, code):
    def remove_commet(code):
        return re.sub('(#.*$)?', '', code)
    def parse_attr(code):
        attr = {}
        m = re.match('.*\#\((.*)\)$', code)
        if m:
            try:
                attr = eval('dict(%s)'%(m.group(1)))
            except Exception:
                pass
        return attr
    def guess_ctx(cmd, code):
        return 'void' if cmd == remove_commet(code).strip() else 'inline'
    attr = parse_attr(code)
    attr.update(ctx=guess_ctx(cmd, code))
    return attr

def escape(text, wrap_tpl, comment_char='#'):
    def do_escape(line): return line and wrap_tpl % (line)
    if not comment_char:
        return re.sub('(?s)^( *)(.*?)$', lambda m: m.group(1) + do_escape(m.group(2)), text)
    else:
        return re.sub('(?s)^( *)(.*?)((?: *{}.*)|(?:\s+)?)$'.format(comment_char), lambda m: m.group(1) + do_escape(m.group(2)) + m.group(3), text)
class PyMixFormater:
    def __init__(self, wrap_tpl, comment_char='#'):
        self.wrap_tpl, self.comment_char = wrap_tpl, comment_char
        self.output = []
    def handle(self, t, c, p):
        def escape_line(line):
            return escape(line, self.wrap_tpl, self.comment_char)
        def escape_antiquotes(line):
            return re.sub('`([^`]+)`', lambda m: escape(m.group(1), self.wrap_tpl, comment_char=None), line)
        if t in 'pe':
            self.out(escape_antiquotes(c.rstrip()), p)
        else:
            self.out(escape_line(c.rstrip()), p)
    def out(self, c, p):
        self.output.append((c, p))
    def format(self, annote):
        def format_line((c, p)): return ('{}#{}'.format(c, p) if annote else c) + '\n'
        return ''.join(map(format_line, self.output))

class PyMixParser:
    def __init__(self, wrap_tpl, comment_char='#'):
        self.plist = []
        self.wrap_tpl, self.comment_char = wrap_tpl, comment_char
    def regist(self, t):
        def add_to_plist(f):
            self.plist.append((t,f))
            return f
        return add_to_plist
    def parse_chunk(self, text):
        for type, parser in self.plist:
            chunk = parser(self, text)
            if chunk: return type, chunk, parser
    def parse_text(self, text):
        def trunc_space(text):
            return re.sub('(?m)[ \t]+$', '', text)
        def add_newline(text):
            return text.endswith('\n') and text or text + '\n'
        text = trunc_space(add_newline(text))
        while text:
            type, chunk, parser = self.parse_chunk(text)
            yield type, chunk, parser
            text = text[len(chunk):]
    def parse(self, text, annote=False):
        if '# *raw-python*' in text:
            return text
        o = PyMixFormater(self.wrap_tpl, self.comment_char)
        for t, c, p in self.parse_text(text):
            o.handle(t, c, p.func_name)
        return o.format(annote)
    def __call__(self, text, **kw):
        return self.parse(text, **kw)

pymix_parse = PyMixParser('Interp("""%s """)')
@pymix_parse.regist('e')
def empty_l(self, text):
    return parse_regexp(text, '\n')
@pymix_parse.regist('n')
def c_comm(self, text):
    return parse_regexp(text, ' */[*].*?[*]/.*?\n')
@pymix_parse.regist('n')
def cpp_comm(self, text):
    return parse_regexp(text, ' *//[^\n].*?\n')
@pymix_parse.regist('x')
def sharp_m(self, text):
    return parse_regexp(text, ' *#([^\n]+\\\\\n)+[^\n].*?\n')
@pymix_parse.regist('n')
def sharp_l(self, text):
    return parse_regexp(text, ' *#[^\n]+\n')
@pymix_parse.regist('n')
def c_stmt(self, text):
    return parse_regexp(text, '^[^\n]*?;\n')
@pymix_parse.regist('p')
def try_stmt(self, text):
    return parse_regexp(text, '''^[ ]*try:\n|^[ ]*except.*?:\n|^[ ]*finally:\n''')
@pymix_parse.regist('p')
def pyelse(self, text):
    return parse_pystmt(text, '^[ ]*else:\n|elif*?:\n', 'if 1: pass\n%s pass')
@pymix_parse.regist('p')
def pyctrl(self, text):
    return parse_pystmt(text, '^[^\n]*?:\n', '%s pass')
@pymix_parse.regist('p')
def pyannot(self, text):
    return parse_pystmt(text, '^[ ]*@.*?\n', '%s\ndef f(): pass')
@pymix_parse.regist('n')
def icmd_st(self, text):
    if re.match('^ *return', text): return ''
    return parse_regexp(text, r'^[_a-zA-Z0-9,.[\]]+( #.*?)?\n')
@pymix_parse.regist('n')
def sh_stmt(self, text):
    if re.match('^ *return', text): return ''
    return parse_regexp(text, ''' *[./_a-zA-Z0-9|-]+( #.*?)?\n''')
@pymix_parse.regist('n')
def sh_opt(self, text):
    return parse_regexp(text, r''' *[./_a-zA-Z0-9]+ -[-a-zA-Z0-9][^\n]*?\n''')
@pymix_parse.regist('p')
def pynormal(self, text):
    return parse_pystmt(text, '^.*?\n', '%s')
@pymix_parse.regist('c')
def literal(self, text):
    return parse_regexp(text, '^.*?\n')

def help():
    print __doc__

if __name__ == '__main__':
    not sys.stdin.isatty() or help() or sys.exit(1)
    text = sys.stdin.read()
    pymix_parse.comment_char = os.getenv('comment_char', '#')
    out = pymix_parse.parse(text, annote=True)
    print out
    parser.suite(out)
