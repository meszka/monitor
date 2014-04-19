import inspect

def monitor_decorator(cls):
    class Wrapped(cls):
        _monitor_counter = 0
        def __init__(self, *args, **kwargs):
            cls.__init__(self, *args, **kwargs)
            self.__class__._monitor_counter += 1
            self.mutex_name = 'mutex-{}-{}'.format(cls.__name__, self.__class__._monitor_counter)

    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name not in ['__init__', '__new__']:
            setattr(Wrapped, name, method_decorator(method))
    return Wrapped

def method_decorator(method):
    def wrapped(*args, **kwargs):
        print("lock {}-mutex".format(args[0].mutex_name))
        value = method(*args, **kwargs)
        print("unlock {}-mutex".format(args[0].mutex_name))
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
