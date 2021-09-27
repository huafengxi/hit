import pprint
class Fail(Exception):
    def __init__(self, msg, obj=None):
        self.msg, self.obj = msg, obj
    def __repr__(self):
        return 'Fail: {} {}'.format(self.msg, self.obj != None and pprint.pformat(self.obj) or '')
    def __str__(self):
        return repr(self)

class MemFileMap:
    def __init__(self):
        self.fmap = {}
    def regist(self, path, content):
        if path not in self.fmap:
            self.fmap[path] = content.split('\n')
    def get_code(self, path, lineno):
        lines = self.fmap.get(path, [])
        if len(lines) >= lineno:
            return lines[lineno - 1]

import inspect
class CallerInfo:
    def __init__(self, depth=1):
        frame = None
        try:
            frame, self.filename, self.lineno, self.function, code_ctx, index = inspect.stack(1)[depth]
            self.env = frame.f_locals
            self.code = code_ctx[0] if code_ctx else None
        finally:
            del frame
    def __repr__(self):
        return 'file={} lineno={} func={} code={}'.format(self.filename, self.lineno, self.function, self.code)

import os
import re, string
import urllib2
import tfile
from logger import logger
class Load:
    def __init__(self, env, parse, base_path, spath=None, **opt):
        self.env, self.parse = env, parse
        self.base_path, self.spath = base_path, spath or []
        self.opt, self.load_list = opt, []
        self.fmap = MemFileMap()
    def get_caller(self, depth=1):
        ci = CallerInfo(depth+1)
        if ci.code == None:
            ci.code = self.fmap.get_code(ci.filename, ci.lineno)
        return ci
    def on_load(self, path, rpath, content):
        logger.debug('%s -> %s', path, rpath)
        self.fmap.regist(rpath, content)
    def __call__(self, plist, quiet=False):
        def on_file_not_find(path):
            if not quiet: raise Fail('file not found: path=%s spath=%s'%(path, self.spath))
            logger.debug('file not found: path=%s spath=%s', path, self.spath)
        def to_list(x): return x.split(',') if type(x) == str else x
        def norm_py(path): return os.path.expanduser(re.sub('^(.*?)([.]py)?$', r'\1.py', path))
        plist = to_list(plist)
        for path in plist:
            if not path: continue
            res = self.read(norm_py(path))
            if not res:
                on_file_not_find(path)
                continue
            rpath, content = res
            self.load_list.append(rpath)
            self.on_load(path, rpath, content)
            exec compile(self.parse(content, **self.opt), rpath, mode='exec') in self.env
    def read(self, path):
        def make_local_reader(dir):
            def read(f):
                p = os.path.expanduser(string.Template(os.path.join(dir, f)).safe_substitute(base=self.base_path))
                if os.path.exists(p): return p, file(p).read()
            return read
        def get_reader(d):
            if type(d) == str or type(d) == unicode:
                return make_local_reader(d)
            else:
                return d
        def try_read(spath, file):
            for d in spath:
                res = get_reader(d)(file)
                if res: return res
        if not path: return
        return try_read(self.spath, path)

    def prepare_local_file(self, f):
        if type(f) == str:
            if os.path.exists(f):
                return f
            elif re.match('http:|https:', f):
                text = urllib2.urlopen(url, timeout=3).read()
            else:
                res = self.read(f)
                if res: text = res[1]
                else: return
        else:
            text = f.read()
        return tfile.write('.cur_ish_%.py', text)
    def dump(self, *path_list):
        for p in path_list:
            rp, content = self.read(p) or ('not-found', '')
            print '### file={} path={} ###'.format(p, rp)
            print content
    def annote(self, text=None, **kw):
        fd = text and file(text) or sys.stdin
        print self.parse(fd.read(), annote=True, **self.opt)
