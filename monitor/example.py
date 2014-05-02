import time
import random
import threading

from monitor.monitor_meta import MonitorBase, hooks
from monitor.main import event_loop, send_exit
from monitor.main import rank

def sleep():
    time.sleep(random.random() + 0.1)

class Buffer(MonitorBase):
    def __init__(self):
        self.buff = self.shared([])
        self.max_length = 4
        self.not_full = self.condition()
        self.not_empty = self.condition()

    def put(self, element):
        while len(self.buff) == self.max_length:
            print('waiting on not_full')
            sleep()
            self.not_full.wait()
        sleep()
        self.buff.insert(0, element)
        sleep()
        self.not_empty.signal()

    def get(self):
        print('inside get')
        while not self.buff:
            print('waiting on not_empty')
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
    for i in range(100):
        print('putting in', i)
        b1.put(i)
        sleep()

def broker():
    while True:
        e = b1.get()
        sleep()
        b2.put(e)
        sleep()

def consumer():
    while True:
        print('about to get')
        print('got', b1.get(e))
        sleep()

# TODO: minimize event_loop boilerplate
print('starting event loop thread')
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
    print('starting producer')
    producer()
else:
    print('starting consumer')
    consumer()

send_exit()
event_loop_thread.join()
