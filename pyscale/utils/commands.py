#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess as sbp
import shlex
import os
import pty

import gevent
from gevent.event import Event

from .gevsubprocess import GPopen
from ..lib.errors import PyscaleError


def command(cmd, exception=PyscaleError, sudo=False, shell=False):
	# fix unicode stuff
	cmd = str(cmd)

	# parse args
	if sudo:
		# XXX: --session-command vs --command(-c)
		# session-command seems to be better but is only available on CentOS & Co.
		# cmd = "su -c '%s'" % cmd
		cmd = "sudo -n bash -c '%s'" % cmd
	if not shell:
		cmd = shlex.split(cmd)

	# execute
	slave = None
	if sudo:
		# give su a pty
		master, slave = pty.openpty()
	
	out, err = GPopen(cmd, stdin=slave, stdout=sbp.PIPE, stderr = sbp.PIPE, shell=shell).communicate()

	# handle errors
	if not out and err:
		if exception:
			raise exception(err)
		else:
			print err

	return out


def execute(cmd, env={}):
	args = shlex.split(cmd)

	if env:
		environ = os.environ.copy()
		environ.update(env)
		os.execvpe(args[0], args,  environ)
	else:
		os.execvp(args[0], args)


# main
if __name__ == '__main__':
	print command('ls', sudo=True, shell=False)
