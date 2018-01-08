#!/usr/bin/env/python
#-*- coding:utf-8 -*-

__author__ = 'BlackYe.'

from lib.core.argument import ArgumentParse as Argument
from lib.controller.scanner import Scanner

from lib.common.output import ConsoleOutput
from lib.net.myrequests import Requester
from lib.common.myexception import RequestException, SkipTargetInterrupt
from lib.common.output import output

class Controller(object):

    def __init__(self, url):

        self.arguments = Argument(url)

        output.debug('Start scan......')
        try:
            self.requester = Requester(url, cookie = self.arguments.cookie,
                                            useragent = self.arguments.useragent,
                                            maxPool = self.arguments.max_threads,
                                            maxRetries = self.arguments.max_retrys,
                                            delay = self.arguments.delay,
                                            timeout = self.arguments.http_timeout,
                                            proxy=self.arguments.proxy,
                                            redirect = True)
            self.requester.request("/")

        except RequestException as e:
            output.error(e.args[0]['message'])
            raise SkipTargetInterrupt

        #matchCallbacks = [self.matchCallback]

        self.scanner = Scanner(self.requester,
                               concurrent_num = 20,
                               internal_timeout = 60,
                               dictionary = {'dir_dic' : self.arguments.dir_dic,
                                             'file_dic' : self.arguments.file_dic,
                                             'bakdir_exts' : self.arguments.bakdir_exts,
                                             'bakfile_exts' : self.arguments.bakfile_exts},
                               match_callbacks = [])

        try:
            self.run()
        except RequestException as e:
            output.error("Fatal error during site scanning: " + e.args[0]['message'])
            raise SkipTargetInterrupt
        finally:
            pass

        output.warning('\nTask Completed')


    def run(self):
        self.scanner.start()