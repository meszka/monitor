from mpi4py import MPI

class Mutex:
    def __init__(self, name):
        self.queue = []
        self.name = name

    def acquire(self):
        # send acquire message to everyone
        # add myself to end of queue
        # wait for reply from everyone (with timestamp > request timestamp)
        # and I am first process in queue (according to timestamp)

    def release(self):
        # send release message to everyone
        # remove myself from beginning of queue


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

    def signal(self):
        # send signal to first (by timestamp) process in queue


if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
