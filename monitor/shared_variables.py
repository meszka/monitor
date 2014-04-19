from collections.abc import MutableSequence
from main import Message
from main import comm, rank, size, clock, pp

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
        self.name = name
        variables[name] = self

    def clear_changes(self):
        del self.changes[:]

    def update(self):
        message = Message('update', clock.time, self.name, self.changes)
        for i in set(range(size)) - {rank}:
            comm.send(message, dest=i)
        self.clear_changes()

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

    def __delitem__(self):
        self.changes.append(('del', key))
        del self._dict[key]

    def __iter__(self):
        iter(self._dict)

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

def update_handler(source, message):
    # pp('received update from', source)
    variable = variables[message.name]
    changes = message.data
    variable.apply_changes(changes)

variable_hooks = { 'update': update_handler }


def test_local():
    s1 = SharedList('s1', [1,2,3])
    s2 = SharedList('s2', [1,2,3])

    s1.extend([5,6,7])
    s1[2:4] = [0,1]
    s1.insert(0, 8)
    s1[1] = 2

    s2.apply_changes(s1.changes)

    print(s1)
    print(s2)
    assert list(s1) == list(s2)

def test_distributed():
    import threading
    import time

    from main import event_loop, send_exit
    from mutex import Mutex, mutex_hooks

    s = SharedList('s1', [1, 2, 3])
    m = Mutex('m')

    hooks = {}
    hooks.update(mutex_hooks)
    hooks.update(variable_hooks)

    event_loop_thread = threading.Thread(target=event_loop, args=(hooks,))
    event_loop_thread.start()

    with m:
        s.pop(0)
        s.append(5)
        # pp('appended')
        s.update()
        # pp('sent update')

    time.sleep(1)

    if rank == 0:
        print(s)
        assert s == [5, 5, 5]

if __name__ == '__main__':
    test_distributed()
