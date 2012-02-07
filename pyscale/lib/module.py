#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

import inspect
import logging
import os
import os.path as osp
import sys

import gevent.monkey
gevent.monkey.patch_all()

import gevent.pool
from gevent_zeromq import zmq

# pyscale
from .log import config_logger
from ..zmq import Socket, MultiSocket, RpcServer

# project
from config.app import Configuration


class BaseModule(object):
	""" Basic Module Class (daemon) """

	def __init__(self, context=None):
		# app config
		self.conf = Configuration()

		# module config
		self.name = osp.basename(osp.dirname(osp.abspath(sys.argv[0])))
		self.pidfile = "tmp/pids/%s.pid" % self.name
		config_logger("logs/%s.log" % self.name, self.conf.log_level)

		# zmq context
		self.context = context or zmq.Context.instance()

		# pool of greenlets
		self.jobs = gevent.pool.Group()

		# zmq REQ/REP API
		self.rpc = RpcServer(self, "ipc://tmp/sockets/rpc/%s.sock" % self.name)
		self.rpc.run()

	def run(self):
		""" Run the current module (start greenlets) """
		# check for previous crash
		if os.access(self.pidfile, os.F_OK):
			pid = open(self.pidfile, 'r').readline()

			if osp.exists('/proc/' + pid):
				logging.warn("%s already running with pid %s" % (self.name, pid))
				return
			else:
				logging.warn("%s seems to have crashed.. deleting pidfile" % self.name)
				os.remove(self.pidfile)

		# run all jobs
		with self:
			try:
				self.jobs.join()
			except KeyboardInterrupt:
				self.jobs.kill()
				# zmq.Context.instance().term()

	def sock(self, name, _type=None):
		""" Socket convenience function """
		if _type:
			return Socket(name, _type)
		else:
			return Socket(name)

	def multisock(self, name, _type=None):
		""" MultiSocket convenince function """
		if _type:
			return MultiSocket(name, _type)
		else:
			return MultiSocket(name)

	def __enter__(self):
		logging.status("%s started" % self.name)

		# create pidfile
		open(self.pidfile, 'w').write(str(os.getpid()))

		return self

	def __exit__(self, type, value, traceback):
		logging.status("%s stopped" % self.name)

		# remove pidfile
		os.remove(self.pidfile)

		return False

	def help(self):
		methods = []
		for name in dir(self):
			obj = getattr(self, name)
			if inspect.ismethod(obj):
				if getattr(obj, 'api', False):
					# extract specs
					spec = inspect.getargspec(obj)

					# extract docstring
					doc = inspect.getdoc(obj)
					if doc: doc = doc.strip()

					methods.append((name, inspect.formatargspec(*spec), doc))
			else:
				if not name.startswith('_'):
					methods.append(name)
		return methods

	# notifications
	def notice(self, msg):
		pass

	def alert(self, msg):
		pass

	def error(self, msg):
		pass
