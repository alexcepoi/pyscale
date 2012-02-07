#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

from pyscale.lib.module import BaseModule


class Module(BaseModule):
	""" Module Class (daemon) """

	# notifications
	def notice(self, msg):
		pass

	def alert(self, msg):
		pass

	def error(self, msg):
		pass
