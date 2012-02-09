General purpose Python framework for writing highly scalable applications.

About
---------------------------------------------------
A typical application consists of several modules. Each module has its own
process, stores a pidfile in 'tmp/pids', and has a logfile in 'logs'.

A RPC protocol is implemented on top of zeromq in order to allow for
inter-module communication. Modules have an auto-adjustable number of workers
in order to cope with a high number of requests. These rpc requests will block
until that module becomes available.
Read more about zeromq at http://zguide.zeromq.org/

Each module consists of several gevent greenlets. A basic module will already
contain a few greenlets that handle incoming rpc requests. You can spawn
additional greenlets for your own needs.
Read more about gevent at http://www.gevent.org/


Tasks
---------------------------------------------------
You can manage and debug your modules using built-in tasks. Type 'cake' at a
bash prompt when inside your project to see available tasks and what they do.
You can also define your own taks.

Commands
---------------------------------------------------
To create a new project:

::

  $ pyscale new <name>

To generate a new module:

::

  $ pyscale generate <name>

To start, stop, debug, view logs and more check out available cake tasks:

::

  $ cake
  $ cake start
  $ cake stop
  $ cake status
  $ cake log
  $ cake console

Usage
---------------------------------------------------
To execute an rpc request on another module:

::

  self.sock('modname').method(*args, **kwargs)

You can also use properties, and chain requests:

::

  self.sock('modname').prop.method()

You can also issue requests on all available modules:

::

  self.multisock('*').method()


To spawn another greenlet in a module either use the 'job' decorator or:

::

  self.jobs.spawn(func)

To debug your application use logs and the console.

Requirements
---------------------------------------------------
System Dependencies:
 * zeromq
 * atd

Python Dependencies:
 * pyzmq
 * gevent
 * gevent_zeromq
 * cake
 * argparse
 * jinja2
 * nose
