from parse import pymix_parse
@AfterLoad.regist
def after_load_change_parser():
    load.parse = pymix_parse

def ish(*args, **kw):
    rc = kw.get('__rc__') or {}
    return ISH(rc.get('ns', [('top', globals())]), list(args), rc.get('kw', kw))

def ISH(ns, args, kw):
    if not args: return
    leaf = ns_leaf(ns)
    hook = leaf.get('prepare_for_ish', None)
    if callable(hook): hook(ns)
    load_list = []
    for x in args:
        if not x.endswith('.py'): break
        f = load.prepare_local_file(x)
        if not f: raise Fail('file not found: {}'.format(x))
        load(f)
        load_list.append(x)
    args = args[len(load_list):]
    if not args: return load_list
    return CALL(ns, args[0], args[1:], kw)
