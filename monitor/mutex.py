import threading
from mpi4py import MPI

from main import Message, QueueElement, Tag
from main import comm, rank, size, clock, pp

mutexes = {}

class Mutex:
    def __init__(self, name):
        self.queue = []
        self.name = name
        self.reply_timestamps = [-1] * size
        self.acquire_cond = threading.Condition()
        self.acquire_count = 0
        mutexes[name] = self

    def acquire(self):
        if self.acquire_count > 0:
            self.acquire_count += 1
        else:
            # send acquire message to everyone
            clock.increment()
            message = Message('acquire_request', clock.time, self.name)
            for i in set(range(size)) - {rank}:
                comm.send(message, tag=Tag.acquire_request, dest=i)
                # pp('sent request to', i)
            # add myself to end of queue
            self.queue.append(QueueElement(message.timestamp, rank))
            self.queue.sort()
            # wait for reply from everyone (with timestamp > request timestamp)
            # and I am first process in queue (according to timestamp)
            self._acquire_wait(message.timestamp)
            self.acquired = True
            self.acquire_count = 1

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
                # pp('waiting...', time, self.reply_timestamps, self.queue)
                self.acquire_cond.wait()
            # pp('done waiting!')
        # while not (self._all_replies() and self._is_first()):
        #     message = comm.recv(source=MPI.ANY_SOURCE, tag=Tag.acquire_reply)
        #     pp('received reply from {}', message.source)
        #     clock.update(message.time)
        #     self.reply_timestamps[message.source] = message.timestamp

    def release(self):
        if self.acquire_count == 0:
            return
        self.acquire_count -= 1
        if self.acquire_count == 0:
            # send release message to everyone
            clock.increment()
            for i in set(range(size)) - {rank}:
                comm.send(Message('release', clock.time, self.name), dest=i, tag=Tag.release)
                # pp('sent release to ', i)
            # remove myself from beginning of queue
            assert self.queue[0].rank == rank
            self.queue.pop(0)
            self.acquire_count -= 1

    def __enter__(self):
        self.acquire()

    def __exit__(self, *exc):
        self.release()


def acquire_request_handler(source, message):
    # pp('received request from', source)
    mutex = mutexes[message.name]
    mutex.queue.append(QueueElement(message.timestamp, source))
    mutex.queue.sort()
    comm.send(Message('acquire_reply', clock.time, message.name),
            dest=source)
    # pp('sent reply to ', source)
def acquire_reply_handler(source, message):
    # pp('received reply from', source)
    mutex = mutexes[message.name]
    # pp('acquiring acquire_cond mutex')
    with mutex.acquire_cond:
        mutex.reply_timestamps[source] = message.timestamp
        # pp('notifying ', mutex.name)
        mutex.acquire_cond.notify()
def release_handler(source, message):
    # pp('received release from', source)
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

mutex_hooks = {
    'acquire_request': acquire_request_handler,
    'acquire_reply': acquire_reply_handler,
    'release': release_handler,
}


if __name__ == '__main__':
    from main import event_loop, send_exit

    m = Mutex('test')

    hooks = mutex_hooks
    event_loop_thread = threading.Thread(target=event_loop, args=(hooks,))
    event_loop_thread.start()

    seq = [0] * size

    pp('mutex test')
    with m:
        for j in range(2):
            with m:
                for i in range(5):
                    pp(seq[rank])
                    seq[rank] += 1

    send_exit()
    event_loop_thread.join()