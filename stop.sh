#!/usr/bin/env python
#coding:utf-8
import commands
import os
import sys

def kill_process(pid):
    _str = commands.getoutput("netstat -lnpte|grep {}".format(pid) + "|awk '{print $NF}'")
    p_pp_li = _str.split('/')
    print p_pp_li

    os.system('kill -9 {} 2>/dev/null'.format(p_pp_li[0]))


if __name__ == '__main__':
    pid = sys.argv[1]
    kill_process(pid)
    kill_process(pid)

