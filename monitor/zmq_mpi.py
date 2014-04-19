import sys
import zmq
import threading
import pickle
import atexit

PORTBASE = 9990

rank = int(sys.argv[1])
size = int(sys.argv[2])

context = zmq.Context()
in_sock = context.socket(zmq.ROUTER)
in_sock.bind('tcp://*:{}'.format(PORTBASE + rank))

out_socks = {}
for i in set(range(size)):
    out_sock = context.socket(zmq.DEALER)
    out_sock.setsockopt(zmq.IDENTITY, str(rank).encode())
    out_sock.connect('tcp://localhost:{}'.format(PORTBASE + i))
    out_socks[i] = out_sock

def send(obj, dest, tag=None):
    out_socks[dest].send(pickle.dumps(obj))

def recv(*args, **kwargs):
    source = int(in_sock.recv())
    message = pickle.loads(in_sock.recv())
    return source, message

def barrier():
    pass

def exit():
    # for sock in out_socks.values():
    #     sock.close()
    # in_sock.close()
    # context.term()
    context.destroy(linger=1)

atexit.register(exit)
