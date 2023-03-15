import time
from threading import Thread
import shlex

def dict_merge(d1, d2):
    if type(d1) != dict: return d2
    if type(d2) != dict: return d1
    for k,v in list(d2.items()):
        d1[k] = dict_merge(d1.get(k), v)
    return d1

def list_attr(**kw):
    for key in list(kw.keys()):
        if not key.startswith('_'):
            print(key)

def get_ts_str(ts=None):
    if ts == None: ts = time.time()
    return time.strftime('%m%d-%X', time.localtime(ts))

def check_ssh_connection(ip, timeout):
    try:
        popen('ssh -T %s -o ConnectTimeout=%d true'%(ip, timeout), timeout=timeout)
        return 0
    except Exception as e:
        return -1

def test_arg(_kx, *args, **kw):
    return _kx in args

class StatReport:
    def __init__(self, total_time=60, interval=1.0):
        self.start_time, self.time_limit = 0, time.time() + total_time
        self.last_report, self.interval = 0.0, interval
        self.cost_time, self.count = 0.0, 0.0
    def __enter__(self):
        self.start()
    def __exit__(self, *args):
        print('duration: %4.2fms'%(1000 * (time.time() - self.start_time)))
    def __iter__(self):
        return self
    def __next__(self):
        if time.time() > self.time_limit:
            raise StopIteration()
        self.end()
        self.start()
        return True

    def oneshot(self):
        self.start()
        self.end()

    def start(self):
        self.start_time = time.time()

    def end(self):
        cur = time.time()
        if self.start_time == 0:
            self.last_report = cur
            return
        self.cost_time += cur - self.start_time
        self.count += 1
        if cur > self.last_report + self.interval:
            print("%s qps=%d rt=%4.2fms"%(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cur)), self.count, 1000 * self.cost_time/(self.count + 1)))
            self.cost_time, self.count = 0.0, 0.0
            self.last_report = cur #(_log_=0)

def genconf(tpl_file, target_file, ns):
    tpl_file, target_file = sub(tpl_file, ns), sub(target_file, ns)
    try:
        tpl = open(tpl_file).read()
    except IOError as e:
        raise Fail('read %s fail'%(tpl_file))
    try:
        open(target_file, 'w').write(sub(tpl, ns))
    except IOError as e:
        raise Fail('write %s fail'%(target_file))
    return target_file

@MagicMap.regist
def magic_genconf(ns, cmd, args, kw):
    cmd_list = shlex.split(cmd)
    _args, _kw = parse_cmd_args(cmd_list)
    def get_tpl_name(p): return ':' in p and p.split(':', 1) or (p, p + '.tpl')
    def conf_wrapper(p, env):
        target, tpl = get_tpl_name(p)
        return genconf(tpl, target, ns)
    return [conf_wrapper(p, ns) for p in _args]

@MagicMap.regist
def magic_choose(d, cmd, args, kw):
    seq = re.findall('(\w+):(\S+)', cmd)
    cmd_map = dict(seq)
    cmd_list, result = [], []
    for c in args:
        if c in list(cmd_map.keys()):
            cmd_list.append(c)
    for c in cmd_list:
        args.remove(c)
    if not cmd_list:
        cmd_list = [k for k,v in seq]
    for c in cmd_list:
        result.append((c, CALL(d, cmd_map.get(c), args, kw)))
    return result

@MagicMap.regist
def magic_calc(ns, cmd, args, kw):
    return eval(cmd, globals(), prepare_eval_env(ns))

@MagicMap.regist
def magic_find(d, cmd, args, kw):
    return find(d, cmd)

def first_valid(*args, **kw):
    for p in args:
        v = find(kw, p)
        if v: return v

def load_file_vars(__path__, __globals__=globals()):
    try:
        exec(compile(open(__path__, "rb").read(), __path__, 'exec'), __globals__, locals())
    except Exception as __e:
        raise Fail('load file %s failed!'%(__path__), __e)
    return dict((k, v) for k,v in list(locals().items()) if not k.startswith('__'))

def result2section(d):
    return '\n'.join('<h3>%s</h3><pre>%s</pre>'%(k, v) for k, v in d)

def uniq_filt(s):
    a = set()
    for i in s:
       if i in a: continue
       a.add(i)
       yield i
