#!/usr/bin/env/python
#-*- coding:utf-8 -*-

__author__ = 'BlackYe.'

from ConfigParser import ConfigParser

class ArgumentParse(object):

    def __init__(self, url):
        self.cookie = ''
        self.useragent = ''
        self.max_threads = 5
        self.max_retrys =  3
        self.delay = 0.5
        self.http_timeout = 30

        self.proxy = None

        conf = ConfigParser()
        conf.read("config.conf")
        self.bakdir_exts = eval(conf.get('dict', 'bakdir_exts'))
        self.bakfile_exts = eval(conf.get('dict', 'bakfile_exts'))
        self.__load_scan_dic(url, conf.get('dict', 'web_dic_path'), conf.get('dict', 'path_dic_path'))

    def __load_scan_dic(self, url, path_dic, file_dic):
        '''
        加载路径探测字典
        :param path_dic:
        :param file_dic:/
        :return:
        '''
        from urlparse import urlparse
        from IPy import IP
        with open(path_dic, 'r') as file:
            self.dir_dic = list(set([each.strip(' \r\n') for each in file.readlines()]))
        file.close()

        with open(file_dic, 'r') as file:
            self.file_dic = list(set([each.strip(' \r\n') for each in file.readlines()]))
            try:
                IP(urlparse(url).netloc.split(':')[0]) #域名形式 www.baidu.com.tar.gz
            except ValueError:
                self.file_dic.extend(['%s%s' % (urlparse(url).netloc.split(':')[0], webfile) for webfile in self.bakdir_exts])
        file.close()

