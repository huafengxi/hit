import os
import re
import itertools

id = itertools.count(0)
def gen_path(pat):
    return pat.replace('%', str(id.next()))

def remove(rexp):
    for f in os.listdir('.'):
        if re.match(rexp, f):
            os.remove(f)

def write(pat, content):
    remove(pat.replace('%', '.*'))
    p = gen_path(pat)
    with open(p, 'w') as f:
        f.write(content)
    return p
