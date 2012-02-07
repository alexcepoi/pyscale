import gevent
from gevent import hub

from pipe import Pipe, file_to_pipe, pipe_to_file

import subprocess
import errno
import sys

PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT

class GPopen(subprocess.Popen):
    """Like :class:`subprocess.Popen`, but communicates with child using 
       :class:`gevsubprocess.pipe.Pipe` objects instead of file objects
    """
    def __init__(self, args, **kwds):
        subprocess.Popen.__init__(self, args, **kwds)

        # Replace self.std(in|out|err) with pipes
        self._greenlets = []
        
        for name in ('stdin','stdout','stderr'):
            file = getattr(self, name)
            if file:
                pipe = Pipe()
                setattr(self, name, pipe)
                
                if name=='stdin':
                    gl = gevent.spawn(pipe_to_file, pipe, file)
                else:
                    gl = gevent.spawn(file_to_pipe, file, pipe)
                    
                self._greenlets.append(gl)
                   
    def communicate(self, input=None):
        if self.stdin:
            if input:
                self.stdin.put(input)
            self.stdin.close()
            
        if self.stdout:
            self.stdout.wait()
            stdout = ''.join(line for line in self.stdout)
        else:
            stdout = None
            
        if self.stderr:
            self.stderr.wait()
            stderr = ''.join(line for line in self.stderr)
        else:
            stderr = None

        self.wait()
        return (stdout, stderr)

    def wait(self, check_interval=0.1):
        # non-blocking, use hub.sleep
        try:
            while True:
                status = self.poll()
                if status is not None:
                    return status
                hub.sleep(check_interval)

        except OSError, e:
            if e.errno == errno.ECHILD:
                # no child process, this happens if the child process
                # already died and has been cleaned up
                return -1

        finally:
            if self._greenlets:
                if sys.exc_info()[0] is None:
                    gevent.joinall(self._greenlets)
                else:
                    gevent.killall(self._greenlets)
                    
                self._greenlets = None
        
