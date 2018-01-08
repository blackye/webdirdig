#!/usr/bin/env/python
#-*- coding:utf-8 -*-

__author__ = 'BlackYe.'

import sys
sys.path.append("/data/project/webdirdig")

from lib.core.webscan import WebScan
from lib.net.myrequests import Requester

def f():
    print "haha"

def g():
    print 111


def test(t_queue):
    t_queue.put("hahah")
    t_queue.put("bbbb")
    t_queue.put("cccc")

if __name__ == '__main__':

    from gevent import queue
    s = queue.Queue()
    print s.qsize()
    test(s)
    print s.qsize()

    i = 0
    while i < s.qsize():
        print s.peek()
        i = i+1

    '''
    url = 'http://tx3.cbg.163.com/'
    try:
        requester = Requester(url)
        requester.request("/help/")

    except Exception as e:
        print (e.args[0]['message'])

    webscan = WebScan(requester, test_path = '/help/', suffix= None, bdir = True)
    print webscan.scan("/help/1/")

    for bakdir_ext in ['.tar.gz', '.zip']:
        exist_dir_suffix = '/help//'
        ox = exist_dir_suffix.split('/')
        print ox
        ox.remove('')
        ooxx = ''

        ooxx = ''.join(('/' + _) if _ != '' else (_ + bakdir_ext) for _ in ox)


        print ooxx
    '''
    """

    from gevent import queue
    from copy import deepcopy
    s = queue.PriorityQueue()
    p = queue.Queue()
    s.put("a")
    s.put("b")
    p.queue = deepcopy(s.queue)
    print p

    s.get()
    print p.qsize()
    p.put("test")
    print p.queue
    """