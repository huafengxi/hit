def dict_updated(*args, **kw):
    new_dict = dict()
    for d in args:
        new_dict.update(d)
    new_dict.update(kw)
    return new_dict

def dict_slice(d, *args):
    return dict((k, d[k]) for k in args if k in d)

def list_merge(ls):
    return reduce(lambda a,b: list(a)+list(b), ls, [])

def expand(spec):
    def multiple_expand(str):
        return [''.join(parts) for parts in itertools.product(*[re.split('[ ,]+', i) for i in re.split(r'\[(.*?)\]', str)])]
    return list_merge(map(multiple_expand, spec.split()))

def str2alphanum(x):
    return [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', x)]

def read(path):
    try:
        with open(path) as f:
            return f.read()
    except IOError as e:
        return ''

def write(path, content):
    with open(path, 'w') as f:
        f.write(content)

def sleep(sleep_time=1, **kw):
    logger.info('sleep %s', str(sleep_time))
    for i in range(int(sleep_time)):
        time.sleep(1)

def safe_int(x, default_value):
    try: return int(x)
    except TypeError as e:
        return default_value

import codecs
def hexlify(text): return codecs.encode(text, "hex")
def unhexlify(text): return codecs.decode(text, "hex")
def _fuzz(text):
    cypher = itertools.cycle('fyuqsrmnqwyvqrjl')
    return ''.join(chr(ord(c) ^ ord(cypher.next())) for c in text)
def fuzz(text): return hexlify(_fuzz(text))
def unfuzz(text): return _fuzz(unhexlify(text))
