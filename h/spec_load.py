__doc__ += '''
* spec file loader
./hit.py spec_load.builders    # show spec_load builders
## in config.py
a = spec_load('a.cfg')
## in a.cfg
hp
h 127.0.0.1
'''
class IdxGen:
    def __init__(self):
        self.dict = {}
    def gen(self, key):
        if key in self.dict:
            self.dict[key] += 1
        else:
            self.dict[key] = 0
        return self.dict[key]

class SpecLoad:
    def __init__(self):
        self.builders = {}
    def regist(self, key):
        def do_regist(handler):
            handler.key = key
            self.builders[handler.key]=handler
            return handler
        return do_regist
    def __call__(self, path):
        if not os.path.isfile(path): return dict()
        spec = file(path).read()
        def construct_dict(type, *args, **kw):
            builder = self.builders.get(type, None)
            if callable(builder):
                return builder(*args, **kw)
            else:
                raise Fail("no constructor defined: %s"%(type))
        def parse_dict(line):
            args, kw = parse_cmd_args(line.split())
            return construct_dict(*args, **kw)
        idx_gen = IdxGen()
        def gen_key(line):
            type = line.split()[0]
            handler = self.builders.get(type)
            if not handler: raise Fail('constructor has not key defined: %s'%(type))
            return '%s%d'%(handler.key, idx_gen.gen(type))
        obj_list = [(gen_key(line), parse_dict(line)) for line in spec.split('\n') if line.strip() and not line.startswith('#')]
        if not obj_list: return None
        return build_dict(obj_list[0][1], dict(obj_list[1:]))

spec_load = SpecLoad()
