#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

import os
import os.path as osp
import shutil

import jinja2

import pyscale
from cake.lib import recurse_up

from ..lib import PyscaleError

def new(projname):
	""" create new project from default files """

	if osp.isdir(projname):
		raise PyscaleError('Folder already exists. Aborting...')
	else:
		project = osp.join(pyscale.__path__[0], 'files', 'project')
		shutil.copytree(project, projname)


def generate(modname):
	""" generate new module """

	# go to project root
	current = os.getcwd()
	root = recurse_up(current, 'Cakefile')

	if root:
		os.chdir(root)
	else:
		raise PyscaleError('Cakefile not found')


	# create folder
	folder = 'app/%s' % modname
	if not osp.isdir(folder):
		os.makedirs(folder)

	
	# create file
	modfile = 'app/%s/main' % modname
	tplfile = osp.join(pyscale.__path__[0], 'files', 'module')

	if osp.exists(modfile):
		raise PyscaleError('Module already exists. Aborting...')
	else:
		with open(tplfile) as f:
			tpl = jinja2.Template(f.read())
			tpl = tpl.render(module=modname.title())

		with open(modfile, 'w') as f:
			f.write(tpl)
