#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

import re

from cake.lib import puts
from cake.color import fore, style

from ..lib.log import EXCEPTION_PREFIX

def println(line):
	# blank line
	if re.match(r'\s*$', line):
		return puts(line)

	# logfile header
	mobj = re.match(r'==> (.*) <==$', line)
	if mobj:
		return puts(style.bright(fore.black('==> ') + fore.white(mobj.group(1)) + fore.black(' <==')))
	
	# exception line
	if re.match(EXCEPTION_PREFIX, line):
		return puts(fore.red(line))

	# standard log line
	basic = r'(.*?\s+)'

	date = basic*3
	time = basic
	type = basic
	file = '(\[.*?\s+)\])'

	mobj = re.match(basic*6 + r'(.*)', line)
	if not mobj:
		# non-conventional line
		return puts(line)
	else:
		groups = list(mobj.groups())

		groups.insert(0, str(fore.cyan))
		groups.insert(4, str(fore.blue))
		groups.insert(6, str(style.bright))
		groups.insert(8, str(style.reset_all))
		groups.insert(9, str(fore.cyan))
		groups.insert(11, str(style.reset_all))

		for idx, string in enumerate(groups):
			string = re.sub(r'(STATUS)', fore.white(r'\1'), string)
			string = re.sub(r'(DEBUG)', fore.white(r'\1'), string)
			string = re.sub(r'(INFO)', fore.green(r'\1'), string)
			string = re.sub(r'(WARNING)', fore.yellow(r'\1'), string)
			string = re.sub(r'(ERROR)', fore.red(r'\1'), string)
			string = re.sub(r'(EXCEPT)', fore.red(r'\1'), string)

			groups[idx] = string


		groups[-1] = re.sub(r'\[', fore.cyan(r'['), groups[-1])
		groups[-1] = re.sub(r'\]', fore.cyan(r']'), groups[-1])

		groups[-1] = re.sub(r'~>', fore.blue(r'~>'), groups[-1])
		groups[-1] = re.sub(r'<~', fore.yellow(r'<~'), groups[-1])

		groups[-1] = re.sub(r'\(', fore.cyan(r'('), groups[-1])
		groups[-1] = re.sub(r'\)', fore.cyan(r')'), groups[-1])

		groups[-1] = re.sub(r"'", fore.cyan(r"'"), groups[-1])
		groups[-1] = re.sub(r'"', fore.cyan(r'"'), groups[-1])

		return puts(''.join(groups))


def main():
	try:
		while True:
			println(raw_input())
	except KeyboardInterrupt:
		pass
