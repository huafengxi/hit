def retry_loop(_retryf, timeout=864000, interval=1, msg='', **kw):
    log_level = int(kw.get('_tlog_', '1'))
    logger.info('retryloop: timeout=%s interval = %s', str(timeout), str(interval))
    end_time = time.time() + safe_int(timeout, 60)
    while time.time() < end_time:
        logger.log(log_level, '#### tryloop %s ####', msg)
        try:
            result = _retryf()
            logger.log(log_level, '#### tryloop success ####')
            return 'succ'
        except Exception as e:
            logger.info('tryloop fail: %s', e)
        sys.stdout.flush()
        time.sleep(float(interval))
    raise Fail('retryloop %s timeout'%(msg))

@MagicMap.regist
def magic_tryloop(ns, cmd, args, kw):
    return retry_loop(lambda : magic_call(ns, cmd, args, kw), msg=cmd, *args, **dict_updated(ns_leaf(ns), kw))

@MagicMap.regist
def magic_seq(ns, cmd_list, args, kw):
    cmd_seq = [(cmd, arg and parse_cmd_args(arg.split(',')) or ([],{})) for cmd, arg in re.findall(r'([0-9a-zA-Z._]+)(?:\[(.*?)\])?', cmd_list)]
    return [(cmd, CALL(ns, cmd, (_args + list(args)), dict_updated(_kw, kw))) for cmd, (_args,_kw) in cmd_seq]

@MagicMap.regist
def magic_all(ns, cmd, args, kw):
    members, cmd = cmd.split(' ', 1)
    members = magic_call(ns, members, args, kw)
    return [('{}.{}'.format(k, cmd), magic_call(ns_add(ns, k, v), cmd, args, kw)) for k,v in members if not k.startswith('_')]

@MagicMap.regist
def magic_rand(ns, cmd, args, kw):
    members, cmd = cmd.split(' ', 1)
    members = magic_call(ns, members, args, kw)
    members = [(k, v) for k,v in members if not k.startswith('_')]
    if not members: return 'empty set'
    k, v = random.choice(members)
    return '{}.{}'.format(k, cmd), magic_call(ns_add(ns, k,v), cmd, args, kw)

@MagicMap.regist
def magic_uniq(ns, cmd, args, kw):
    return list(set(ret for (key, ret) in magic_all(ns, cmd, args, dict_updated(kw, _log_=0))))

def is_match(key, pat, *args, **kw):
    attr = kw.get(key, None)
    return type(attr) == str and re.match(pat, attr)

@MagicMap.regist
def magic_filter(ns, cond, args, kw):
    return [(k, v) for k,v in sorted(ns_leaf(ns).items(), key=lambda x:str2alphanum(x[0])) if type(v) == dict and not k.startswith('_') and magic_call(ns_add(ns,k, v), cond, args, dict_updated(kw, _tlog_=2))]

@MagicMap.regist
def magic_cond(ns, cmd, args, kw): # '!cond: not xxx: actiont'
    cond, cmd = cmd.split(': ', 1)
    neg = cond.startswith('not')
    if neg:
        cond_cmd = cond.split(' ', 1)[-1]
    else:
        cond_cmd = cond
    result = magic_call(ns, cond_cmd, args, kw)
    if (neg and not result) or (not neg and result):
       return magic_call(ns, cmd, args, kw)
    return 'skip %s'%(cmd)

@MagicMap.regist
def magic_check(ns, cmd, args, kw):
    m = re.split(' *# *', cmd)
    if len(m) != 2:
        raise Fail('check cmd should be split by #')
    cmd, msg = m
    try:
        magic_call(ns, cmd, args, kw)
        return 'OK'
    except Fail as e:
        raise Fail('check fail: %s'%(msg))

