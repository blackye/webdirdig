#!/usr/bin/env/python
#-*- coding:utf-8 -*-

__author__ = 'BlackYe.'


import random
import string


class RandomUtils(object):
    @classmethod
    def randString(cls, n=12, omit=None):
        seq = string.ascii_lowercase + string.ascii_uppercase + string.digits
        if omit:
            seq = list(set(seq) - set(omit))
        return ''.join(random.choice(seq) for _ in range(n))