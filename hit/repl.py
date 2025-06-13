import os
import re
import sys
if not sys.stdout.isatty():
    os.environ['TERM'] = ''
try:
  import readline
except ImportError:
  import pyreadline as readline
  def do_nothing(*args, **kw): pass
  readline.redisplay = do_nothing
import atexit
import traceback
import pprint
import subprocess
import copy
import tfile

import ast
def parse_expr(expr):
    try: return ast.parse(expr, mode='eval')
    except: pass

class BaseInterp:
    def __init__(self, globals, locals):
        self.prefix, self.prefix2 = None, None
        self.match_list = None
        self.globals, self.locals = globals, locals

    def get_prompt(self):
        def get_cwd():
            home = os.path.realpath(os.path.expanduser('~'))
            cwd = os.getcwd()
            if cwd == home:
                ret = '~'
            elif cwd.startswith(home):
                ret = os.path.join('~', cwd[len(home) + 1:])
            else:
                ret = cwd
            return ret
        return '%s $ '%(get_cwd())

    def prepare_env(self):
        return self.locals, self.globals

    def preprocess(self, line):
        return line

    def interp(self, line):
        locals, globals = self.prepare_env()
        cmd = self.preprocess(line.strip())
        ret = None
        try:
            tpath = tfile.write('.cur_cmd_%', line.strip())
            if parse_expr(cmd):
                code = compile(cmd, tpath, 'eval')
                ret = eval(code, globals, locals)
            else:
                code = compile(cmd, tpath, 'exec')
                exec(code, globals, locals)
                ret = None
        except Exception as e:
            print(e, traceback.format_exc())
        return ret

    def on_exception(self, line, e):
        print('Console Exception: %s'%(e))
        print(traceback.format_exc())

    def pprint(self, line, ret):
        if type(ret) == str:
            print(ret)
        elif ret == None:
            pass
        else:
            pprint.pprint(ret)

    def safe_get_matched(self, prefix, full_prefix):
        try:
            return self.get_matched(prefix, full_prefix)
        except:
            print(traceback.format_exc())
        return []

    def complete(self, prefix, index):
        prefix2 = readline.get_line_buffer()[:readline.get_begidx()]
        if (prefix, prefix2) != (self.prefix, self.prefix2):
            self.match_list = [match for match in sorted(set(self.safe_get_matched(prefix, prefix2))) if match.startswith(prefix)]
            self.prefix, self.prefix2 = prefix, prefix2
        if index >= len(self.match_list):
            return None
        else:
            return self.match_list[index]

class Console:
    def __init__(self, histfile):
        self.histfile = histfile
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        atexit.register(readline.write_history_file, histfile)
        readline.set_pre_input_hook(self.enter_indent)
        self.indent = ''

    def enter_indent(self):
        readline.insert_text(self.indent)
        # readline.redisplay()
    def read_lines(self, prompt):
        lines = []
        self.indent = ''
        line = input(prompt)
        lines.append(line)
        if not line.endswith(':'):
            return lines
        self.indent = '    '
        while True:
            line = input(('.' * (len(prompt) - 1)) + ' ')
            if not line.strip():
                break
            self.indent = re.match(' *', line).group(0)
            lines.append(line)
        return lines
    def on_reload(self):
        readline.write_history_file(self.histfile)
    def repl(self, interp):
        readline.set_completer_delims(' \t\n`!@#$^&*()=+[{]}\\|;:\'",<>?')
        readline.set_completer(interp.complete)
        readline.parse_and_bind("tab: complete")
        while True:
            try:
                lines = self.read_lines(interp.get_prompt())
            except EOFError:
                print('exit')
                return 'done'
            except KeyboardInterrupt:
                print('\n receive C-c, reload console, use ctrl-D to exit')
                self.on_reload()
                lines = ['reload_console']
            lines = '\n'.join(lines).strip()
            try:
                result = interp.interp(lines)
            except KeyboardInterrupt as e:
                result = None
            except Exception as e:
                interp.on_exception(lines, e)
                result = None
            interp.pprint(lines, result)

class Completer:
    def __init__(self, kw_list, locals, globals):
        self.kw_list = kw_list
        self.locals, self.globals = locals, globals
    def get_matched(self, prefix, prefix2):
        return self.get_file_path(prefix) + self.get_instance_attr(prefix) + self.get_keyword_list() + self.get_shell_completion(prefix2)
    def get_shell_completion(self, prefix2):
        def dict_updated(d, **kw):
            new_dict = copy.copy(d)
            new_dict.update(**kw)
            return new_dict
        if prefix2:
            return []
        p = subprocess.Popen('compgen -A function -abck 2>/dev/null || true', stdout=subprocess.PIPE, shell=True, executable='/bin/bash')
        stdout = p.communicate(None)[0]
        return [line.strip() for line in stdout.split('\n')]
    def get_file_path(self, prefix):
        dirname = os.path.dirname(prefix)
        try:
            file_list = os.listdir(os.path.expanduser(dirname) or '.')
        except IOError as e:
            file_list = []
        file_list = [os.path.join(dirname, f) for f in file_list]
        return [os.path.isdir(os.path.expanduser(f)) and '%s/'%(f) or f for f in file_list]
    def get_keyword_list(self):
        return self.kw_list
    def get_instance_attr(self, prefix):
        def split_path(path):
            p = path.rsplit('.', 1)
            return len(p) > 1 and p or [''] + p
        def get_instance(path):
            try:
                return eval(path, self.globals, self.locals)
            except Exception as e:
                pass
        if not re.match('^[.a-zA-Z0-9]*$', prefix):
            return []
        dir_path = split_path(prefix)[0]
        if dir_path:
            base = get_instance(dir_path)
            keys = dir(base)
        else:
            keys = dir(self.locals) + dir(self.globals)
        return ['%s%s'%(dir_path and '%s.'%(dir_path) or '', k) for k in keys if not k.startswith('_')]

if __name__ == '__main__':
    class TestInterp(BaseInterp):
        def __init__(self):
            BaseInterp.__init__(self, globals(), globals())
        def get_matched(self, prefix, prefix2):
            completer = Completer('admin root apple'.split(), locals(), globals())
            return completer.get_matched(prefix, prefix2)
    console = Console('.histfile')
    console.repl(TestInterp())
