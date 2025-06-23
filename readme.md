# what hit.py can do

## dispatch python function
edit a.py
```
logger.set_log_level(0)
a, b = 1, dict(c=2)
d = '$a ${b.c}'
def hello(c=3, **__kw): return 'hello c=%d'%(int(c))
echo = '!sh: echo c=$c'
```

test
`$ alias i='./hit.py a.py'`

inspect vars
```
hit$ i a
1
hit$ i b
{'c': 2}
hit$ i b.c
2
```

string interpolation
```
hit$ i d
1 2
```

call function
```
hit$ i hello
hello c=3
hit$ i hello 4
hello c=4
hit$ i hello c=5
hello c=5
hit$ i b.hello
hello c=2
hit$ i b.hello c=6
hello c=6
```

shell command
```
hit$ i echo
c=
0
hit$ i echo c=3
c=3
0
hit$ i b.echo
c=2
0
```
