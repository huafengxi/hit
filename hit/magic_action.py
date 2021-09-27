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
    return ('_dryrun_' in sys.argv) and '%s%s'%(cmd, format_input(input)) or popen(cmd, input=input, output=output, **kw)

@MagicMap.regist
def magic_print(d, cmd, args, kw):
    print cmd

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
