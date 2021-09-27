def make_sh_mon(ip='', cmd='tsar -l -i 1', log='tsar-basic.log', **__kw):
    role = 'mon'
    id = '$log'
    start = '!ssh: nohup $cmd > $log & '
    tail = '!ssht: tail -f $log'
    stop = '!ssh: pkill -f -x "^$cmd" # NoException'
    pid = '!sshp: pgrep -f -x "^$cmd" || echo none'
    return build_dict(locals(), __kw)

def make_sys_mon(ip='', **__kw):
    tsar = make_sh_mon(ip, cmd='tsar -l -i 1 --cpu --tcp --load --pcsw', log='tsar.log')
    tsar0 = make_sh_mon(ip, cmd='tsar -l -i 1 --io -I dm-0', log='tsar-dm0.log')
    tsar1 = make_sh_mon(ip, cmd='tsar -l -i 1 --io -I dm-1', log='tsar-dm1.log')
    vmstat = make_sh_mon(ip, cmd='vmstat 1', log='vmstat.log')
    # iostat = make_sh_mon(cmd='iostat -x 1', log='iostat.log')
    mpstat = make_sh_mon(ip, cmd='mpstat -P ALL 1', log='mpstat.log')
    all_mon = '!filter: role mon'
    id = '!all: all_mon id'
    pid = '!all: all_mon pid'
    start = '!all: all_mon start'
    stop = '!all: all_mon stop'
    restart = '!seq: stop start'
    return build_dict(locals(), __kw)

@spec_load.regist('h')
def Host(ip, **__kw):
    mon = make_sys_mon(ip)
    role = 'host'
    id = '$ip'
    basedir = _hit_path_
    ssh = '!sh: ssh -t $ip $_rest_'
    sudo = '''$basedir/sshpass -P '"password for $usr:"' -f $basedir/my.pass sudo'''
    rsync = '!sh: rsync -avz bin $ip:'
    sshpass = '!sh: sshpass -f $passwd rsync -avz ~/.ssh $ip:'
    free_mem = "!sshp: free -g |sed -n '3p' |awk '{print $4}'"
    total_mem = "!sshp: free -g |sed -n '2p' |awk '{print $2}'"
    core_num = "!sshp: lscpu -p |grep -v '^#' |wc -l"
    disk_num = "!sshp: df -h|grep '^/dev/' |wc -l"
    home_free = "!sshp: df -h /home |sed -n '2p' |awk '{print $4}'"
    netdev = "!sshp: ifconfig |grep '^eth' |sed -n 1p |awk '{print $1}'"
    netspeed = "!sshsudo: ethtool $netdev |grep Speed | awk '{print $2}'"
    clock = "!sshp: cat /sys/devices/system/clocksource/clocksource0/current_clocksource"
    hugepage = "!sshp: cat /sys/kernel/mm/redhat_transparent_hugepage/enabled |grep -o '\[.*\]'"
    kernel = "!sshp: uname -r |grep -o 'el[0-9]'"
    load = "!sshp: uptime | grep -o 'load average: .*' "
    raid = "!sshsudo: MegaCli64 -LdPdInfo -aAll |grep 'Current Cache Policy' | grep -o 'Write[A-Z][a-zA-Z]*' | tr '\\n' ' '"
    eth_irq = "!sshsudo: $basedir/bind-irq.py eth"
    aliflash_irq = "!sshsudo: $basedir/bind-irq.py aliflash"
    stat = '''!print: $ip ${total_mem}M ${core_num}Core net:$netspeed kernel:$kernel clock:$clock hugepage:$hugepage raid: $raid'''
    irq_stat = '''!print: eth: $eth_irq aliflash: $aliflash_irq'''
    logdisk = 'dm-0'
    tsar = '''!sh: tsar -d 20170920 -i 1 --cpu --tcp --traffic --io -s util,retran,bytin,bytout,await |grep -C  '''
    return build_dict(locals(), **__kw)

@spec_load.regist('hp')
def HostPool(host_list=None, **__kw):
    itime = '2017 09-20 20:02'
    all_host = '!filter: role host'
    passwd = hit_file_path('my.pass')
    id = '!all: all_host id'
    rsync = '!all: all_host rsync'
    stat = '!all: all_host stat'
    sshpass = '!all: all_host sshpass'
    ssh = '!all: all_host ssh'
    return build_dict(locals(), **__kw)
