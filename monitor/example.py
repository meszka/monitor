import time
import random
import threading

from monitor.monitor_meta import MonitorBase
from monitor.main import rank, size, pp
from monitor.util import event_loop_thread

def sleep():
    time.sleep(random.random() * 0.1 + 0.1)

class Buffer(MonitorBase):
    def __init__(self):
        self.buff = self.shared([])
        self.max_length = 2
        self.not_full = self.condition()
        # pp(self.not_full.name, 'is', id(self.not_full))
        self.not_empty = self.condition()
        # pp(self.not_empty.name, 'is', id(self.not_empty))

    def put(self, element):
        while len(self.buff) == self.max_length:
            pp('waiting on not_full')
            sleep()
            self.not_full.wait()
        sleep()
        self.buff.insert(0, element)
        sleep()
        self.not_empty.signal()
        pp('signalled not_empty')

    def get(self):
        while not self.buff:
            pp('waiting on not_empty')
            sleep()
            self.not_empty.wait()
        sleep()
        # pp('about to pop')
        element = self.buff.pop()
        # pp('popped')
        sleep()
        # pp('signalling not_full')
        self.not_full.signal()
        pp('signalled not_full')
        sleep()
        return element

b1 = Buffer()
b2 = Buffer()

MAX = 5

def producer():
    for i in range(MAX + 1):
        pp('putting in', i)
        b1.put(i)
        sleep()
    pp('DONE')

def broker():
    e = None
    while e != MAX:
        e = b1.get()
        sleep()
        pp('delivering', e)
        b2.put(e)
        sleep()
    pp('DONE')

def consumer():
    e = None
    while e != MAX:
        # pp('about to get')
        e = b2.get()
        pp('got', e)
        sleep()
    pp('DONE')

with event_loop_thread():
    # if rank == 1:
    #     producer()
    # elif rank == 2:
    #     broker()
    # elif rank == 3:
    #     consumer()
    # elif rank == 4:
    #     consumer()
    if rank == 0:
        pp('starting producer')
        producer()
    elif rank == 1:
        pp('starting broker')
        broker()
    else:
        pp('starting consumer')
        consumer()
