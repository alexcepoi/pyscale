#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

import re
import logging


patterns = {}
patterns['REQ'] = 'rpc'
patterns['SUB'] = 'pub'


def format_args(args=[], kwargs={}):
	args = [repr(i) for i in args]
	kwargs = ['%s=%s' % (key, repr(value)) for key, value in kwargs.items()]
	return ', '.join(args + kwargs)

def format_method(method, args=[], kwargs={}, clean=True):
	if clean:
		if method == '__getattribute__' and len(args) == 1 and not kwargs:
			return '.%s' % args[0]

		if method == '__call__':
			return '(%s)' % format_args(args, kwargs)

	return '.%s(%s)' % (method, format_args(args, kwargs))
