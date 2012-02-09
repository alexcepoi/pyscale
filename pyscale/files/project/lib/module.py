#! /usr/bin/env python
# -*- coding: utf-8 -*-

from pyscale.lib.module import BaseModule, job


class Module(BaseModule):
	""" Module Class (daemon) """

	# notifications
	def notice(self, msg):
		pass

	def alert(self, msg):
		pass

	def error(self, msg):
		pass
