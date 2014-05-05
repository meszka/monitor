import threading

from monitor.main import Message, QueueElement
from monitor.main import comm, rank, size, clock, pp

conditions = {}

DEBUG = False
def debug(*args):
    if DEBUG:
        pp('condition:', *args)

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
            comm.send(message, dest=i)
            debug('sent wait to', i)
        # release mutex
        self.mutex.release()
        # blocking recv of signal message
        debug('waiting for signal')
        with self.signal_cond:
            self.signal_cond.wait()
        debug('got signal, waiting for mutex')
        # acquire mutex
        self.mutex.acquire()

    def signal(self):
        ## lock unnecessary, because signal can only be called inside
        ## mutex section, while wait_handler and pop_handler only outside
        ## mutex section
        if not self.queue:
            debug('signal: empty queue')
            return
        # send signal to first (by timestamp) process in queue
        first = self.queue[0].rank
        clock.increment()
        message = Message('signal', clock.time, self.name)
        comm.send(message, dest=first)
        debug('sent signal to', first)
        self.queue.pop(0)

def wait_handler(source, message):
    debug('received wait from', source)
    condition = conditions[message.name]
    with condition.signal_cond:
        condition.queue.append(QueueElement(message.timestamp, source))
        condition.queue.sort()
def signal_handler(source, message):
    debug('received signal from', source)
    condition = conditions[message.name]
    # tell everyone eles to remove this process from queue
    clock.increment()
    message = Message('pop', clock.time, condition.name)
    for i in set(range(size)) - {rank, source}:
        comm.send(message, dest=i)
        debug('sent pop to', i)
    debug('acquiring signal_cond lock')
    with condition.signal_cond:
        debug('acquired signal_cond lock')
        condition.signal_cond.notify()
        debug('notified')
    debug('handled signal')
def pop_handler(source, message):
    debug('received pop from', source)
    condition = conditions[message.name]
    with condition.signal_cond:
        if not condition.queue:
            debug('pop: condition queue empty')
        else:
            # TODO: can this assertion fail?
            assert condition.queue[0].rank == source
            condition.queue.pop(0)

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
