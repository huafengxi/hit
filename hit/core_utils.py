def dump(*args, **kw): return [(i, eval(i)) for i in args]
def seq(*args, **kw): return [(i, entry([i], kw)) for i in args]

def d2ns(d): return d['__rc__']['ns']
def call(d, path, *args, **kw): return CALL(d2ns(d), path, args, dict_updated(d['__rc__']['kw'], kw))
def find_from_top(d, path): return efind_value([('top', d)], path)
def find(d, path): return efind_value(d['__rc__']['ns'], path) if id(globals()) != id(d) else find_from_top(d, path)
def find_base(d, k): return efind_base(d2ns(d), k)
def sub2(tpl, d): return sub(tpl, d2ns(d))
