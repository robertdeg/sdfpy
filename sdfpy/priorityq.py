class PriorityQueue(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._lookup = {}
        self._heap = [None]

    def peek(self):
        """Returns the smallest element in the heap, without removing it
        """
        res = self._heap[1]
        value = self[res]
        return (res, value)

    def pop(self):
        """Returns and removes the heap's smallest element
        """
        res = self._heap[1]

        # put the heap's last element at the top of the heap
        self._swap(1, len(self))

        # delete the previous top element
        value = self[res]
        del self[res]

        # restore heap property
        self._sink(1)

        return (res, value)

    def popitem(self):
        """Returns and removes the heap's smallest element.
        (equivalent to pop())
        """
        
        return self.pop()

    def clear(self):
        """Empties the queue
        """
        super().clear()
        self._heap = [None]
        self._lookup.clear()

    def __iter__(self):
        while self:
            yield self.pop()

    def __delitem__(self, key):
        """Deletes key from the queue.
        Complexity: O(log N).
        Deleting keys is more expensive for ones that are closer to the top of the heap.
        """

        # swap item to be deleted with heap's last item
        pos = self._lookup[key]
        self._swap(pos, len(self))

        # delete from heap and lookup
        del self._lookup[key]
        del self._heap[-1]

        # delete from dictionary
        super().__delitem__(key)

        # restore heap property
        self._sink(pos)

    def __setitem__(self, key, value):
        if key not in self:
            # append to heap
            self._lookup[key] = len(self._heap)
            self._heap.append(key)

            # simulate a decrease in value, this causes
            # the item top be moved up
            current = value
        else:
            current = self[key]

        super().__setitem__(key, value)

        # look up current index
        pos = self._lookup[key]

        if value > current:
            # move item away from root
            self._sink(pos)
        else:
            # move item towards root
            self._swim(pos)

    def _setlu(self, i):
        self._lookup[self._heap[i]] = i

    def _less(self, i, j):
        val_i = self[self._heap[i]]
        val_j = self[self._heap[j]]
        if type(val_i) is type(val_j) is tuple:
            return val_i[0] < val_j[0]
        else:
            return val_i < val_j

    def _swap(self, i, j):
        (self._heap[i], self._heap[j]) = (self._heap[j], self._heap[i])
        self._setlu(i)
        self._setlu(j)
        
    def _swim(self, k):
        # while the child at position k is smaller than its parent at position k // 2:
        # move up
        while (k > 1) and self._less(k, k // 2):
            self._swap(k, k // 2)
            k = k // 2

    def _sink(self, k):
        N = len(self)
        while (2 * k <= N):
            j = 2 * k       # j is the left child of k

            # inspect the child that has the lowest value,
            # so check if the right child is lower than the left child
            if j < N and self._less(j + 1, j):
                j += 1

            # check if there is a heap violation, which is the case
            # if the child is lower than the parent
            if not self._less(j, k):
                break

            # there is a heap violation, fix and propagate down
            self._swap(k, j)
            k = j

