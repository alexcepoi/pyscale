#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import logging.handlers
import traceback


class MyFormatter(logging.Formatter):
	def format(self, record):
		record.fname = "[%s:%s]" % (record.filename, record.lineno)
		return logging.Formatter.format(self, record)


EXCEPTION_PREFIX = '   =>  '

def log_exception(msg=None):
	""" Custom exception log helper """
	if msg is None:
		msg = traceback.format_exc()
	
	lines = msg.split('\n')
	lines = [ '%s%s' % (EXCEPTION_PREFIX, line) for line in lines if line]
	msg = '\n' + '\n'.join(lines) + '\n'

	logging.log(75, '\n%s' % msg)

def log_status(msg):
	""" Always log regardless of level """
	logging.log(100, msg)


def config_logger(stream=sys.stdout, level=logging.DEBUG):
	logger = logging.getLogger()
	logger.setLevel(level)


	# handler
	if stream in [sys.stdout, sys.stderr]:
		handler = logging.StreamHandler(stream)
	else:
		handler = logging.handlers.RotatingFileHandler(stream, maxBytes=409600, backupCount=3)
	logger.addHandler(handler)

	# formatter
	formatter = MyFormatter(
		fmt = '%(asctime)s %(levelname)-8s %(fname)-20s  %(message)s',
		datefmt = '%b %d %Y %H:%M:%S',
	)
	handler.setFormatter(formatter)
	
	# custom levels
	logging.addLevelName(75, 'EXCEPT')
	logging.exception = log_exception

	logging.addLevelName(100, 'STATUS')
	logging.status = log_status


# test
if __name__ == '__main__':
	config_logger()

	logging.warning('test')
	logging.info('test')
	logging.debug('test')
	logging.error('test')
	
	try: err_var
	except Exception as ex:
		logging.exception()

	logging.status('test')
