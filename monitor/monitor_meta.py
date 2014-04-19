from mpi4py import MPI
import inspect
import threading

from monitor.mutex import Mutex

def method_decorator(method):
    def wrapped(self, *args, **kwargs):
        # print(self, *args, **kwargs)
        self._mutex.acquire()
        value = method(self, *args, **kwargs)
        for var in self._variables:
            var.sync()
        self._mutex.release()
        return value
    return wrapped

class MonitorMeta(type):
    def __init__(cls, name, bases, attrs):
        super(MonitorMeta, cls).__init__(name, bases, attrs)
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name not in ['wait', 'signal', 'register', '__init__', '__new__']:
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

    def register(self, variables):
        self._variables = variables

from monitor.shared_variables import SharedList

class Monitor(MonitorBase):
    def __init__(self):
        self.s1 = SharedList('s1', [1,2,3])
        self.register([self.s1])

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

    def list_append(self, elem):
        self.s1.append(elem)

    def list_print(self):
        print(self.s1)

if __name__ == '__main__':
    import time

    from monitor.main import event_loop
    from monitor.mutex import mutex_hooks
    from monitor.shared_variables import variable_hooks

    hooks = {}
    hooks.update(mutex_hooks)
    hooks.update(variable_hooks)

    event_loop_thread = threading.Thread(target=event_loop, args=(hooks,))
    event_loop_thread.start()

    m = Monitor()
    # print(m._mutex)
    # while True:
    #     m.seq()
    m.list_append(5)
    time.sleep(1)
    m.list_print()
