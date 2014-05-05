import sys
import zmq
import threading
import pickle
import atexit
import time

from monitor.zmq_hosts import host_for

rank = int(sys.argv[1])
size = int(sys.argv[2])
PORTBASE = int(sys.argv[3])

context = zmq.Context()
in_sock = context.socket(zmq.ROUTER)
in_sock.bind('tcp://*:{}'.format(PORTBASE + rank))

out_socks = {}
for i in range(size):
    host = host_for(i)
    out_sock = context.socket(zmq.DEALER)
    out_sock.setsockopt(zmq.IDENTITY, str(rank).encode())
    out_sock.connect('tcp://{}:{}'.format(host, PORTBASE + i))
    out_socks[i] = out_sock

def send(obj, dest, tag=None):
    out_socks[dest].send(pickle.dumps(obj))

def recv(*args, **kwargs):
    source = int(in_sock.recv())
    message = pickle.loads(in_sock.recv())
    return source, message

def barrier():
    time.sleep(1)

def exit():
    # for sock in out_socks.values():
    #     sock.close()
    # in_sock.close()
    # context.term()
    context.destroy(linger=1)

atexit.register(exit)
