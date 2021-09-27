import itertools
import copy

def efind(ns, path):
    ns = copy.copy(ns)
    '''example input: ns=[(top, global()] path='a.b.c' '''
    if not path: return ns, None
    def search_key(ns, k):
        for name,env in ns:
            if k in env: return env[k]
    for key in filter(None, path.split('.')):
        d = search_key(ns, key)
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

@AfterLoad.regist
def after_load_call_hook():
    ns, cur_dict_set = [], set()
    def handle_dict(ns, d, k='top'):
        if type(d) != dict: return
        if id(d) in cur_dict_set: return
        cur_dict_set.add(id(d))
        ns.insert(0, (k, d))
        hook = d.get('after_load', None)
        if callable(hook):
            logger.trace("call after_load hook for %s", epath(ns))
            hook(ns)
        for (k, v) in d.items():
            if k[0] != '_': handle_dict(ns, v, k)
        ns.pop(0)
    handle_dict([], globals())

def build_dict(*args, **kw):
    def dict_filter(f, d):
        return dict(filter(f, d.items()))
    def dict_updated(*args, **kw):
        new_dict = dict()
        for d in args:
            new_dict.update(d)
        new_dict.update(kw)
        return new_dict
    return dict_filter(lambda (k,v): not k.startswith('__'), dict_updated(*args, **kw))

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
