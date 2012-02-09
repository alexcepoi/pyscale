#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path as osp
import pydoc
import shutil

import jinja2

import pyscale
from cake.lib import recurse_up
from cake.color import puts, fore

from ..lib import PyscaleError


def find_project():
	current = os.getcwd()
	return recurse_up(current, 'Cakefile')


def new(projname):
	""" create new project from default files """

	# find project template
	if find_project() != False:
		raise PyscaleError('Inside another project. Aborting...')
	elif osp.isdir(projname):
		raise PyscaleError('Folder already exists. Aborting...')
	else:
		project = osp.join(pyscale.__path__[0], 'files', 'project')

	# copy project template
	def ignore(dirname, names):
		common = osp.commonprefix([project, dirname])

		puts(fore.green('   init ') + osp.join(projname, dirname[len(common)+1:]))
		return []

	shutil.copytree(project, projname, ignore=ignore)


def generate(modname):
	""" generate new module """

	# check for valid name
	if modname.lower() in pydoc.Helper.keywords.keys():
		raise PyscaleError('%s is a Python keyword.' % repr(modname.lower()))

	# go to project root
	root = find_project()
	if root != False:
		os.chdir(root)
	else:
		raise PyscaleError('Pyscale project not found (missing Cakefile?)')


	# create folder
	folder = 'app/%s' % modname
	if osp.isdir(folder):
		puts(fore.yellow(' exists ') + folder)
	else:
		puts(fore.green('  mkdir ') + folder)
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

		puts(fore.green(' create ') + modfile)
		with open(modfile, 'w') as f:
			f.write(tpl)
