#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import glob
import os.path as osp

from .common import patterns
from .socket import Socket

class MultiObject(object):
	def __init__(self, lst):
		self.objs = lst

	# accessing attributes
	def __getattr__(self, method):
		objs = map(lambda x: getattr(x, method), self.objs)
		return MultiObject(objs)

	def __setattr__(self, key, value):
		if key == 'objs':
			return super(MultiObject, self).__setattr__(key, value)

		objs = map(lambda x: setattr(x, key, value), self.objs)
		return MultiObject(objs)

	def __delattr__(self, key):
		if key == 'objs':
			return super(MultiObject, self).__setattr__(key, value)

		objs = map(lambda x: delattr(x, key), self.objs)
		return MultiObject(objs)


	# overloading
	def __call__(self, *args, **kwargs):
		objs = map(lambda x: x(*args, **kwargs), self.objs)
		return MultiObject(objs)

	def __str__(self):
		return str(self.objs)

	def __repr__(self):
		return repr(self.objs)

	def __len__(self):
		return len(self.objs)

	def __dir__(self):
		return dir(self.objs)

	def __getitem__(self, index):
		return self.objs[index]


class MultiSocket(object):
	""" ZMQ multi-client for all messaging patterns"""

	def __new__(cls, name, _type='REQ', subscription='', context=None):
		# extract (name, pattern) from sockfile
		def parse(sockfile):
			folder, name = osp.split(osp.splitext(sockfile)[0])
			pattern = osp.basename(folder)
			pattern = [item[0] for item in patterns.iteritems() if item[1] == pattern][0]

			return name, pattern

		socks = glob.glob("tmp/sockets/%s/%s.sock" % (patterns[_type], name))
		socks = map(lambda x: parse(x), socks)

		socks = [Socket(i[0], i[1], subscription, context) for i in socks]

		return MultiObject(socks)
