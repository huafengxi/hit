def popen_wrapper(ns, cmd, input=None, output=None, **kw):
    if type(cmd) == str:
        cmd = sub(cmd, ns)
    if type(input) == str:
        input = sub(input, ns)
    if input != None and 'DiscardOutput' in input and logger.get_log_level() < 2:
        cmd += ' >/dev/null 2>/dev/null'
    def format_input(input):
        if not input: return ''
        else: return ' <<<%s'%(input)
    if kw.get('trace_sh'): print('#', cmd)
    return ('_dryrun_' in sys.argv) and '%s%s'%(cmd, format_input(input)) or popen(cmd, input=input, output=output, **kw)

@MagicMap.regist
def magic_print(d, cmd, args, kw):
    print(cmd)

def prepare_popen_ns(ns, args, kw):
    return ns_add(ns, 'popen_kw', dict_updated(kw, _rest_=args))

@MagicMap.regist
def magic_sh(ns, cmd, args, kw):
    is_interactive = getattr(console, 'mode', 'batch') == 'interactive'
    if is_interactive: kw.update(ignore_shell_error=True)
    ret = popen_wrapper(prepare_popen_ns(ns, args, kw), cmd, **kw)
    if not is_interactive: return ret

@MagicMap.regist
def magic_popen(ns, cmd, args, kw):
    return popen_wrapper(prepare_popen_ns(ns, args, kw),  cmd, output=True, **kw)

@MagicMap.regist
def magic_bg(ns, cmd, args, kw):
    def redirect_stdout(filename):
        fd_out = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        os.dup2(fd_out, sys.stdout.fileno())
        os.dup2(fd_out, sys.stderr.fileno())
        if fd_out > 2: # Don't close 0, 1, or 2 if somehow fd_out was one of them
            os.close(fd_out)
    pid = os.fork()
    if pid < 0:
        raise Fail("fork fail")
    if pid > 0:
        return pid
    os.setpgrp()
    name = kw.get('name', 'bg')
    redirect_stdout(f'log/{name}.log')
    magic_call(ns, cmd, args, kw)
    sys.exit(0)

def make_ssh_cmd(ns):
    return 'ssh {} -6 $usr@$ip%$dev' if efind_value(ns, 'ip').startswith('fe80:') else 'ssh {} $usr@$ip'
@MagicMap.regist
def magic_ssh(ns, cmd, args, kw):
    if efind_value(ns, 'is_local'):
        return magic_sh(ns, cmd, args, kw)
    else:
        return magic_sh(ns, make_ssh_cmd(ns).format('-T -q'), args, dict_updated(kw, input=cmd))

@MagicMap.regist
def magic_ssht(ns, cmd, args, kw):
    if efind_value(ns, 'is_local'):
        return magic_sh(ns, cmd, args, kw)
    else:
        return magic_sh(ns, '{} {}'.format(make_ssh_cmd(ns).format('-t'), repr(cmd)), args, dict_updated(kw, input=None))

@MagicMap.regist
def magic_sshp(ns, cmd, args, kw):
    if efind_value(ns, 'is_local'):
        return magic_popen(ns, cmd, args, kw)
    else:
        return magic_popen(ns, '{} {}'.format(make_ssh_cmd(ns).format('-T -q'), repr(cmd)), args, dict_updated(kw, input=None))

@MagicMap.regist
def magic_sql(ns, cmd, args, kw):
    user, passwd = kw.get('sql_user', 'root'), kw.get('sql_passwd', '')
    return magic_sh(ns, '$mysql_cmd -h $ip -P $mysql_port -u$mysql_user $mysql_passwd_param', args, dict_updated(kw, input=cmd, mysql_user=user, mysql_passwd_param= '-p' + passwd if passwd else ''))
