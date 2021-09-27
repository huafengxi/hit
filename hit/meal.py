#!/usr/bin/env python2
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

class NotMatch(Exception):
    def __init__(self, msg=''):
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class EvalDict(OrderedDict):
    def __init__(self, __d={}, **kw):
        new_dict = {}
        new_dict.update(__d)
        new_dict.update(kw)
        OrderedDict.__init__(self, new_dict)

class EvalList(list):
    def __init__(self, iter):
        list.__init__(self, iter)

class MatchList(list):
    def __init__(self):
        list.__init__(self)
    def regist(self, rule):
        self.append(rule)
        return rule
    def regist_before(self, func):
        self.insert(0, func)
        return func
    def call(self, d): return self.meal(EvalDict(d))
    def match(self, kw):
        msg = []
        for f in self:
            try:
                return f(**kw)
            except NotMatch as e:
                if e.msg: msg.append(e.msg)
        raise NotMatch('NoMatchCall: {}'.format(msg))
    def meal(self, expr):
        while True:
            if isinstance(expr, EvalDict):
                expr = self.match(dict((k, self.meal(v)) for k, v in expr.items()))
            elif isinstance(expr, EvalList):
                expr = [self.meal(i) for i in expr]
            else:
                break
        return expr

class FuncMap(dict):
    def __init__(self):
       dict.__init__(self) 
    def regist(self, func):
        self[func.func_name] = func
        return func

import re
class Matching:
    @staticmethod
    def test(x):
        if not x:
            raise NotMatch(x)
    @staticmethod
    def test_re(x, pat):
        if not re.match(pat, x):
            raise NotMatch(x)


if __name__ == '__main__':
    X = MatchList()
    E = EvalDict
    @X.regist
    def prod(op=None, x=0, y=0, **kw):
        if op != 'prod': raise NotMatch()
        return x * y

    @X.regist
    def add(op=None, x=0, y=0, **kw):
        if op != 'add': raise NotMatch()
        return x + y

    @X.regist
    def sqrt(op=None, x=0, y=0, **kw):
        if op != 'sqrt': raise NotMatch()
        return E(op='add', x=E(op='prod', x=x, y=x), y=E(op='prod', x=y,y=y))

    print X(op='sqrt', x=3, y=4)
