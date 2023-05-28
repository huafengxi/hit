def sub(template, ns, max_iter=50):
    '''no exception should hitpen'''
    if '$' not in template: return template
    logger.debug('ns=%s template=%s', epath(ns), repr(template))
    def template_substitute(template, ns, substitute_handler):
        '''magic marker example: $word ${abc.def} ${{1+2}}'''
        return re.sub('(?s)(?<![$])(?:\${{(.+?)}}|\${(.+?)}|\$([a-zA-Z_]\w*))', lambda m: substitute_handler(ns, m.group(1) or m.group(2) or m.group(3), m.group(0)), template)
    def format_ret(x, orig):
        if (type(x) == list or type(x) == tuple) and all(type(x) == str for x in x):
            return ' '.join(x)
        if x == None or type(x) != str and type(x) != int and type(x) != float and type(x) != long:
            return orig
        else:
            return str(x)
    old, cur = "", template
    def substitute_handler(ns, expr, orig_expr):
        try:
            ret = handle_interpolate(expr, ns)
        except Exception as e:
            logger.debug('interpolate fail: expr=%s, ns=%s, %s', expr, epath(ns), traceback.format_exc())
            ret = orig_expr
        logger.debug('sub: %s expr=%s to=%s', epath(ns), repr(expr), repr(ret))
        ret = format_ret(ret, orig_expr)
        return ret
    for i in range(max_iter):
        if cur == old: break
        old, cur = cur, template_substitute(cur, ns, substitute_handler)
    logger.debug('sub ret: ns=%s template=%s ret=%s', epath(ns), repr(template), repr(cur))
    return cur

def handle_interpolate(expr, ns):
    if expr.count('\n') > 0:
        exec(expr, globals(), prepare_eval_env(ns))
        return ''
    return CALL(ns, expr, [], dict(_tlog_=3))
