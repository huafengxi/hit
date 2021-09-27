import repl
CompHook = Hook()
class ConsoleInterp(repl.BaseInterp):
    def __init__(self, env):
        repl.BaseInterp.__init__(self, env, env)

    def preprocess(self, line):
        cmd = pymix_parse(line)
        logger.trace('Command: %s -> %s', line.strip(), cmd.strip())
        return cmd

    def get_matched(self, prefix, prefix2):
        def list_merge(ls): return reduce(lambda a,b: list(a)+list(b), ls, [])
        locals, globals = self.prepare_env()
        result = []
        try:
            result = CompHook(prefix, prefix2, locals, globals)
        except Exception as e:
            logger.debug('get_matched: %s %s: %s', prefix, prefix2, traceback.format_exc())
        return list_merge(result)

def console(**kw):
    console.mode = 'interactive'
    return repl.Console(hit_file_path('.hit_history')).repl(ConsoleInterp(globals()))

@CompHook.regist
def comp_base(prefix, prefix2, locals, globals):
    completer = repl.Completer('disable-reboot _log_ _mode_'.split(), locals, globals)
    return completer.get_matched(prefix, prefix2)
import copy

@CompHook.regist
def comp_ndict(prefix, prefix2, locals, globals):
    if not re.match('[.a-zA-Z0-9]+', prefix):
        return []
    def dict_updated(d, **kw):
        new_dict = copy.copy(d)
        new_dict.update(**kw)
        return new_dict
    def split_path(path):
        p = path.rsplit('.', 1)
        return len(p) > 1 and p or [''] + p
    dir_path, attr_name = split_path(prefix)
    if dir_path:
        d = find(locals, dir_path)
    else:
        d = dict_updated(locals, **globals)
    if type(d) != dict:
        d = {}
    return ['%s%s'%(dir_path and '%s.'%(dir_path) or '', type(v) == dict and '%s.'%(k) or k) for k,v in d.items() if not k.startswith('_')]

def reload_console(**kw):
    os.execl(sys.argv[0], *sys.argv)

def cd(dir='', **kw):
    if not dir: dir = '~'
    os.chdir(os.path.expanduser(dir))
