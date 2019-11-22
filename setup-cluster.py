#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# auth: jessen
# purpose: redis-cluster-test

## 准备步骤 ##
# 1. 下载 redis源码, 解压, 目录名称改为redis
# 2. 将此脚本放在 redis 同级目录中
# 3. 执行脚本
#   自动创建 redis-cluster 目录 ,生成配置文件, 启动集群, 并进行集群配置

##  脚本逻辑说明  ##
# 0.默认会创建一个 9 个节点的集群 (3个master, 每个 master 2个slave )
# genConf.首先会根据端口号自动创建 相应的目录, 每个目录中一个 redis.conf 配置文件, copy 自 redis 源码目录. 然后自动修改 其中的参数.
# startall. 启动所有 redis 实例 (命令执行目录为 端口号目录内部)
# meet. 以第一个 master 节点为起始 , 对其他所有节点 进行 cluster meet, 将所有节点组到一个 cluster 中
# addslots. 根据 master 个数, 自动均分 16384 个槽位, 并进行 cluster addslots 操作
# do_replicate. 对所有的slave 节点执行命令: cluster replicate <master node id>

# 可以需要修改的地方
# a)redis 目录名称, 创建的 redis-cluster 配置目录
# b)主节点个数, 端口号. slave 个数 (slave 节点端口号自动顺延)
# c)自动修改的 redis.conf 文件
#

import os
import shutil
import time
import sys

def clean_dir(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.makedirs(dir)

base_dir = os.getcwd()
redis_bin_dir = base_dir+'/redis/src'

master_ports = range(7001, 7004)  # 3 个 master, 端口分别是 7001~7003
master_count = len(master_ports)
replicate = 2  # 每个 master 2个 replicate

all_ports = list(master_ports)
next_port = max(master_ports)+1
for i in range(0, replicate*master_count):
    all_ports.append(next_port)
    next_port = next_port+1
master_ports = [str(x) for x in master_ports]
all_ports = [str(x) for x in all_ports]


cdir = 'redis-cluster'

clean_dir(cdir)
os.chdir(cdir)


def print_green(text):
    print('\033[0;32m'+str(text)+'\033[0m')


def print_blue(text):
    print('\033[0;34m'+str(text)+'\033[0m')


def genConf():
    for p in all_ports:
        os.mkdir(p)
        shutil.copy('../redis/redis.conf', p)
        fn = p+'/redis.conf'
        lines = []

        # 匹配开头, 替换整行
        remap = {
            'bind ': '#bind 127.0.0.1',
            'port ': 'port '+p,
            'protected-mode ': 'protected-mode no',
            'daemonize ': 'daemonize yes',
            'pidfile ': 'pidfile /var/run/redis_'+p+'.pid',
            '# cluster-enabled ': 'cluster-enabled yes',
            '# cluster-node-timeout ': 'cluster-node-timeout 15000',
            '# cluster-config-file ': 'cluster-config-file nodes.conf'
        }
        print('\n')
        print_blue('generate cluster config: '+fn)
        f = open(fn, 'r')
        for line in f.readlines():
            line = line.strip('\n')
            for (k, v) in remap.items():
                if line.startswith(k):
                    print(line, ' => ', v)
                    line = v

            lines.append(line)
        f.close()
        # TODO 如果需要的配置不在文件中, 则需要添加行

        f = open(fn, 'w')
        for line in lines:
            f.write(line+'\n')
        f.close()
        print_green('generate cluster config done: file='+fn)


def startall():
    print_blue('starting redis servers ...')
    os.chdir(base_dir+'/'+cdir)
    for p in all_ports:
        os.chdir(p)
        os.system(redis_bin_dir+'/redis-server redis.conf')
        os.chdir('..')
    print_green('start all redis server success')


def meet():
    print_blue('do cluster meet ...')
    p0 = all_ports[0]
    for p in all_ports[1:]:
        os.system(redis_bin_dir+'/redis-cli -p '+p0 +
                  ' cluster meet 127.0.0.1 '+p+' > /dev/null')
        print_green(p0+' cluster meet '+p+' success')


def addslots():
    print_blue('adding slots ...(this will take a while)')
    avg_solts = 16384/master_count
    slots = {}
    b = 0
    for p in master_ports[:-1]:
        ran = [b, b+avg_solts]
        slots[p] = ran
        b = ran[1]+1
    slots[master_ports[master_count-1]] = [b, 16383]

    for (port, r) in slots.items():
        sys.stdout.write('add slots '+str(r) + ' to '+port+'.     ')
        for i in range(r[0], r[1]+1):
            os.system(redis_bin_dir+'/redis-cli -p '+port +
                      ' cluster addslots '+str(i) + ' > /dev/null')
            sys.stdout.write('\b\b\b\b')
            sys.stdout.write('{:>3d}%'.format((i-r[0])*100/(r[1]-r[0])))
            sys.stdout.flush()
        print_green(' done')
    print_green('add slots done')

# nodes.conf 中含有 myself 的行, 最前端的字符串


def get_node_id(port):
    os.chdir(base_dir+'/'+cdir+'/'+str(port))
    f = open('nodes.conf', 'r')
    node_id = ''
    for line in f.readlines():
        if line.find('myself') > 0:
            node_id = line.split(' ')[0]
            break
    f.close()
    return node_id


def do_replicate():
    print_blue('do cluster replicate')
    rep_map = {}
    idx = master_count
    for p in master_ports:
        rep_map[p] = []
        for i in range(0, replicate):
            rep_map[p].append(all_ports[idx])
            idx = idx+1

    for (m, s) in rep_map.items():
        m_id = get_node_id(m)
        for s0 in s:
            os.system(redis_bin_dir+'/redis-cli -p ' + s0 + ' cluster replicate '+m_id)
            print_green(s0+' replicate to '+m+'('+m_id+')')


genConf()
startall()
meet()
#print_blue('sleep 3s ...')
# time.sleep(3)
addslots()
do_replicate()
