#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import traceback

import gevent
import gevent.pool
import gevent.queue
from gevent_zeromq import zmq

# python is great
import types
types.MethodWrapper = type(object().__getattribute__)

# library
from .common import format_method
from ..lib import PyscaleError, ReqError

# let zmq select jsonapi (for performance)
from zmq.utils import jsonapi
if jsonapi.jsonmod is None:
	raise ImportError('jsonlib{1,2}, json or simplejson library is required.')


class RpcWorker(gevent.Greenlet):
	""" zmq RPC Worker """

	def __init__(self, server):
		super(RpcWorker, self).__init__()

		self.server = server

	def _run(self):
		self.sock = self.server.context.socket(zmq.REQ)
		self.sock.connect("inproc://workers")

		self.sock.send('READY')

		# request loop
		while True:
			self._ready = True
			envelope, req = self.recv()
			self._ready = False

			if req is None:
				# kill me if you dare
				break
			else:
				# love me, i don't care
				try: reply = self.handle(req)
				except ReqError as e:
					self.send(envelope, e.msg, error=True)
				else:
					self.send(envelope, reply)

	def handle(self, requests):
		logging.debug("[zmq] <~ self%s" % ''.join([format_method(*req) for req in requests]))

		# loop request chain
		module = self.server.module
		result = module
		parsed = module.name

		for method, args, kwargs in requests:
			# parse request
			try:
				if method == '__dir':
					result = dir(result, *args, **kwargs)
				elif method == '__len':
					result = len(result, *args, **kwargs)
				elif method == '__set':
					result = setattr(result, *args, **kwargs)
				elif method == '__del':
					result = delattr(result, *args, **kwargs)
				else:
					try: result = getattr(result, method)
					except AttributeError:
						parsed += '.' + method
						raise
					else:
						parsed += format_method(method, args, kwargs)
						result = result(*args, **kwargs)
			except AttributeError:
				msg = 'AttributeError: \'%s\'' % parsed
				logging.error(msg)
				module.alert(msg)
				raise ReqError(parsed)
			except PyscaleError as ex:
				msg = ''.join(traceback.format_exception_only(type(ex), ex)).strip()
				logging.error(msg)
				module.alert(msg)
				raise ReqError(parsed)
			except Exception as ex:
				msg = traceback.format_exc()
				logging.exception(msg)
				module.error(msg)
				raise ReqError(parsed)

		return result

	def recv(self):
		envelope = self.sock.recv_multipart()
		msg = jsonapi.loads(envelope.pop())

		return envelope, msg

	def send(self, envelope, msg, error=False):
		if error:
			msg = jsonapi.dumps({'error': msg})
		else:
			# FIXME: exception handling should be better done
			# but there are too many json libraries out there
			try: msg = jsonapi.dumps({'result': msg})
			except Exception:
				msg = jsonapi.dumps({'proxy': repr(msg)})

		envelope.append(msg)
		return self.sock.send_multipart(envelope)


class RpcServer(object):
	""" zmq RPC Server featuring Router-to-Router broker (LRU queue) """

	def __init__(self, module, address, ready_workers=1, max_workers=float('inf'), context=None):
		self.module  = module
		self.address = address
		self.context = context or zmq.Context.instance()

		self.ready_workers = ready_workers
		self.max_workers   = max_workers

		self.workers = gevent.pool.Group()

	def spawn_worker(self):
		if len(self.workers) < self.max_workers:
			# we keep track of workers internally
			worker = RpcWorker(self)
			self.workers.start(worker)

			# but also register them as module jobs
			self.module.jobs.add(worker)

	@property
	def status(self):
		# for debugging purposes
		return [getattr(worker, '_ready', None) for worker in self.workers]

	def run(self):
		# spawn workers
		for i in xrange(self.ready_workers):
			self.spawn_worker()

		# create broker
		clients = self.context.socket(zmq.XREP)
		clients.bind(self.address)

		workers = self.context.socket(zmq.XREP)
		workers.bind("inproc://workers")

		# XXX: zmq devices don't work with gevent
		# zmq.device(zmq.QUEUE, clients, workers)
		self.broker = RpcBroker(clients, workers, self)


class RpcBroker(object):
	""" zmq gevent-compatible LRU Queue Device """

	def __init__(self, clients, workers, server):
		self.clients = clients
		self.workers = workers
		self.server  = server

		# here we keep track of idle workers
		self.ready = gevent.queue.Queue()

		# spawn jobs that redirect requests from clients to workers and back
		self.jobs = gevent.pool.Group()
		fwd = self.jobs.spawn(self.forward)
		bwd = self.jobs.spawn(self.backward)

		self.server.module.jobs.add(fwd)
		self.server.module.jobs.add(bwd)

	def forward(self):
		while True:
			# client request: [client][empty][req]
			msg = self.clients.recv_multipart()

			# assertions
			assert msg[1] == ''

			# spawn additional worker if none available
			if self.ready.empty():
				self.server.spawn_worker()

			# get a ready worker and pass request
			worker = self.ready.get()
			self.workers.send_multipart([worker, ''] + msg)

	def backward(self):
		while True:
			# worker response: [worker][empty][ready] or [worker][empty][client][empty][reply]
			msg = self.workers.recv_multipart()

			# assertions
			assert msg[1] == ''
			assert len(msg) == 3 or (len(msg) == 5 and msg[3] == '')

			# route reply back to client
			if msg[2] != 'READY':
				self.clients.send_multipart(msg[2:])

			# decide worker fate
			worker = msg[0]

			if self.ready.qsize() >= max(self.server.ready_workers, 1):
				# kill worker (send None as request)
				self.workers.send_multipart([worker, '', jsonapi.dumps(None)])
			else:
				# keep worker (mark as ready)
				self.ready.put(worker)
