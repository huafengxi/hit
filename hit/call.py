def prepare_eval_env(ns):
    d = {}
    for name, env in reversed(ns):
        d.update(env)
    return d

def CALL(ns, p, args, kw):
    log_level = int(kw.get('_tlog_', '1'))
    logger.log(log_level, '%s %s', epath(ns), p)
    ns2, target = call_find_target(ns, p)
    if target == None:
        logger.debug('find none: %s %s: ns=%s', epath(ns), p, epath(ns2))
        return
    logger.trace('find: %s: %s func=%s', epath(ns2), p, repr(target))
    return call_handle_target(ns2, target, args, kw)

def is_magic_str(x): return re.match(r'!\w+(\[.*\])?:', x)
def is_dot_chain(path): return all(re.match(r'[_a-zA-Z]\w*$', x) for x in path.split('.'))
def call_find_target(ns, path):
    if is_magic_str(path): return ns, path
    try: return ns, eval(path, globals(), prepare_eval_env(ns))
    except: pass
    if not is_dot_chain(path): return ns, None
    ns = efind(ns, path)
    return ns[1:], ns_leaf(ns)

import inspect
import types
def prepare_func_kwargs(func, args, ns, kw):
    if isinstance(func, types.BuiltinFunctionType):
        return {}
    spec = inspect.getargspec(func)
    if len(spec.args) < len(args) and not spec.varargs:
        raise Exception("too many args for {}, given arg num: {}".format(spec.args, len(args)))
    new_kw = {}
    for arg in spec.args[len(args):]:
        if type(arg) != str: raise Exception("not support nest args: %s"%(args_names))
        if arg in kw: new_kw[arg] = kw[arg]
    if spec.keywords == None: return new_kw
    new_kw.update(ns_leaf(ns))
    new_kw.update(kw, __rc__=dict(ns=ns, kw=kw))
    for arg in spec.args[:len(args)]:
        if type(arg) != str:
            raise Exception("not support nest args: %s"%(args_names))
        if arg in new_kw:
            del new_kw[arg]
    return new_kw

def call_handle_target(ns, target, args, kw):
    if type(target) == str: target = sub(target, ns_add(ns, '__call_kw_helper', kw))
    if callable(target):
        result = target(*args, **prepare_func_kwargs(target, args, ns, kw))
    elif type(target) == str:
        result = magic_str(ns, target, args, kw)
    else:
        return target
    if type(result) == str: result = sub(result, ns_add(ns, 'call_kw', kw))
    return result

MagicMap = FuncMap()
def magic_str(ns, str, args, kw):
    m = re.match(r'!(\w+)(?:\[(.*)\])?:(.*)', str)
    if not m: return str
    handler_name, handler_args, str_content = m.groups()
    handler = MagicMap.get('magic_' + handler_name, None)
    if not callable(handler): return str
    _args, _kw = parse_cmd_args([_f for _f in sub(handler_args or '', ns).split(',') if _f])
    return handler(ns, str_content.strip(), (_args + list(args)), dict_updated(_kw, kw))

### deps: epath(d) find(ns, path) sub(tpl, ns)
