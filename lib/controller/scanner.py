#!/usr/bin/env/python
#-*- coding:utf-8 -*-

__author__ = 'BlackYe.'

import gevent
from gevent import monkey
from gevent import Greenlet
from gevent.pool import Pool
from gevent import queue
from gevent import event
from gevent import Timeout
monkey.patch_all()

from lib.core.webscan import WebScan
from lib.common.output import output

import gc
from copy import deepcopy

class Scanner(object):

    def __init__(self, requester, concurrent_num = 50, internal_timeout = 60, dictionary = {}, match_callbacks = []):

        self.requester = requester
        self.dictionary = dictionary #扫描字典
        #self.threadsCount = threads if len(self.dictionary) >= threads else len(self.dictionary)
        self.concurrent_num = concurrent_num
        self.match_callbacks = match_callbacks

        self.internal_timeout = internal_timeout

        self.dir_max_threshold_cnt  = 10 #目录最大阈值
        self.file_max_threshold_cnt = 20 #文件最大阈值

        self.stop_signal = event.Event()

        self.exist_sensi_que = queue.Queue()
        self.exist_dir_cache_que = queue.Queue() #exist path cache
        self.exist_dir_que  = queue.PriorityQueue()
        self.exist_file_cache_que = queue.Queue() #current file exist dir cache

        self._webdir_pool = Pool(self.concurrent_num)
        self.webdir_pool = Pool(self.concurrent_num)
        self.webfile_pool = Pool(self.concurrent_num)

        self.default_dir_webscan = WebScan(self.requester, bdir = True)
        self.default_file_webscan = WebScan(self.requester)


    def start(self):
        # Setting up testers

        self.start_webdir_scan()
        self.start_webfile_scan()
        self.start_webfileext_scan()

        print self.exist_sensi_que.queue


        """
        for callback in self.match_callbacks:
            callback(result)
        """

    def stop_scan(self):
        self.stop_signal.set()


    def __push_result2dir(self, origin_que, target_ques):
        assert True == isinstance(target_ques, list)

        if not self.stop_signal.isSet():
            while not origin_que.empty():
                _ = origin_que.get_nowait()
                for item_que in target_ques:
                    item_que.put(_)
            self.stop_signal.clear()

        self.__clear_cache_queue(origin_que)

    def __push_result2file(self, origin_que, target_ques):
        assert True == isinstance(target_ques, list)

        if not self.stop_signal.isSet():
            while not origin_que.empty():
                _ = origin_que.get_nowait()
                target_ques[0].put(_)
                target_ques[1].put(_[1])

            self.stop_signal.clear()
        self.__clear_cache_queue(origin_que)

    def __clear_cache_queue(self, origin_que):
        origin_que.queue.clear()

    def __spider_crawler_schedu(self):
        pass

    def start_webdir_scan(self):
        output.debug(">> Start first web dir scan.....")
        #self._webdir_pool.map(self.__webdir_first_scan_schedu, ['/%s/' % str(dir_dic) for dir_dic in self.dictionary['dir_dic']])

        exist_dir_cache_que = queue.Queue()
        for dir_dic in self.dictionary['dir_dic']:
            self.webdir_pool.apply_async(self.__webdir_scan_schedu, args = (self.default_dir_webscan , '/%s/' % dir_dic, exist_dir_cache_que))

        self.webdir_pool.join()
        self.__push_result2dir(exist_dir_cache_que, [self.exist_dir_que, self.exist_dir_cache_que])

        output.debug(">> Start web dir scan....")
        try:
            while not self.exist_dir_cache_que.empty():
                dir_suffix = self.exist_dir_cache_que.get_nowait()
                output.debug("[+] found exist dir :%s" % dir_suffix)
                testwebscan = WebScan(self.requester, test_path = dir_suffix, suffix = None, bdir = True)
                for dir_dic in self.dictionary['dir_dic']:
                    test_dir_dic = '%s%s/' % (dir_suffix, dir_dic)
                    self.webdir_pool.apply_async(self.__webdir_scan_schedu, args = (testwebscan, test_dir_dic, exist_dir_cache_que))

                self.webdir_pool.join()
                self.__push_result2dir(exist_dir_cache_que, [self.exist_dir_que, self.exist_dir_cache_que])

        except queue.Empty as e:
            pass

        output.debug("[==] web dir scan over...:")
        del self.exist_dir_cache_que
        del exist_dir_cache_que


    def __webdir_scan_schedu(self, testwebscan, test_dir_dic, exist_dir_cache_que):
        output.debug("scan dir: %s" % test_dir_dic)

        if not self.stop_signal.isSet():
            if exist_dir_cache_que.qsize() <= self.dir_max_threshold_cnt:
                if testwebscan.scan(test_dir_dic):
                    exist_dir_cache_que.put(test_dir_dic)
            else:
                self.stop_scan()
        else:
            output.debug('[--] exist scan dir: %s' % test_dir_dic)


    def start_webfile_scan(self):
        '''
        文件爆破
        :return:
        '''
        gc.collect()
        self.exist_sensi_que.queue = deepcopy(self.exist_dir_que.queue)
        self.exist_dir_que.put('/')
        output.debug(">> Start scan web file scan.....")

        exist_file_cache_que = queue.Queue()

        try:
            while not self.exist_dir_que.empty():
                exist_dir_suffix = self.exist_dir_que.get()
                if exist_dir_suffix != '/':
                    testwebscan = WebScan(self.requester, test_path = exist_dir_suffix, suffix = None, bdir = False)
                    for file_dic in self.dictionary['file_dic']:
                        self.webfile_pool.apply_async(self.__webfile_scan_schedu, args=(testwebscan, '%s%s' % (exist_dir_suffix, file_dic), exist_file_cache_que))

                    self.webfile_pool.join()
                    self.__push_result2file(exist_file_cache_que, [self.exist_file_cache_que, self.exist_sensi_que])

                    #动态添加存在的目录文件字典
                    # /help      =>  /help.tar.gz
                    # /help/test =>  /help/test.tar.gz
                    for bakdir_ext in self.dictionary['bakdir_exts']:
                        ox = exist_dir_suffix.split('/')
                        ox.remove('')
                        self.webfile_pool.apply_async(self.__webfile_scan_schedu, args=(testwebscan, ''.join(('/' + _) if _ != '' else (_ + bakdir_ext) for _ in ox), exist_file_cache_que))

                    self.webfile_pool.join()
                    self.__push_result2file(exist_file_cache_que, [self.exist_file_cache_que, self.exist_sensi_que])

                else:
                    for file_dic in self.dictionary['file_dic']:
                        self.webfile_pool.apply_async(self.__webfile_scan_schedu, args=(self.default_file_webscan, '/%s' % file_dic, exist_file_cache_que))
                    self.webfile_pool.join()
                    self.__push_result2file(exist_file_cache_que, [self.exist_file_cache_que, self.exist_sensi_que])

        except queue.Empty as e:
            pass

        del exist_file_cache_que
        output.debug("[==] web file scan over...:")


    def __webfile_scan_schedu(self, testwebscan, test_file_dic, exist_file_cache_que):
        output.debug("scan file: %s" % test_file_dic)
        if not self.stop_signal.isSet():
            if self.exist_file_cache_que.qsize() <= self.file_max_threshold_cnt:
                if testwebscan.scan(test_file_dic):
                    exist_file_cache_que.put((testwebscan, test_file_dic))
            else:
                self.stop_scan()
        else:
            output.debug('[--] exist scan file:%s' % test_file_dic)

    def start_webfileext_scan(self):
        '''
        脚本备份文件爆破
        /help/a.php  -> /help/a.php.bak
        :return:
        '''
        output.warning(">> Start file ext scan....")
        exist_webfileext_que = queue.Queue()
        try:
            while not self.exist_file_cache_que.empty():
                testwebscan, exist_file = self.exist_file_cache_que.get_nowait()
                try:
                    ext_pos = exist_file.rindex(".")
                    if exist_file[ext_pos:] in ['.php', '.asp', '.jsp', 'jspx', 'aspx']:
                        for bakfile_ext in self.dictionary['bakfile_exts']:
                            self.webfile_pool.apply_async(self.__webfile_scan_schedu, args = (testwebscan, '%s%s' % (exist_file, bakfile_ext), exist_webfileext_que))

                        self.webfile_pool.join()
                        self.__push_result2file(exist_webfileext_que, [self.exist_file_cache_que, self.exist_sensi_que])

                except ValueError:
                    pass
        except queue.Empty as e:
            pass

        del exist_webfileext_que
        del self.exist_file_cache_que