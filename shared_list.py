from collections.abc import MutableSequence

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

class SharedList(MutableSequence):
    def __init__(self, seq=[]):
        self._list = list(seq)
        self.changes = []

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

    def clear_changes(self):
        del changes[:]

if __name__ == '__main__':
    s1 = SharedList([1,2,3])
    s2 = SharedList([1,2,3])

    s1.extend([5,6,7])
    s1[2:4] = [0,1]
    s1.insert(0, 8)
    s1[1] = 2

    s2.apply_changes(s1.changes)

    print(s1)
    print(s2)
    assert list(s1) == list(s2)
