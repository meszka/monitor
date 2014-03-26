import inspect

def monitor_decorator(cls):
    class Wrapped(cls):
        mutex_name = cls.__name__
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        setattr(Wrapped, name, method_decorator(method))
    return Wrapped

def method_decorator(method):
    def wrapped(*args, **kwargs):
        print("lock {}-mutex".format(args[0].__class__.mutex_name))
        value = method(*args, **kwargs)
        print("unlock {}-mutex".format(args[0].__class__.mutex_name))
        return value
    return wrapped


@monitor_decorator
class Monitor:
    def test(self):
        print("test")
        return 1

    def abc(self):
        print("abc")
        return 2
