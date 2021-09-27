import threading
def wait_process(p, flush=True):
    if not flush: return p.communicate()[0]
    lines = []
    for line in iter(p.stdout.readline, ""):
        print line.rstrip()
        lines.append(line)
    p.stdout.close()
    p.wait()
    return ''.join(lines)

class bg_exec:
    def __init__(self, cmd, env=globals(), flush=False):
        self.cmd = sub(cmd, env)
        try:
            self.p = subprocess.Popen(self.cmd, shell = True, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, executable='/bin/bash')
	    self.out = None
            def bg_run():
                self.out = wait_process(self.p, flush)
            self.bg_thread = threading.Thread(target = bg_run)
            self.bg_thread.start()
        except OSError as e:
            self.p = None
            self.out = '{0}: {1}'.format(str(e), cmd)
    def __del__(self):
        self.kill()
    def __call__(__self, *args, **kw):
        return __self.stop_and_output()
    def __str__(self):
        return 'bg_exec: %s'%(self.cmd)
    def wait(self):
        while self.p.poll() is None:
            time.sleep(0.1)
    def kill(self):
        if self.p and self.p.poll() is None:
            try:
                self.p.kill()
            except Exception as e:
                pass
    def get_output(self):
        while self.out is None:
            time.sleep(0.1)
        return self.out or 'BGProcess Fail: %s'%(self.cmd)
    def stop_and_output(self):
        if not self.p: return 'process not exist: %s'%(self.cmd)
        self.kill()
        return self.get_output()

class Async(Thread):
    def __init__(self, func, *args, **kw):
        self.result = None
        def call_and_set():
            self.result = func(*args, **kw)
        Thread.__init__(self, target=call_and_set)
        self.setDaemon(True)
        self.start()

    def get(self, timeout=None):
        self.join(timeout)
        #return self.isAlive() and self.result
        return self.result

class Proc:
    def __init__(self, func, *args, **kw):
        self.result = None
        rfd, wfd = os.pipe()
        self.pid = os.fork()
        if self.pid > 0:
            os.close(wfd)
            self.rfd = rfd
        else:
            os.close(rfd)
            ret = func(*args, **kw)
            os.write(wfd, str(ret))
            sys.exit(0)
    def get(self, timeout=None):
        ret = os.read(self.rfd, 8192)
        os.close(self.rfd)
        os.waitpid(self.pid, 0)
        return ret

if os.name != 'nt':
    from multiprocessing import Process,Value
    class Pdo:
        def __init__(self, f, args):
            self.plist = [Process(target=f, args=(x,)) for x in args]
            for p in self.plist:
                p.daemon = True
                p.start()
        def wait(self):
            for p in self.plist:
                p.join()

@MagicMap.regist
def magic_bgsh(d, cmd, arg, kw):
    return bg_exec(cmd, dict_updated(d, _rest_=arg), flush=True)

@MagicMap.regist
def magic_bgwait(d, cmd, arg, kw):
    return [(k, v.get_output()[-80:]) for k, v in magic_call(d, cmd, arg, kw)]

async = Async
async_par_limit = 64
@MagicMap.regist
def magic_par(d, cmd, args, kw):
    par_limit = int(find(kw, 'par_limit') or async_par_limit)
    timeout = int(kw.get('par_timeout', '7200'))
    members, cmd = cmd.split(' ', 1)
    members = magic_call(d, members, args, kw)
    task_queue = []
    result = []
    def collect_result():
        rk, rv = task_queue.pop(0)
        result.append(('%s.%s'%(rk, cmd), rv.get(timeout)))
    for k, v in members:
        if k.startswith('_'):
           continue
        if len(task_queue) > par_limit:
            collect_result()
        task_queue.append((k, async(magic_call, v, cmd, args, kw)))
    while task_queue:
        collect_result()
    return result
