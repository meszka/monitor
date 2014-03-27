import inspect

def method_decorator(mutex, method):
    def wrapped(*args, **kwargs):
        print("lock {}-mutex".format(mutex))
        value = method(*args, **kwargs)
        print("unlock {}-mutex".format(mutex))
        return value
    return wrapped

class MonitorBase:
    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        mutex = object.__getattribute__(self, '__class__').__name__
        if inspect.ismethod(attr):
            return method_decorator2(mutex, attr)
        else:
            return attr

class Monitor(MonitorBase):
    def test(self):
        print("test")
        return 1

    def abc(self):
        print("abc")
        return 2
