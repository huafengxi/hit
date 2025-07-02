if sys.version_info[0] < 3:
    import mysubprocess32 as subprocess
else:
    import subprocess
def popen_win32(cmd, input, output, timeout):
    no_tty = sys.stdin == os.devnull
    p = subprocess.Popen(cmd, shell=True, stdin=(input or no_tty) and subprocess.PIPE or None, stdout=(output or no_tty) and subprocess.PIPE or None, stderr=subprocess.STDOUT)
    # p = subprocess.Popen(cmd, shell=True, stdin=input and subprocess.PIPE or None, stdout=output and subprocess.PIPE or None, stderr=subprocess.STDOUT)
    out = p.communicate(input=input)[0]
    ret = p.returncode
    return out, ret

def popen_unix(cmd, input, output, timeout):
    env = dict_updated(os.environ, BASH_ENV=hit_file_path('h/sh.rc'))
    p = subprocess.Popen(cmd, shell=True, stdin=input and subprocess.PIPE or None, stdout=output and subprocess.PIPE or None, stderr=subprocess.STDOUT, env=env, executable='/bin/bash')
    out = p.communicate(input=input, timeout=timeout)[0]
    if type(out) == bytes:
        out = out.decode('utf-8')
    ret = p.returncode
    return out, ret

if os.name == 'nt':
    popen_mos = popen_win32
else:
    popen_mos = popen_unix

def on_popen_error(kw, cmd, e):
    if not kw.get('ignore_shell_error'):
        raise e

def popen(cmd, input=None, output=True, timeout=None, **kw):
    if 'NoException' in cmd: kw['ignore_shell_error'] = True
    if type(input) == str:
        input = input.encode('utf-8')
    if type(timeout) == str:
        timeout = float(timeout)
    logger.trace('cmd=%s, input=%s, output=%s timeout=%s', repr(cmd), repr(input), output, str(timeout))
    try:
        out, ret = popen_mos(cmd, input, output, timeout)
    except Exception as e:
        logger.error('shell fail: %s input=%s %s', cmd, repr(input), traceback.format_exc())
        on_popen_error(kw, cmd, e)
    if ret != 0:
        on_popen_error(kw, cmd, Fail('shell fail: %s input=%s ret=%s'%(cmd, repr(input), ret)))
    if output:
        return out.strip()
    else:
        return ret

def sh(cmd):
    return popen(cmd, output=False, timeout=1)
