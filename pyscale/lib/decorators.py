#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

def api(method):
	""" Basic decorator for module API methods """
	method.api = True
	return method
