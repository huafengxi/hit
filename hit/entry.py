from meal import EvalDict,EvalList,Matching,NotMatch,MatchList,FuncMap
ArgvMatch = MatchList()

@ArgvMatch.regist
def argv_match_empty(args=None, **opt):
    Matching.test(not args)
    return 'console'

@ArgvMatch.regist
def argv_match_ish(**opt):
    return 'ish'

from hook import Hook
AfterLoad, TearDown = Hook(), Hook()

def entry(args, kw):
    AfterLoad()
    head = ArgvMatch.match(dict(args=args, kw=kw))
    logger.trace('ArgvMatch: head=%s args=%s kw=%s', head, args, kw)
    TearDown()
    return globals()[head](*args, **kw)

