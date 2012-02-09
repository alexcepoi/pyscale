#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import glob
import os.path as osp
from contextlib import contextmanager

from gevent_zeromq import zmq
from .common import patterns, format_method
from ..lib import ReqError


class ProxySocket(object):
	reserved = ['_obj', '_parsed', '_key', '_value', '_attr', '_str']

	def __init__(self, obj, parsed=[]):
		self._obj = obj
		self._parsed = []

		self._str = None

	def __getattr__(self, key):
		self._key = key
		self._attr = 'get'
		return self._rpc()

	def __setattr__(self, key, value):
		if key in self.reserved:
			return super(ProxySocket, self).__setattr__(key, value)

		self._key = key
		self._value = value
		self._attr = 'set'
		return self._rpc()

	def __delattr__(self, key):
		if key in self.reserved:
			return super(ProxySocket, self).__delattr__(key)

		self._key = key
		self._attr = 'del'
		return self._rpc()

	def __call__(self, *args, **kwargs):
		self._attr = 'call'
		return self._rpc(*args, **kwargs)

	def _rpc(self, *args, **kwargs):
		# prepare request
		if self._attr is 'call':
			blob =  ('__call__', args, kwargs)
		elif self._attr is 'get':
			blob = ('__getattribute__', [self._key], {})
		elif self._attr is 'set':
			blob = ('__set', [self._key, self._value], {})
		elif self._attr is 'del':
			blob = ('__del', [self._key], {})
		elif self._attr is 'dir':
			blob = ('__dir', [], {})
		elif self._attr is 'len':
			blob = ('__len', [], {})
		else:
			raise ValueError('Unknown value for attr: %s' % self.attr)

		self._parsed.append(blob)

		# make request
		if self._obj._sock is not None:
			reply = self._obj._send(self._parsed)
		else:
			with self._obj:
				reply = self._obj._send(self._parsed)

		# parse response
		if 'error' in reply:
			return ReqError(reply['error'])
		elif 'proxy' in reply:
			self._str = '(proxy: %s)' % reply['proxy']
			return self
		elif 'result' in reply:
			return reply['result']
		else:
			raise ValueError('reply must be result, proxy or error')

		return result

	def __str__(self):
		if self._str is None:
			return super(ProxySocket, self).__str__()

		return str(self._str)

	def __repr__(self):
		if self._str is None:
			return super(ProxySocket, self).__repr__()

		return str(self._str)

	def __dir__(self):
		self._attr = 'dir'
		return self._rpc()

	def __len__(self):
		self._attr = 'len'
		return self._rpc()


class Socket(object):
	""" ZMQ client for all messaging patterns """
	reserved = ['_name', '_type', '_pattern', '_subscription', '_context', '_sock_file', '_sock']

	def __init__(self, name, _type='REQ', subscription='', context=None):
		self._name          = name
		self._type          = _type.upper()
		self._pattern       = patterns[self._type]
		self._subscription  = subscription
		self._context       = context or zmq.Context.instance()

		self._sock_file = "ipc://tmp/sockets/%s/%s.sock" % (self._pattern, self._name)
		self._sock = None

	def _open(self):
		if self._sock is not None:
			return

		self._sock = self._context.socket(getattr(zmq, self._type))
		self._sock.connect(self._sock_file)

		if self._pattern == 'pub':
			self._sock.setsockopt(zmq.SUBSCRIBE, self._subscription)

		return self

	def _close(self):
		if self._sock is not None:
			self._sock.close()
			self._sock = None

		return self

	def __enter__(self):
		return self._open()

	def __exit__(self, type, value, trace):
		self._close()

	def _send(self, blob):
		self._sock.send_json(blob)
		logging.debug("[zmq] ~> %s%s" % (self._name, ''.join([format_method(*req) for req in blob])))
		return self._sock.recv_json()

	# pass to proxy
	def __getattr__(self, key):
		return getattr(ProxySocket(self), key)

	def __setattr__(self, key, value):
		if key in self.reserved:
			return super(Socket, self).__setattr__(key, value)
		else:
			return setattr(ProxySocket(self), key, value)

	def __delattr__(self, key):
		if key in self.reserved:
			return super(Socket, self).__delattr__(key)
		else:
			return delattr(ProxySocket(self), key)

	def __call__(self, *args, **kwargs):
		return ProxySocket(self).__call__(*args, **kwargs)

	def __dir__(self):
		return dir(ProxySocket(self))
