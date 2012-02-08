#! /usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
	name = 'pyscale',
	version = '0.1',

	platforms = 'linux',
	license = 'GPLv3',

	url = 'https://github.com/alexcepoi/pyscale',
	download_url = 'https://github.com/alexcepoi/pyscale/zipball/master',

	description = 'General purpose Python framework for writing highly scalable applications',
	long_description = open('README.rst').read(),

	packages = ['pyscale', 'pyscale.lib', 'pyscale.tools', 'pyscale.utils', 'pyscale.utils.gevsubprocess', 'pyscale.zmq'],
	scripts = ['bin/pyscale'],
	include_package_data = True,

	author = 'Alexandru Cepoi',
	author_email = 'alex.cepoi@gmail.com',
	maintainer = 'Alexandru Cepoi',
	maintainer_email = 'alex.cepoi@gmail.com',

	install_requires = ['pyzmq', 'gevent', 'gevent_zeromq', 'cake', 'nose', 'jinja2'],
)

