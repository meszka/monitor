import collections
from collections.abc import MutableSequence, MutableMapping
from monitor.main import Message
from monitor.main import comm, rank, size, clock, pp

def slice_to_tuple(s):
    if isinstance(s, slice):
        return (s.start, s.stop, s.step)
    else:
        return s

def tuple_to_slice(t):
    if isinstance(t, tuple):
        return slice(*t)
    else:
        return t

variables = {}

class SharedVariable:
    def __init__(self, name):
        self.changes = []
        self.pending_changes = []
        self.name = name
        variables[name] = self

    def clear_changes(self):
        del self.changes[:]

    def sync(self):
        message = Message('sync', clock.time, self.name, self.changes)
        for i in set(range(size)) - {rank}:
            comm.send(message, dest=i)
        self.clear_changes()

    def apply_pending_changes(self):
        for timestamp, changes in self.pending_changes:
            self.apply_changes(changes)
        self.pending_changes = []

class SharedList(SharedVariable, MutableSequence):
    def __init__(self, name, seq=[]):
        self._list = list(seq)
        SharedVariable.__init__(self, name)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        self.changes.append(('set', slice_to_tuple(index), value))
        self._list[index] = value

    def __delitem__(self, index):
        self.changes.append(('del', slice_to_tuple(index)))
        del self._list[index]

    def __str__(self):
        return str(self._list)

    def __repr__(self):
        return self.__str__()

    def insert(self, index, value):
        self.changes.append(('insert', slice_to_tuple(index), value))
        self._list.insert(index, value)

    def apply_changes(self, changes):
        for change in changes:
            if change[0] == 'set':
                index = tuple_to_slice(change[1])
                self._list[index] = change[2]
            elif change[0] == 'del':
                index = tuple_to_slice(change[1])
                del self._list[index]
            elif change[0] == 'insert':
                index = tuple_to_slice(change[1])
                self._list.insert(index, change[2])


class SharedDict(SharedVariable, MutableMapping):
    def __init__(self, name, mapping={}):
        self._dict = dict(mapping)
        SharedVariable.__init__(self, name)

    def __len__(self):
        return len(self._dict)

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self.changes.append(('set', key, value))
        self._dict[key] = value

    def __delitem__(self, key):
        self.changes.append(('del', key))
        del self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __str__(self):
        return str(self._dict)

    def __repr__(self):
        return self.__str__()

    def apply_changes(self, changes):
        for change in changes:
            if change[0] == 'set':
                self._dict[change[1]] = change[2]
            elif change[0] == 'del':
                del self._dict[change[1]]


def shared_auto(name, data):
    if isinstance(data, collections.Sequence):
        return SharedList(name, data)
    elif isinstance(data, collections.Mapping):
        return SharedDict(name, data)
    else:
        raise TypeError('Shared variable data must be a sequence or a mapping')


def sync_handler(source, message):
    # pp('received update from', source)
    variable = variables[message.name]
    changes = message.data
    timestamp = message.timestamp
    variable.pending_changes.append((timestamp, changes))
    variable.pending_changes.sort()

variable_hooks = { 'sync': sync_handler }


def test_shared_list_local():
    if rank == 0:
        s1 = SharedList('s1', [1,2,3])
        s2 = SharedList('s2', [1,2,3])

        s1.extend([5,6,7])
        s1[2:4] = [0,1]
        s1.insert(0, 8)
        s1[1] = 2

        s2.apply_changes(s1.changes)

        print(s1, '==', s2)
        assert list(s1) == list(s2)

def test_shared_list_distributed():
    import threading
    import time

    from monitor.main import event_loop, send_exit
    from monitor.mutex import Mutex, mutex_hooks

    s = SharedList('s1', size * [1])
    m = Mutex('m')

    hooks = {}
    hooks.update(mutex_hooks)
    hooks.update(variable_hooks)

    event_loop_thread = threading.Thread(target=event_loop, args=(hooks,))
    event_loop_thread.start()

    with m:
        s.apply_pending_changes()
        s.pop(0)
        s.append(5)
        # pp('appended')
        s.sync()
        # pp('sent update')

    send_exit()
    event_loop_thread.join()

    if rank == 0:
        s.apply_pending_changes()
        print(s, '==', size * [5])
        assert list(s) == size *[5]

def test_shared_dict_local():
    if rank == 0:
        s1 = SharedDict('s1', {'a': 1, 'b': 2, 'c': 3})
        s2 = SharedDict('s2', {'a': 1, 'b': 2, 'c': 3})

        s1.update({'a': 5, 'c': 6})
        s1['d'] = 7
        del s1['b']

        s2.apply_changes(s1.changes)

        print(s1, '==', s2)
        assert dict(s1) == dict(s2)

def test_shared_dict_distributed():
    import threading
    import time

    from monitor.main import event_loop, send_exit
    from monitor.mutex import Mutex, mutex_hooks

    s = SharedDict('s1', {'a': 0})
    m = Mutex('m')

    hooks = {}
    hooks.update(mutex_hooks)
    hooks.update(variable_hooks)

    event_loop_thread = threading.Thread(target=event_loop, args=(hooks,))
    event_loop_thread.start()

    with m:
        s.apply_pending_changes()
        s['a'] += 1
        s.sync()

    send_exit()
    event_loop_thread.join()

    if rank == 0:
        s.apply_pending_changes()
        print(s, '==', {'a': size})
        assert dict(s) == {'a': size}

if __name__ == '__main__':
    test_shared_list_local()
    test_shared_dict_local()
    # test_shared_list_distributed()
    test_shared_dict_distributed()
