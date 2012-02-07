#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

import os
import os.path as osp
import logging

class Configuration(object):
	def __init__(self, env='development'):
		self.env = os.environ.get('APP_ENV') or env
		self.root = osp.abspath('.')
	
	@property
	def log_level(self):
		if self.env == 'production':
			return logging.WARNING
		else:
			return logging.DEBUG
