import time
import random
import threading

from monitor.monitor_meta import MonitorBase, hooks
from monitor.main import event_loop, send_exit
from monitor.main import rank, pp

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
        pass

    def get(self):
        while not self.buff:
            pp('waiting on not_empty')
            sleep()
            self.not_empty.wait()
        sleep()
        element = self.buff.pop()
        sleep()
        self.not_full.signal()
        sleep()
        return element

b1 = Buffer()
b2 = Buffer()

def producer():
    for i in range(10):
        pp('putting in', i)
        b1.put(i)
        sleep()

# def broker():
#     while True:
#         e = b1.get()
#         sleep()
#         b2.put(e)
#         sleep()

def consumer():
    while True:
        # pp('about to get')
        pp('got', b1.get())
        sleep()

# TODO: minimize event_loop boilerplate
pp('starting event loop thread')
event_loop_thread = threading.Thread(target=event_loop, args=(hooks,))
event_loop_thread.start()

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
else:
    pp('starting consumer')
    consumer()

send_exit()
event_loop_thread.join()
