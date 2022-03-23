_sql_trace_ = False
cur_conn = None

def set_conn(conn):
    global cur_conn
    cur_conn = conn

def on_sql_error(sql, e):
    logger.error("QueryFail: %s: %s", sql, e)
    logger.debug(traceback.format_exc())
    if 'NoException' not in sql:
        raise e

def get_sql_conn(kw, ns):
    conn = kw.get('conn', 'cur')
    return efind_value(ns, '%s_conn'%(conn))

def sql_query(sql, ns, kw):
    conn = get_sql_conn(kw, ns)
    if not conn: raise Fail('no sql conn: %s for %s'%(kw.get('conn', 'cur'), sql))
    try:
        return conn.query(sql, ns)
    except Exception as e:
        on_sql_error(sql, e)

def sql_queryp(sql, ns, kw):
    conn = get_sql_conn(kw, ns)
    if not conn: raise Fail('no sql conn: %s'%(sql))
    try:
        return conn.queryp(sql, ns)
    except Exception as e:
        on_sql_error(sql, e)

@LineMatch.regist
def line_match_sql(head='', **kw):
    Matching.test(head.lower() in 'use set change show alter create drop insert update delete select begin commit rollback'.split())
    return 'sqlp' if kw.get('ctx') == 'void' else 'sql2'

@MagicMap.regist
def magic_sql2(ns, cmd, args, kw):
    return sql_query(sub(cmd, ns), ns, kw)[1]

@MagicMap.regist
def magic_sqlp(ns, cmd, args, kw):
    return sql_queryp(sub(cmd, ns), ns, kw)

def table_format(header, rows):
    if not rows:
        return 'Empty'
    def get_max_lens(rows):
        if not rows:
            return None
        col_lens = [1] * len(rows[0])
        for row in rows:
            for idx, col in enumerate(row):
                if len(str(col)) > col_lens[idx]:
                    col_lens[idx] = len(str(col))
        return col_lens
    def format_row(row, lens):
        return '|' + ''.join(" %-*s |"%(lens[idx], col != None and str(col) or '') for (idx,col) in enumerate(row))
    def ruler(lens):
        return '+' + ''.join('%s+'%('-' * (size + 2)) for size in lens)
    lens = get_max_lens(list(rows) + [header])
    lines = [ruler(lens)] + [format_row(header, lens)] + [ruler(lens)] + [format_row(row, lens) for row in rows] + [ruler(lens)]
    return '\n'.join(lines)

def print_sql_result(header_and_rows):
    (header, rows) = header_and_rows
    print(table_format(header, rows))

# psql
def parse_text_table(output):
    if not output: return
    if 'ERROR' in output: raise Fail('sql fail: %s'%(output))
    lines = re.findall('^\|(.*)\|$', output, re.M)
    if not lines:
        lines = output.split('\n')
        return [[cell.strip() for cell in re.split("\s+", line)] for line in lines]
    return [[cell.strip() for cell in line.split('|')] for line in lines]
class PConn:
    def __init__(self, cmd):
        self.cmd = cmd
    def query(self, sql, d):
        tab = parse_text_table(popen(self.cmd,  sql))
        if tab: return tab[0], tab[1:]
        return [], []
    def queryp(self, sql, d):
        return popen(self.cmd, sql, output=False)

# mysql
from warnings import filterwarnings
try:
    import MySQLdb as sql_connector
except ImportError:
    import mysql.connector as sql_connector
_sql_trace_ = False
class SqlConn:
    def __init__(self, conn_str, user='root', passwd='', database='oceanbase'):
        if ':' not in conn_str: 
            logger.debug("SqlConn: conn_str=%s", conn_str)
            ns = efind([('top', globals())], conn_str)
            if not ns_leaf(ns): raise Fail('can not get_conn because "server" does not exist', conn_str)
            conn_str = sub('$ip:$mysql_port', ns)
        logger.debug('make sql_conn: %s %s %s', conn_str, user, database)
        m = re.match('^(.*?):(.*?)$', conn_str)
        if not m: raise Fail('invalid conn str', conn_str)
        ip, port = m.groups()
        self.conn = sql_connector.connect(host=ip, port=int(port), user=user, passwd=passwd, db=database)
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    def commit(self):
        return self.conn.commit()
    def query(self, sql, d):
        # cur = self.conn.cursor(sql_connector.cursors.Cursor)
        cur = self.conn.cursor()
        cur.execute(sql)
        #result = cur.fetchall()
        desc = cur.description
        if not desc:
            ret = [], []
        else:
            ret = [c[0] for c in desc], list(cur)
        cur.close()
        return ret
    def queryp(self, sql, d):
        return print_sql_result(self.query(sql, d))

#import tsql
#class TConn:
#    def __init__(self, path, env=globals()):
#        self.conn = tsql.TConn(path, env)
#    def close(self):
#        self.conn.close()
#    def query(self, sql, env):
#        return self.conn.query(sql, env)
#    def queryp(self, sql, env):
#        return self.conn.queryp(sql, env)

comp_sql_conn = None

@MagicMap.regist
def magic_sql_comp(ns, cmd, args, kw):
    def write_rows(path, rows):
        write(path, '\n'.join(str(r[0]) for r in rows))
    def dump_diff(main_rows, comp_rows):
        write_rows('a.txt', main_rows)
        write_rows('b.txt', comp_rows)
        direct_popen('diff -u a.txt b.txt')
    if _sql_trace_:
        logger.info('COMP SQL: %s', cmd)
    try:
        header, main_rows = cur_sql_conn.query(cmd)
        header, comp_rows = comp_sql_conn.query(cmd)
        if main_rows != comp_rows:
            dump_diff(main_rows, comp_rows)
            raise Fail('result not match: %s: vimdiff a.txt b.txt'%(cmd))
    except sql_connector.Error as e:
        on_sql_error(cmd, e)

class DummyConn:
    def __init__(self):
        pass
    def close(self): pass
    def query(self, sql, env):
        print(sql)
        return ['sql'], [sql]
    def queryp(self, sql, env):
        return self.query(sql, env)
