import inspect

def method_decorator(mutex, method):
    def wrapped(*args, **kwargs):
        print("lock {}-mutex".format(mutex))
        value = method(*args, **kwargs)
        print("unlock {}-mutex".format(mutex))
        return value
    return wrapped

class MonitorMeta(type):
    def __init__(cls, name, bases, attrs):
        setattr(cls, 'mutex', cls.__name__)
        super(MonitorMeta, cls).__init__(name, bases, attrs)
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name not in ['wait', 'signal']:
                setattr(cls, name, method_decorator(cls.mutex, method))


class MonitorBase(object, metaclass=MonitorMeta):
    def wait(self, condition):
        print("waiting on condition: {} while releasing mutex: {}"
                .format(condition, self.mutex))

    def signal(self, condition):
        print("sending signal on condition: {}".format(condition))


class Monitor(MonitorBase):
    def test(self):
        self.wait("aaa")
        print("test")
        self.signal("aaa")
        return 1

    def abc(self):
        print("abc")
        return 2
