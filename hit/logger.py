import sys
import os, os.path
import time, datetime
import inspect

def get_caller(depth=1):
    frame = None
    caller = ''
    try:
        frame, filename, lineno, function, code_ctx, index = inspect.stack()[depth]
        caller = '{}:{} {}:'.format(os.path.basename(filename), lineno, function)
    finally:
        del frame
    return caller

def header(depth):
    return '{} {} '.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), get_caller(depth))

def log_format(msg, args):
    if not args: return msg
    return msg % args

class Logger:
    ERROR = 0
    INFO = 1
    TRACE = 2
    DEBUG = 3
    def __init__(self, level, fd=sys.stdout):
        self.level = level
        self.fd = fd

    def disable_log(self):
        self.fd = None
        self.set_log_level(-1)

    def set_log_file(self, log_file):
        if log_file:
            sys.stdin = os.devnull
            f = open(log_file, 'wb+')
            sys.stdout, sys.stderr = f, f
            logger.fd = f
            os.dup2(f.fileno(), 1)
            os.dup2(f.fileno(), 2)

    def output(self, *msg):
        if self.fd == None: return
        for m in msg:
            self.fd.write(m)
        self.fd.flush()

    def set_log_level(self, level): self.level = level
    def get_log_level(self): return self.level

    def do_log(self, level, msg, args):
        if level <= self.level:
            self.output(header(4), log_format(msg, args), '\n')
    def log(self, level, msg, *args): return self.do_log(level, msg, args)
    def error(self, msg, *args): return self.do_log(Logger.ERROR, msg, args)
    def info(self, msg, *args): return self.do_log(Logger.INFO, msg, args)
    def trace(self, msg, *args): return self.do_log(Logger.TRACE, msg, args)
    def debug(self, msg, *args): return self.do_log(Logger.DEBUG, msg, args)

logger = Logger(1)
if __name__ == '__main__':
    log = Logger(1)
    log.log(Logger.DEBUG, 'this log should not output')
    log.log(Logger.ERROR, 'hello log header %s', 42)
    def f(): log.info("log from func f")
    f()
