import gevent
from gevent import socket
from gevent.event import Event
from gevent.queue import Queue, Empty, Full #@UnusedImport

import fcntl
import os
import sys
import errno

class PipeClosed(Exception):
    """Exception raised by :func:`Pipe.get` and :func:`Pipe.put` indicating
       the :class:`Pipe` was closed
       
    """
    pass

class Pipe(Queue):
    """A :class:`Pipe` is a :class:`gevent.queue.Queue` that can be closed."""
    
    def __init__(self, maxsize=None):
        Queue.__init__(self, maxsize)
        self._closed = Event()
        self._event_cancel = None
        
    def close(self):
        """Closes the pipe"""
        self._closed.set()
        
        # Raise PipeClosed on all waiting getters and putters
        if self.getters or self.putters:
            self._schedule_unlock()
        
    def closed(self):
        """Returns ``True`` when the pipe has been closed.
        (There might still be items available though)
        
        """
        return self._closed.is_set()
    
    def finished(self):
        """Returns ``True`` when the pipe has been closed and is empty."""
        return self.empty() and self.closed() 
        
    def wait(self, timeout=None):
        """ Wait until the pipe is closed
        """
        self._closed.wait(timeout)
        
    def waiting(self):
        return len(self.getters)>0 or len(self.putters)>0
        
    def put(self, item, block=True, timeout=None):
        """Put an item into the pipe.

        If optional arg *block* is true and *timeout* is ``None`` (the default),
        block if necessary until a free slot is available. If *timeout* is
        a positive number, it blocks at most *timeout* seconds and raises
        the :class:`Full` exception if no free slot was available within that time.
        Otherwise (*block* is false), put an item on the pipe if a free slot
        is immediately available, else raise the :class:`Full` exception (*timeout*
        is ignored in that case).
        
        :raises: :class:`PipeClosed` if the pipe is closed
        
        """
        if self.closed():
            raise PipeClosed
        
        Queue.put(self, item, block, timeout)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the pipe.

        If optional args *block* is true and *timeout* is ``None`` (the default),
        block if necessary until an item is available. If *timeout* is a positive number,
        it blocks at most *timeout* seconds and raises the :class:`Empty` exception
        if no item was available within that time. Otherwise (*block* is false), return
        an item if one is immediately available, else raise the :class:`Empty` exception
        (*timeout* is ignored in that case).

        :raises: :class:`PipeClosed` if the pipe is closed
        
        """
        if self.finished():
            raise PipeClosed
        
        return Queue.get(self, block, timeout)
    
    def _unlock(self):
        #if self.finished():
        if self.closed():
            while self.getters:
                getter = self.getters.pop()
                if getter:
                    getter.throw(PipeClosed)

            while self.putters:
                putter = self.putters.pop()
                if putter:
                    putter.throw(PipeClosed)
                        
        Queue._unlock(self)

    def next(self):
        """Iterate over the items in the pipe, until the pipe is empty and closed."""
        try:
            return self.get()

        except PipeClosed:
            raise StopIteration

def pipe_to_file(pipe, file):
    """Copy items received from *pipe* to *file*"""
    if file.closed:
        return
    
    fcntl.fcntl(file, fcntl.F_SETFL, os.O_NONBLOCK)

    fno = file.fileno()

    try: 
        socket.wait_write(fno)
    except IOError, ex:
        if ex[0] != errno.EPERM:
            raise

        sys.exc_clear()
        use_wait = False
    else:
        use_wait = True

    for chunk in pipe:
        while chunk:
            try:
                written = os.write(fno, chunk)
                chunk = chunk[written:]

            except IOError, ex:
                if ex[0] != errno.EAGAIN:
                    raise
                
                sys.exc_clear()
                
            except OSError, ex:
                if not file.closed:
                    raise
                
                sys.exc_clear()
                pipe.close()
                return
                
            if use_wait: 
                socket.wait_write(fno)
            else:
                gevent.sleep(0)

    file.close()

def file_to_pipe(file, pipe, chunksize=-1):
    """Copy contents of *file* to *pipe*. *chunksize* is passed on to file.read()
    """
    if file.closed:
        pipe.close()
        return
    
    fcntl.fcntl(file, fcntl.F_SETFL, os.O_NONBLOCK)

    fno = file.fileno()
    use_wait = True
    
    while True:
        try:
            chunk = file.read(chunksize)
            if not chunk:
                break
            pipe.put(chunk)

        except IOError, ex:
            if ex[0] != errno.EAGAIN:
                raise
        
            sys.exc_clear()
       
        try: 
            if use_wait:
                socket.wait_read(fno)
        except IOError, ex:
            if ex[0] != errno.EPERM:
                raise

            sys.exc_clear()
            use_wait = False
            
        if not use_wait:
            gevent.sleep(0)

    file.close()
    pipe.close()
        
__all__ = ['Pipe', 'pipe_to_file', 'file_to_pipe', 'PipeClosed', 'Empty', 'Full']
