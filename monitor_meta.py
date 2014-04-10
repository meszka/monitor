from mpi4py import MPI
from main import *
import inspect
import threading

def method_decorator(method):
    def wrapped(self, *args, **kwargs):
        self._mutex.acquire()
        value = method(*args, **kwargs)
        self._mutex.release()
        return value
    return wrapped

class MonitorMeta(type):
    def __init__(cls, name, bases, attrs):
        super(MonitorMeta, cls).__init__(name, bases, attrs)
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name not in ['wait', 'signal', '__init__', '__new__']:
                setattr(cls, name, method_decorator(method))


class MonitorBase(object, metaclass=MonitorMeta):
    _monitor_counter = 0
    def __new__(cls, *args, **kwargs):
        obj = super(MonitorBase, cls).__new__(cls, *args, **kwargs)
        cls._monitor_counter += 1
        mutex_name = 'mutex-{}-{}'.format(cls.__name__, cls._monitor_counter)
        obj._mutex = Mutex(mutex_name)
        return obj

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
    print(m._mutex)
    while True:
        m.seq()
