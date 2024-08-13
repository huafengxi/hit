import itertools
import copy

def efind_base(ns, k):
    for name, env in ns:
        if k in env: return env

class NDVKey:
    def getv(ns): pass
class NDHook:
    def onload(ns): pass
def efind(ns, path):
    ns = copy.copy(ns)
    '''example input: ns=[(top, global()] path='a.b.c' '''
    if not path: return ns, None
    def search_key(ns, k):
        env = efind_base(ns, k)
        return env[k] if env != None else None
    for key in filter(None, path.split('.')):
        d = search_key(ns, key)
        if isinstance(d, NDVKey):
            d = d.getv(ns)
        ns.insert(0, (key, d))
        if type(d) != dict:
            break
    return ns

def efind_value(ns, path):
    return ns_leaf(efind(ns, path))

def epath(ns): return '.'.join(reversed([name for name, env in ns]))
def ns_leaf(ns): return ns[0][1]
def ns_add(ns, k, v): return [(k,v)] + ns
def ns_leaf_key(ns): return ns[0][0]

def _call_hook(global_dict):
    ns, cur_dict_set = [], set()
    def handle_dict(ns):
        k, d = ns[0]
        if type(d) != dict: return
        if id(d) in cur_dict_set: return
        cur_dict_set.add(id(d))
        hooks = []
        for (k, v) in d.items():
            if isinstance(v, NDHook):
                hooks.append(k)
            if k[0] != '_': handle_dict([(k,v)] + ns)
        for k in sorted(hooks):
            hook = d.get(k)
            hook.onload(ns)
    handle_dict([('top', global_dict)])

# def collect_keys(d, is_match):
#     done_set = set()
#     def _collect_keys(d, is_match):
#         if type(d) != dict or id(d) in done_set: return set()
#         done_set.add(id(d))
#         key_set = set(k for k in d.keys() if is_match(k))
#         for v in d.values():
#             key_set |= collect_keys(v, is_match)
#         return key_set
#     return _collect_keys(d, is_match)

@AfterLoad.regist
def after_load_call_hook():
    _call_hook(globals())

def build_dict(*args, **kw):
    def dict_filter(f, d):
        return dict(filter(f, d.items()))
    def dict_updated(*args, **kw):
        new_dict = dict()
        for d in args:
            new_dict.update(d)
        new_dict.update(kw)
        return new_dict
    return dict_filter(lambda k_v: not k_v[0].startswith('__'), dict_updated(*args, **kw))

class ChainBuilder:
    def __init__(self):
        self.chain = []

    def __call__(self, node):
        self.chain.append(node)
        return node

    def build(self, **kw):
        for node in self.chain:
            kw = node(**kw)
        return kw
