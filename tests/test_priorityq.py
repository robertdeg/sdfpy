import unittest
import random
from sdfpy.priorityq import PriorityQueue

class TestPriorityQueue(unittest.TestCase):

    def test_heap_sort(self):
        q = PriorityQueue()
        for i in range(10):
            q[ i ] = i

        self.assertListEqual( list( iter( q )), [(i, i) for i in range(10)] )

        for i in range(10, 0, -1):
            q[ i ] = i

        self.assertListEqual( list( iter( q )), [(i, i) for i in range(1, 11)] )

        for s in [42, 255, 101, 500]:
            random.seed( s )
            ls = list(range(100))
            random.shuffle( ls )

            for i in ls:
                q[ i ] = i
            
            self.assertListEqual( list( iter( q )), sorted([(i, i) for i in ls]))

    def test_decrease_priority(self):
        q = PriorityQueue()

        for i in range(1, 50):
            q[ i ] = i

        # change priority of all multiples of 7 
        for i in range(7, 50, 7):
            q[ i ] = i + 50

        self.assertListEqual( list( iter( q )), [(i, i) for i in range(1, 50) if i % 7 != 0] + [(i, i + 50) for i in range(7, 50, 7) ] )

    def test_increase_priority(self):
        q = PriorityQueue()

        for i in range(1, 50):
            q[ i ] = i

        # change priority of all multiples of 6 
        for i in range(6, 50, 6):
            q[ i ] = i - 50

        self.assertListEqual( list( iter( q )), [(i, i - 50) for i in range(6, 50, 6) ] + [(i, i) for i in range(1, 50) if i % 6 != 0] )

if __name__ == '__main__':
    unittest.main()

