#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import glob
import os
import os.path as osp

import code
import signal

from cake.lib import puts
from cake.color import fore

from ..zmq import Socket, MultiSocket


def api(modules):
	# ensure iterable
	if isinstance(modules, Socket):
		modules = [modules]
	
	# iterate list
	for module in modules:
		puts('= ' + fore.green(module.name))
		for obj in module.help():
			if isinstance(obj, list):
				# method
				puts('  * ' + fore.yellow(obj[0]) + ' ' + fore.white(obj[1]))
				if obj[2]:
					puts('    ' + fore.blue(obj[2]))

def reinit(namespace, info=True):
	# clean sockets
	for sock in namespace.sockets:
		delattr(namespace, sock.name)

	# create sockets
	namespace.all = MultiSocket('*')
	namespace.sockets = namespace.all.objs

	for sock in namespace.sockets:
		setattr(namespace, sock.name, sock)
	
	# display info
	if info:
		puts('=== ' + fore.blue('PyScale Console') + ' =', padding='=')
		for sock in ['all'] + sorted([x.name for x in namespace.sockets]):
			puts('    ' + fore.green('>>> ') + sock)
		puts('=====================', padding='=')


def main(namespace):
	# parse args
	command = ' '.join(sys.argv[1:])

	if not command:
		# console (interactive)
		try: reinit(namespace)
		except KeyboardInterrupt:
			pass

		# ignore Ctrl-C (interferes with gevent)
		signal.signal(signal.SIGINT, lambda signum, frame: None)
	else:
		# call (non-interactive)
		reinit(namespace, info=False)

		console = code.InteractiveConsole(locals())
		console.runsource(command)
