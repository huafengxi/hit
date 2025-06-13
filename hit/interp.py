import parse
def prepare_rctx(cmd):
    ci = load.get_caller(3)
    ns = [('top', globals())]
    if id(ci.env) != id(globals()):
        ns.insert(0, ('local', ci.env))
    run_ctx = dict(parse.get_attr(cmd, ci.code), ns=ns, code=ci.code, caller="{}:{}".format(os.path.basename(ci.filename), ci.lineno))
    return run_ctx

LineMatch = MatchList()
def Interp(cmd):
    cmd = cmd.strip()
    rc = prepare_rctx(cmd)
    return INTERP(rc, cmd, [], {})

def INTERP(rc, cmd, args, kw):
    def get_head(cmd): return re.match('[^ ;]*', cmd).group(0)
    cmd = sub(cmd, rc['ns']).strip()
    if re.match(r'^\s*$', cmd) or re.match(r'^\s*#', cmd): return cmd
    func = LineMatch.match(dict(kw=kw, args=args, cmd=cmd, head=get_head(cmd), rc=rc))
    logger.trace('cmd=%s caller=%s code=%s ctx=%s func=%s', repr(cmd), rc['caller'], repr(rc['code']), rc.get('ctx'), func)
    return MagicMap.get('magic_' + func)(rc['ns'], cmd, args, kw)

def interp(*args, **kw):
    if not args: return None
    cmd, args = args[0].strip(), list(args[1:])
    rc = kw['__rc__']
    rc.update(code="Interp('''{}''')".format(cmd), caller="<cmd>")
    return INTERP(rc, cmd, args, rc['kw'])
