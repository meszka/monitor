from mpi4py import MPI

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
        # send signal to first process in queue

if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
