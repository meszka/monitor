from mpi4py import MPI
from main import *
import inspect
import threading

def method_decorator(mutex, method):
    def wrapped(*args, **kwargs):
        mutex.acquire()
        value = method(*args, **kwargs)
        mutex.release()
        return value
    return wrapped

class MonitorMeta(type):
    def __init__(cls, name, bases, attrs):
        setattr(cls, 'mutex', Mutex(cls.__name__))
        super(MonitorMeta, cls).__init__(name, bases, attrs)
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name not in ['wait', 'signal']:
                setattr(cls, name, method_decorator(cls.mutex, method))


class MonitorBase(object, metaclass=MonitorMeta):
    def wait(self, condition):
        condition.wait()

    def signal(self, condition):
        condition.signal()

class Monitor(MonitorBase):
    def test(self):
        self.wait("aaa")
        print("test")
        self.signal("aaa")
        return 1

    def abc(self):
        print("abc")
        return 2

    def seq(self):
        for i in range(10):
            print(rank, i)

if __name__ == '__main__':
    event_loop_thread = threading.Thread(target=event_loop)
    event_loop_thread.start()

    m = Monitor()
    print(m.mutex)
    while True:
        m.seq()
