#!/usr/bin/python
# -*- coding: UTF-8 -*-

# auth: jessen
# purpose: redis sentinel test

import os
import shutil
import time
import sys

base_dir = os.getcwd()
redis_bin_dir = base_dir+'/redis/src'

sdir=base_dir+'/redis-sentinel'

def clean_dir(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.makedirs(dir)


clean_dir(sdir)
os.chdir(sdir)


redis_conf_dir=sdir+'/redises'
redis_port = range(6001,6004)
redis_port = [str(x) for x in redis_port]


sentinel_conf_dir=sdir+'/sentinels'
master_name = 'mymaster'
sentinel_ports = range(26001,26004)
sentinel_ports=[str(x) for x in sentinel_ports]



def print_green(text):
    print('\033[0;32m'+str(text)+'\033[0m')


def print_blue(text):
    print('\033[0;34m'+str(text)+'\033[0m')

def gen_redis_conf():
    clean_dir(redis_conf_dir)
    os.chdir(redis_conf_dir)
    for p in redis_port:
        os.mkdir(p)
        shutil.copy(base_dir+'/redis/redis.conf', p)
        fn=p+'/redis.conf'
        lines = []

        # 匹配开头, 替换整行
        remap = {
            'bind ': '#bind 127.0.0.1',
            'port ': 'port '+p,
            'protected-mode ': 'protected-mode no',
            'daemonize ': 'daemonize yes',
            'pidfile ': 'pidfile /var/run/redis_'+p+'.pid'
        }
        
        print('\n')
        print_blue('generate redis config: '+fn)
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
        if p != redis_port[0]:
            lines.append('slaveof 127.0.0.1 '+redis_port[0])

        f = open(fn, 'w')
        for line in lines:
            f.write(line+'\n')
        f.close()
        print_green('generate redis config done: file='+fn)

def gen_sentinel_conf():
    clean_dir(sentinel_conf_dir)
    os.chdir(sentinel_conf_dir)
    for p in sentinel_ports:
        os.mkdir(p)
        shutil.copy(base_dir+'/redis/sentinel.conf', p)
        fn=p+'/sentinel.conf'
        lines = []

        # 匹配开头, 替换整行
        remap = {
            'port ': 'port '+p,
            'daemonize ': 'daemonize yes',
            'pidfile ': 'pidfile /var/run/redis_sentinel_'+p+'.pid',
            'sentinel monitor ' : 'sentinel monitor '+master_name+' 127.0.0.1 '+redis_port[0] +' ' +str(len(redis_port)/2+1),
            'sentinel down-after-milliseconds ' : 'sentinel down-after-milliseconds ' + master_name+' 30000',
            'sentinel parallel-syncs ' : 'sentinel parallel-syncs '+master_name+' 1',
            'sentinel failover-timeout ' : 'sentinel failover-timeout '+master_name+' 180000'
        }
        
        print('\n')
        print_blue('generate sentinel config: '+fn)
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
        print_green('generate sentinel config done: file='+fn)


def startall_redis():
    print_blue('starting redis servers ...')
    os.chdir(redis_conf_dir)
    for p in redis_port:
        os.chdir(p)
        os.system(redis_bin_dir+'/redis-server redis.conf')
        os.chdir('..')
    print_green('start all redis server success')

def startall_sentinel():
    print_blue('starting sentinel servers ...')
    os.chdir(sentinel_conf_dir)
    for p in sentinel_ports:
        os.chdir(p)
        os.system(redis_bin_dir+'/redis-sentinel sentinel.conf')
        os.chdir('..')
    print_green('start all sentinel server success')


gen_redis_conf()
gen_sentinel_conf()

startall_redis()
startall_sentinel()
