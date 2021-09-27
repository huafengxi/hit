import threading

import os, fcntl
class FileLock:
    def __init__(self, path, msg):
        self.path, self.fd = path, -1
        logger.info("file_lock: %s", path)
        self.close = os.close
        self.lock(msg)
        logger.info("file_lock succ: %s %s", path, msg)
    def __del__(self):
        self.unlock()
    def lock(self, msg):
        self.fd = os.open(self.path, os.O_RDWR|os.O_CREAT)
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        os.write(self.fd, msg)
    def unlock(self):
        if self.fd >= 0:
             self.close(self.fd)
             self.fd = -1

def get_tag(content, tag): return '\n'.join(re.findall('^#%s: (.+)$'%(tag,), content, re.M))
def upload(content):
    ret = popen('i oss.sh put /tmp/%s'%(get_tag(content, 'name')), input=content)
    return get_tag(content, 'summary')
def ding(msg):
    logger.info('ding: %s', msg)
    return popen('i ding.py', input=msg)
def gen_report(path, __env=globals(), **kw):
    tpl = get_pack() and __pack__.read(path) or file(path).read()
    pub_url = popen('echo $PUB_URL')
    new_env = dict_updated(__env, kw, PUB_URL=pub_url)
    return sub(tpl, new_env)
def report_upload(path, __env=globals(), **kw): return upload(gen_report(path, __env, **kw))

class ThreadRun(threading.Thread):
    def __init__(self, __f, *args, **kw):
        def thread_func():
            try:
               self.result = __f(*args, **kw)
            except Exception as e:
               self.result = e
        threading.Thread.__init__(self, target=thread_func)
        self.result = None
        self.setDaemon(True)
        self.start()
    def wait(self, timeout):
        self.join(timeout)
        if self.isAlive(): return 'execute cost too much time, timeout=%d'%(timeout)
        return self.result

class FlowLogger:
    ERROR = 0
    INFO = 1
    TRACE = 2
    DEBUG = 3
    def __init__(self, level):
        self.level = level
        self.logger = logger
        self.summary = []
    def ding(self, msg):
        self.logger.info('ding: %s', msg)
        return popen('i ding.py', input=msg)
    def flush(self):
        self.ding('\n'.join(self.summary))
        self.summary = []
    def log(self, level, msg):
        if level <= self.level:
            self.logger.info(msg)
            ding(msg)
        if level <= FlowLogger.TRACE:
            self.summary.append(msg)
    def debug(self, msg):
        return self.log(FlowLogger.DEBUG, msg)
    def info(self, msg):
        return self.log(FlowLogger.INFO, msg)
    def error(self, msg):
        return self.log(FlowLogger.ERROR, msg)

class Flow(FlowLogger):
    def __init__(self, timeout=None, ding_level=FlowLogger.ERROR):
        self.file_lock, self.timeout = None, timeout
        self.setup_hook, self.teardown_hook = [], []
        self.cl = []
        FlowLogger.__init__(self, ding_level)
    def do_setup(self):
        for h in self.setup_hook:
           self.execute(globals(), h)
    def do_teardown(self):
        for h in self.teardown_hook:
           self.execute(globals(), h)
        self.flush()
    def prepare(self):
        self.info('flow setup: %s'%(time.strftime('%Y-%m-%d %H:%M:%S')))
        self.file_lock = FileLock('pidlock', str(os.getpid()))
        TearDown.regist(self.do_teardown)
    #def __del__(self): self.flush()
    def filt(self, cmd):
        idx_str = '0123456789abcdefghijklmnopqrst'
        cf = globals().get('cf', '')
        if not cf: return True
        self.cl.append(cmd)
        idx = idx_str[len(self.cl)-1]
        logger.debug('cf=%s idx=%s', cf, idx)
        if cf == '-':
            print '%s: %s'%(idx, cmd)
        return ('-%s'%(idx) not in cf) and (idx in cf or '.' in cf)
    def run_with_filt(self, env, cmd):
        if not self.filt(cmd): return 'skip %s'%(cmd)
        self.execute(env, cmd)
    def execute(self, env, cmd):
        if self.file_lock == None:
            self.prepare()
            self.do_setup()
        self.debug('flow case begin: %s'%(cmd))
        ret = self.do_execute(env, cmd)
        self.debug('flow case end: %s -> %s'%(cmd, ret))
        ret = '%s: %s'%(cmd, ret)
        if 'ERROR' in ret:
            self.error(ret)
        else:
            self.info(ret)
        return ret
    def do_execute(self, env, cmd):
        def safe_ish(env, cmd):
            try:
                return Interp(cmd, locals=env)
            except Exception as e:
                self.logger.debug(traceback.format_exc())
                return 'ERROR: %s fail: %s'%(cmd, e)
        start_ts = time.time()
        ret = ThreadRun(safe_ish, env, cmd).wait(self.timeout)
        if ret == None:
            ret = 'ERROR: execute fail, result is None'
        used_time = int(time.time() - start_ts)
        if type(ret) != str: ret = 'done'
        return '%s%s'%(used_time > 10 and 'use %ds, '%(used_time,) or '', ret)

@MagicMap.regist
def magic_case(d, cmd, args, kw):
    flow = find(d, "cur_flow")
    if not flow: raise Fail("cur_flow not defined")
    return flow.run_with_filt(d, cmd)
cur_flow = Flow()
