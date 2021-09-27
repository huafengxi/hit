
@LineMatch.regist
def line_match_given(rc, **_kw):
    type = rc.get('type')
    Matching.test(type != None)
    return type

@LineMatch.regist
def line_match_pysuite(head='', **_kw):
    Matching.test(head in 'print raise return import from global pass'.split())
    return 'pysuite'

@LineMatch.regist
def line_match_call_line(cmd='', rc='', args=None, **_kw):
    target = call_find_target(rc['ns'], cmd)
    if not target or target[1] == None: raise NotMatch('can not find target as full line: {}'.format(cmd))
    args.insert(0, target)
    return  'handle_call_line'

@LineMatch.regist
def line_match_call_head(rc=None, head='', cmd=None, args=None, kw=None, **_kw):
    target = call_find_target(rc['ns'], head)
    if not target or target[1] == None: raise NotMatch('can not find target use head: {}'.format(head))
    cmd_list = shlex.split(cmd)
    _args, _kw = parse_cmd_args(cmd_list[1:])
    for i in reversed(_args): args.insert(0, i)
    kw.update((k,v) for k,v in _kw.items() if k not in kw)
    args.insert(0, target)
    return  'handle_call_head'

def is_executable_file(path):
    def is_executable_file_unix(path):
        return subprocess.call('f() { alias $1 || declare -F $1 || which $1; } && f %(path)s >/dev/null 2>&1'%dict(path=path), shell=True, executable='/bin/bash') == 0
    def is_executable_file_win32(path):
        return subprocess.call('where %s'%(path), shell=True) == 0
    return is_executable_file_win32(path) if os.name == 'nt' else is_executable_file_unix(path)

@LineMatch.regist
def line_match_popen(head='', rc=None, **_kw):
    Matching.test_re(head, '^[~_./a-zA-Z0-9-]+$')
    Matching.test(head in 'alias ulimit export set LD_LIBRARY_PATH LD_PRELOAD CC CXX'.split() or is_executable_file(head))
    return 'popen' if rc.get('ctx') != 'void' else 'sh'

