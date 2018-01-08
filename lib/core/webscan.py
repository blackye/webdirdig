#!/usr/bin/env/python
#-*- coding:utf-8 -*-

__author__ = 'BlackYe.'


from lib.common.util import RandomUtils
from lib.common.fuzzy_string_cmp import DynamicContentParser
from difflib import SequenceMatcher

import re

class WebScan(object):

    def __init__(self, requester, test_path = None, suffix = None, bdir = False):

        '''
        if test_path is None or test_path is "":
            self.test_path = RandomUtils.randString()
        else:
            self.test_path = test_path
        '''
        self.test_path = test_path if test_path is not None else ""
        if suffix is None:
            self.suffix = RandomUtils.randString()
        else:
            self.suffix = suffix

        self.bdir = bdir
        self.requester = requester
        self.tester = None
        self.redirect_regexp = None
        self.invalid_status = None
        self.dynamic_parser = None
        self.ratio = 0.98
        self.redirect_status_codes = [301, 302, 307]
        self.__init_env()

    def __init_env(self):
        first_path = self.test_path + self.suffix + '%s' % ('/' if self.bdir else '')
        first_response = second_response = None
        try:
            first_response = self.requester.request(first_path)
        except Exception,e:
            return
        self.invalid_status = first_response.status
        if self.invalid_status == 404:
            # Using the response status code is enough :-}
            return

        # look for redirects
        second_path = self.test_path + RandomUtils.randString(omit=self.test_path) + '%s' % ('/' if self.bdir else '')
        try:
            second_response = self.requester.request(second_path)
        except Exception:
            return
        if first_response.status in self.redirect_status_codes and first_response.redirect and second_response.redirect:
            self.redirect_regexp = self.generate_redirect_regexp(first_response.redirect, second_response.redirect)

        # Analyze response bodies
        self.dynamic_parser = DynamicContentParser(self.requester, first_path, first_response.body, second_response.body)
        base_ratio = float("{0:.2f}".format(self.dynamic_parser.comparisonRatio))  # Rounding to 2 decimals
        # If response length is small, adjust ratio
        if len(first_response) < 2000:
            base_ratio -= 0.1
        if base_ratio < self.ratio:
            self.ratio = base_ratio

    def generate_redirect_regexp(self, first_location, second_location):
        if first_location is None or second_location is None:
            return None
        sm = SequenceMatcher(None, first_location, second_location)
        marks = []
        for blocks in sm.get_matching_blocks():
            i = blocks[0]
            n = blocks[2]
            # empty block
            if n == 0:
                continue
            mark = first_location[i:i + n]
            marks.append(mark)
        regexp = "^.*{0}.*$".format(".*".join(map(re.escape, marks)))
        return regexp

    def scan(self, path):
        response = None
        try:
            response = self.requester.request(path)
        except Exception:
            return False

        if hasattr(response.headers, 'Content-Length') and not int(response.headers.get('Content-Length')): #过滤掉空白页面
            return False
        if self.invalid_status == 404 and response.status == 404:
            return False
        if response.status >= 400 and response.status < 404:
            return False
        if self.invalid_status != response.status:
            return True
        redirect_to_invalid = False
        if self.redirect_regexp is not None and response.redirect is not None:
            redirect_to_invalid = re.match(self.redirect_regexp, response.redirect) is not None
            # If redirection doesn't match the rule, mark as found
            if not redirect_to_invalid:
                return True

        ratio = self.dynamic_parser.relative_distance(response.body)
        if ratio >= self.ratio:
            return False
        elif redirect_to_invalid and ratio >= (self.ratio - 0.15):
            return False
        return True
