#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

import sys
import re
import glob
import operator
import os
import os.path as osp
import subprocess as sbp
import nose
import fnmatch

from cake.lib import task, path, puts
from cake.color import fore
from cake.errors import CakeError

from ..zmq import Socket
from ..utils import command, execute
from ..lib import PyscaleError


# == Helpers ==
def python():
	return  "%s -uB" % sys.executable

def shell(cmd, exception=None):
	return command(cmd, shell=True, exception=exception)

def all_modules(regex='*'):
	mods = []
	for path in glob.iglob('app/%s/main' % regex):
		module = osp.basename(osp.dirname(path))
		mods.append((module, path))
	return mods

def running_modules(regex='*'):
	mods = []
	for pidfile in glob.iglob('tmp/pids/%s.pid' % regex):
		module = osp.splitext(osp.basename(pidfile))[0]
		pid = open(pidfile).read()
		mods.append((module, pid, pidfile))
	return mods


# == Module Management ==
@task('Starting Modules')
def start(module='*', env='development'):
	""" Start [module] """

	os.environ['APP_ENV'] = env

	for module, path in all_modules(module):
		try:
			cmd = "PYTHONPATH=. %s %s &>> logs/%s.log" % (python(), path, module)
			shell("echo '%s' | at now" % cmd, exception=PyscaleError)
		except PyscaleError as e:
			msg = str(e).strip('\n')
			msg = ' '.join(msg.split('\n'))

			puts(fore.cyan("%-10s" % module) + "(%s) scheduled" % msg)

@task('Stopping Modules')
def stop(module='*'):
	""" Stop [module] """

	for module, pid, pidfile in running_modules(module):
		shell('kill %s' % pid)
		shell('rm -f %s' % pidfile)
		shell('rm -f tmp/sockets/*/%s.sock' % module)

		puts(fore.cyan("%-10s" % module) + "(pid: %s) stopped" % fore.red(pid))

@task
def restart(module='*', env='development'):
	""" Restart [module] """

	stop(module)
	start(module, env)

@task
def clean(module='*'):
	""" Clean temp files """
	shell('rm -f logs/%s.log' % module)
	shell('rm -f tmp/pids/%s.pid' % module)
	shell('rm -f tmp/sockets/*/%s.sock' % module)

@task
def reset(module='*', env='development'):
	""" Restart [module] and clean up temp files """
	stop(module)
	clean(module)
	start(module, env)

@task
def kill(signal=9):
	""" Kill zombie (unregistered) modules """
	zombies = []
	pids = set(m[1] for m in running_modules())

	for line in shell('ps -e --no-headers -o pid,command').split('\n'):
		try: pid, name = re.match(r'\s*(\d+)\s+(.+)$', line).groups()
		except AttributeError: continue

		mob = re.search(r'app/(.*?)/main', name)
		if mob and pid not in pids:
			zombies.append((mob.group(1), pid))

	if not zombies:
		puts(fore.green('No zombies detected'))
	else:
		puts(fore.green('Killing %d zombie modules' % len(zombies)))
		for name, pid in zombies:
			puts(' * Killing %-10s (pid: %s) ...' % (fore.cyan(name), fore.red(pid)))

			try: shell('kill -s %s %s' % (signal, pid), exception=RuntimeError)
			except RuntimeError as e:
				puts(fore.magenta('   Error: ') + e.args[0])

@task
def status():
	""" View running modules """
	for module, pid, pidfile in running_modules():
		if not osp.exists("/proc/%s" % pid):
			puts(fore.red("%s (pid %s) crashed" % (module, pid)))

	pids = map(operator.itemgetter(1), running_modules())
	if pids:
		pscomm = "ps -p %s -o pid,user,command:50,pcpu,pmem,vsz,nice,start,time" % ','.join(pids)
		psinfo = shell(pscomm).split('\n')

		if len(psinfo) > 1 and psinfo[1]:
			puts(fore.green(psinfo[0]))

			for ps in psinfo[1:]:
				color = lambda mobj: re.sub(mobj.group(1), fore.cyan(mobj.group(1)), mobj.group(0))
				puts(re.sub('app/(.*?)/main', color, ps))

@task
def log(module='*', lines=10):
	""" View log for [module] """

	if not glob.glob('logs/*.log'):
		raise CakeError('No logfiles found')
	else:
		try: sbp.call("tail -n %s -f logs/%s.log | PYTHONPATH=. %s tools/logger" % (lines, module, python()), shell=True)
		except KeyboardInterrupt: pass


# == Debugging ==
@task
def run(what, *args):
	""" Run from project root """

	what = osp.join(path.current, what)
	args = ' '.join([what] + list(args))

	execute("%s %s" % (python(), args), env={'PYTHONPATH': '.'})

@task
def debug(what, *args):
	""" Run interactively from project root"""

	what = osp.join(path.current, what)
	args = ' '.join([what] + list(args))

	execute("%s -i %s" % (python(), args), env={'PYTHONPATH': '.'})

@task
def console(*args, **kwargs):
	""" Debugging Console """

	argv = list(args) + ['%s=%s' % (key, val) for key, val in kwargs.items()]
	if len(argv) > 1:
		raise CakeError('console() can receive 0 or 1 arguments')

	if argv:
		run('tools/console %s' % ' '.join(argv))
	else:
		debug('tools/console')

@task
def test(pattern='*'):
	""" Run Unit Tests """
	# recurse folder for tests
	files = []
	for root, dirs, fnames in os.walk('tests'):
		for fname in fnmatch.filter(fnames, '%s_tests.py' % pattern):
			files.append(osp.join(root, fname))

	# run tests
	nose.main(argv=[''] + files)
