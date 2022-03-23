@MagicMap.regist
def magic_handle_call_line(ns, cmd, args, kw):
    ns, func = args[0]
    return call_handle_target(ns, func, args[1:], kw)

@MagicMap.regist
def magic_handle_call_head(ns, cmd, args, kw):
    ns, func = args[0]
    return call_handle_target(ns, func, args[1:], kw)

@MagicMap.regist
def magic_call(ns, cmd, args, kw):
    cmd_list = shlex.split(cmd)
    _args, _kw = parse_cmd_args(cmd_list[1:])
    return CALL(ns, cmd_list[0], (_args + list(args)), dict_updated(_kw, kw))

@MagicMap.regist
def magic_pyexpr(ns, cmd, args, kw):
    try:
        result = eval(cmd, globals(), ns_leaf(ns))
    except Exception as e:
        logger.debug('pyexpr fail: %s', traceback.format_exc())
        raise Fail("pyexpr fail: %s"%(e))
    return result

@MagicMap.regist
def magic_pysuite(ns, cmd, args, kw):
    exec(cmd, globals(), ns_leaf(ns))
