import time
from mpi4py import MPI

comm = MPI.COMM_WORLD

rank = comm.rank
size = comm.size

send = comm.send

def recv(*args):
    status = MPI.Status()
    message = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
    source = status.Get_source()
    return source, message

#barrier = comm.barrier
def barrier():
    time.sleep(3)
    comm.barrier()
