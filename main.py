from mpi4py import MPI
from collections import namedtuple
from enum import IntEnum
import threading

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

Tag = IntEnum('Tag', 'acquire_request acquire_reply release wait signal')

mutexes = {}

class Mutex:
    def __init__(self, name):
        self.queue = []
        self.name = name
        self.reply_timestamps = [-1] * size
        self.acquire_cond = threading.Condition()
        mutexes[name] = self

    def acquire(self):
        # send acquire message to everyone
        clock.increment()
        message = Message('acquire_request', clock.time, self.name)
        for i in [r for r in range(size) if r != rank]:
            comm.send(message, tag=Tag.acquire_request, dest=i)
            pp('sent request to', i)
        # add myself to end of queue
        self.queue.append(QueueElement(message.timestamp, rank))
        self.queue.sort()
        # wait for reply from everyone (with timestamp > request timestamp)
        # and I am first process in queue (according to timestamp)
        self._acquire_wait(message.timestamp)

    def _all_replies(self, time):
        # pp('reply timestamps: ', self.reply_timestamps, 'time: ', time)
        timestamps = self.reply_timestamps[:rank] + self.reply_timestamps[rank+1:]
        # pp(timestamps)
        return all([t > time for t in timestamps])
        # for i in [r for r in range(size) if r != rank]:
        #     if self.reply_timestamps[i] <= time:
        #         pp('false: ', self.reply_timestamps[i])
        #         return False
        # pp('true')
        # return True

    def _is_first(self):
        # pp(self.queue)
        return self.queue[0].rank == rank
        # return True

    def _acquire_wait(self, time):
        with self.acquire_cond:
            while not (self._all_replies(time) and self._is_first()):
                pp('waiting...', time, self.reply_timestamps, self.queue)
                self.acquire_cond.wait()
            # pp('done waiting!')
        # while not (self._all_replies() and self._is_first()):
        #     message = comm.recv(source=MPI.ANY_SOURCE, tag=Tag.acquire_reply)
        #     pp('received reply from {}', message.source)
        #     clock.update(message.time)
        #     self.reply_timestamps[message.source] = message.timestamp

    def release(self):
        # send release message to everyone
        clock.increment()
        for i in [r for r in range(size) if r != rank]:
            comm.send(Message('release', clock.time, self.name), dest=i)
            pp('sent release to ', i)
        # remove myself from beginning of queue
        assert self.queue[0].rank == rank
        self.queue.pop(0)

class Condition:
    def __init__(self, monitor, name):
        self.queue = []
        self.mutex = monitor.mutex
        self.name = name

    def wait(self):
        # release mutex
        # send wait message to everyone
        # blocking recv of signal message
        # acquire mutex
        pass

    def signal(self):
        # send signal to first (by timestamp) process in queue
        pass

def event_loop():
    while True:
        # pp('event loop recv...')
        status = MPI.Status()
        message = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        source = status.Get_source()
        # pp('type: {}'.format(message.type))
        # pp('source: {}'.format(source))
        # pp('received sth: {}'.format(message))
        clock.update(message.timestamp)

        if message.type == 'acquire_request':
            pp('received request from', source)
            mutex = mutexes[message.name]
            mutex.queue.append(QueueElement(message.timestamp, source))
            mutex.queue.sort()
            comm.send(Message('acquire_reply', clock.time, message.name),
                    dest=source)
            pp('sent reply to ', source)
        elif message.type == 'acquire_reply':
            pp('received reply from', source)
            mutex = mutexes[message.name]
            # pp('acquiring acquire_cond mutex')
            with mutex.acquire_cond:
                mutex.reply_timestamps[source] = message.timestamp
                # pp('notifying ', mutex.name)
                mutex.acquire_cond.notify()
        elif message.type == 'release':
            pp('received release from', source)
            mutex = mutexes[message.name]
            # pp('queue: ', mutex.queue)
            # pp('source: ', source)
            with mutex.acquire_cond:
                # if mutex.queue[0].rank != source:
                #     pp('trying to release: {}, head of queue is: {}'
                #             .format(source, mutex.queue[0].rank))
                # assert mutex.queue[0].rank == source
                # mutex.queue.pop(0)
                mutex.queue = [q for q in mutex.queue if q.rank != source]
                mutex.queue.sort()
                mutex.acquire_cond.notify()
        else:
            pp('wat')

if __name__ == '__main__':
    m = Mutex('test')

    event_loop_thread = threading.Thread(target=event_loop)
    # event_loop_thread.daemon = True
    event_loop_thread.start()


    seq = [0] * size

    for j in range(2):
        m.acquire()
        for i in range(5):
            pp(seq[rank])
            seq[rank] += 1
        m.release()

    comm.barrier()

    pp(' EXIT ')

    # event_loop_thread.join()
