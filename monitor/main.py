from collections import namedtuple
import threading
import time
import sys

import monitor.config as config
if config.backend == 'mpi':
    import monitor.mpi_wrapper as comm
elif config.backend == 'zmq':
    import monitor.zmq_mpi as comm

def pp(*args):
    print('{}:'.format(rank), *args)
    sys.stdout.flush()

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

rank = comm.rank
size = comm.size
clock = LamportClock()

class Message:
    def __init__(self, type, timestamp, name, data=None):
        self.type = type
        self.timestamp = timestamp
        self.name = name
        self.data = data

QueueElement = namedtuple('QueueElement', ['timestamp', 'rank'])

def event_loop(hooks={}):
    exits = [False] * size

    while True:
        source, message = comm.recv()
        clock.update(message.timestamp)

        if message.type == 'exit':
            exits[source] = True
            if all(exits):
                pp(' ||| exiting event loop')
                return
        elif message.type in hooks:
            handler = hooks[message.type]
            handler(source, message)
        else:
            pp('wat')

def send_exit():
    pp(' ||| sending exit to everyone')
    clock.increment()
    for i in range(size):
        comm.send(Message('exit', clock.time, ''), dest=i)
