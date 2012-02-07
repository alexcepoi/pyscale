#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-


class PyscaleError(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return self.msg


class ReqError(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __getattr__(self, key):
		return self

	def __setattr__(self, key, name):
		if key == 'msg':
			return super(ReqError, self).__setattr__(key, name)
		return self

	def __delattr__(self, key):
		if key == 'msg':
			return super(ReqError, self).__delattr__(key, name)
		return self

	def __call__(self, *args, **kwargs):
		return self

	def __str__(self):
		return '(error: %s)' % self.msg

	def __repr__(self):
		return str(self)

	def __nonzero__(self):
		return False
