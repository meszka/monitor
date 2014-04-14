from mpi4py import MPI
from collections import namedtuple
from enum import IntEnum
import threading
import time

def pp(*args):
    print('{}:'.format(rank), *args)

class LamportClock:
    def __init__(self):
        self.time = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.time += 1

    def update(self, other_time):
        with self.lock:
            self.time = max(self.time, other_time) + 1

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
clock = LamportClock()

Message = namedtuple('Message', ['type', 'timestamp', 'name'])
QueueElement = namedtuple('QueueElement', ['timestamp', 'rank'])

Tag = IntEnum('Tag', 'acquire_request acquire_reply release wait signal pop')

# TODO: this should be in MonitorBase along with mutexes and conditionals
def event_loop(hooks={}):
    while True:
        status = MPI.Status()
        # pp('event loop recv...')
        message = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        # pp('done recv')
        source = status.Get_source()
        # pp('done get source')
        # pp('type: {}'.format(message.type))
        # pp('source: {}'.format(source))
        # pp('received sth: {}'.format(message))
        clock.update(message.timestamp)
        # pp('done clock update')

        if message.type == 'exit':
            pp(' ||| exiting event loop')
            return
        elif message.type in hooks:
            handler = hooks[message.type]
            handler(source, message)
        else:
            pp('wat')

def send_exit():
    pp(' EXIT ')
    comm.barrier()
    pp(' ||| sending exit to event loop')
    for i in range(size):
        comm.send(Message('exit', 0, ''), dest=i)
    # comm.send(Message('exit', 0, ''), dest=rank)
