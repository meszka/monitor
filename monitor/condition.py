import threading
from mpi4py import MPI

from monitor.main import Message, QueueElement, Tag
from monitor.main import comm, rank, size, clock, pp

conditions = {}

class Condition:
    def __init__(self, mutex, name):
        self.queue = []
        self.mutex = mutex
        self.name = name
        self.signal_cond = threading.Condition()
        conditions[name] = self

    def wait(self):
        # send wait message to everyone
        clock.increment()
        message = Message('wait', clock.time, self.name)
        for i in set(range(size)) - {rank}:
            comm.send(message, dest=i, tag=Tag.wait)
            # pp('sent wait to', i)
        # release mutex
        self.mutex.release()
        # blocking recv of signal message
        # pp('waiting for signal')
        self._signal_wait()
        # pp('got signal, waiting for mutex')
        # acquire mutex
        self.mutex.acquire()

    def signal(self):
        if not self.queue:
            # pp('signal: empty queue')
            return
        # send signal to first (by timestamp) process in queue
        first = self.queue[0].rank
        clock.increment()
        message = Message('signal', clock.time, self.name)
        comm.send(message, dest=first, tag=Tag.signal)
        # pp('sent signal to', first)
        # tell everyone eles to remove that process from queue
        clock.increment()
        message = Message('pop', clock.time, self.name)
        for i in set(range(size)) - {rank, first}:
            comm.send(message, dest=first, tag=Tag.pop)
            # pp('sent pop to', i)
        self.queue.pop()

    def _signal_wait(self):
        with self.signal_cond:
            self.signal_cond.wait()

def wait_handler(source, message):
    # pp('received wait from', source)
    condition = conditions[message.name]
    condition.queue.append(QueueElement(message.timestamp, source))
    condition.queue.sort()
def signal_handler(source, message):
    # pp('received signal from', source)
    condition = conditions[message.name]
    # pp('acquiring signal_cond lock')
    with condition.signal_cond:
        # pp('acquired signal_cond lock')
        condition.signal_cond.notify()
        # pp('notified')
    # pp('handled signal')
def pop_handler(source, message):
    # pp('received pop from', source)
    condition = conditions[message.name]
    with condition.signal_cond:
        assert condition.queue[0].rank != rank
        condition.queue.pop()

condition_hooks = {
    'wait': wait_handler,
    'signal': signal_handler,
    'pop': pop_handler,
}


if __name__ == '__main__':
    import time

    from monitor.main import event_loop, send_exit
    from monitor.mutex import Mutex, mutex_hooks

    m = Mutex('test')
    c = Condition(m, 'test')

    hooks = {}
    hooks.update(mutex_hooks)
    hooks.update(condition_hooks)

    event_loop_thread = threading.Thread(target=event_loop, args=(hooks,))
    event_loop_thread.start()

    pp('cond test')
    if rank == 0:
        m.acquire()
        while True:
            pp('||| waiting for signal')
            c.wait()
            pp('||| got signal!')
        m.release()
    elif rank == 1:
        while True:
            m.acquire()
            pp('||| working...')
            time.sleep(2)
            c.signal()
            pp('||| sent signal...')
            m.release()

    send_exit()
    event_loop_thread.join()
