#!/usr/bin/env python2
# -*- coding: utf-8-unix -*-
'''
* general
./hit.py __doc__           # show this help
./hit.py load.dump hit.md  # show manual

./hit.py ...  _log_=0      # disable log
./hit.py ...  _log_=3      # enable debug log

./hit.py ... @var=val '@print xx' # exec python stmt before cmd

profile=1 ./hit.py xxx            # profile
pdb=1 ./hit.py xxx                # enter pdb if exception
'''

import sys, os, os.path

def get_pack(): return globals().get('__pack__', None)
_hit_path_ = os.path.realpath('.') if get_pack() else os.path.dirname(os.path.realpath(sys.argv[0]))
def hit_file_path(name=''): return os.path.join(_hit_path_, name)
def setup_sys_path():
    if not get_pack():
        sys.path.insert(0, hit_file_path('hit'))
    for path in '../pylib pylib ../bin .'.split():
        sys.path.insert(0, hit_file_path(path))
    sys.path.insert(0, '.')
setup_sys_path()

from load import Load, Fail
def idf(x, **kw): return x
load = Load(env=globals(), parse=idf, base_path=_hit_path_, spath='.,$base,$base/hit'.split(','))

import re
def parse_cmd_args(args):
    return [i for i in args if not re.match('^\w+=', i)], dict(i.split('=', 1) for i in args if re.match('^\w+=', i))

import pprint
from logger import logger

def myexec(stmt, env=globals()):
     exec(stmt, env)
def hit_run(argv):
    special_opts = ['_dryrun_']
    def get_and_remove(kw, k, v):
        ret = kw.get(k, v)
        if k in kw: del kw[k]
        return ret
    def exec_stmt_in_argv(argv):
        def safe_eval(x):
            try: return eval(x)
            except: return x
        def exec_stmt(x):
            m = re.match('@(\w+)=(.*)', x)
            if m:
                globals()[m.group(1)] = safe_eval(m.group(2))
            else:
                myexec(x[1:])
        new_argv = []
        for x in argv:
            if x.startswith('@'): exec_stmt(x)
            else: new_argv.append(x)
        return new_argv
    def do_print(x): print(x)
    def print_result(x):
        if x == None: pass
        elif type(x) == str: do_print(x)
        else: do_print(pprint.pformat(x))
    args, kw = parse_cmd_args(exec_stmt_in_argv(argv))
    args = [x for x in args if x not in special_opts]
    logger.set_log_level(int(get_and_remove(kw, '_log_', 1)))
    logger.trace('hit_path: %s sys.path: %s load.spath: %s args=%s kw=%s', _hit_path_, sys.path, load.spath, args, kw)
    load('init0.py')
    result = entry(args, kw)
    print_result(result)

logger.set_log_file('d:/hit.log' if 'pythonw' in sys.executable else '')
if '__pack__' in globals(): load.spath.insert(0, __pack__.find_file)
if sys.stdin == os.devnull:
    import tkinter.messagebox
    def alert(title, msg): return tkinter.messagebox.showerror(title, msg)
else:
    def alert(title, msg): print("ERROR: %s: %s"%(title, msg))

def main(): hit_run(sys.argv[1:])
import traceback
try:
    if os.getenv('profile') == '1':
        import cProfile, pstats
        cProfile.run('main()', 'pstat')
        p = pstats.Stats('pstat')
        p.sort_stats('time').print_stats(30)
    else:
        main()
except Fail as e:
    print(e)
    sys.exit(1)
except:
    alert('Exception', traceback.format_exc())
    if os.getenv('pdb') == '1':
        import pdb
        pdb.post_mortem()
