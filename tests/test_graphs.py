import unittest
import networkx as nx
from sdfpy.graphs import longest_distances, shortest_distances, NegativeCycle, PositiveCycle

class TestShortestPaths(unittest.TestCase):

    def test_negative_self_loop(self):
        # create a small graph
        g = nx.MultiDiGraph()
        g.add_edge(1, 2, weight = 1)
        g.add_edge(2, 3, weight = -1)
        g.add_edge(2, 3, weight = 1)
        g.add_edge(3, 3, weight = -1)

        try:
            parents, distances = shortest_distances( g, 1 )
        except NegativeCycle as c:
            self.assertListEqual( c.cycle, [(3, 3, 0)] )
        else:
            self.fail( "Negative self-loop not detected" )

    def test_negative_small_loop(self):
        # create a small graph
        g = nx.MultiDiGraph()
        g.add_edge(1, 2, weight = 1)
        g.add_edge(2, 3, weight = -1)
        g.add_edge(2, 3, weight = 1)
        g.add_edge(3, 2, weight = 0)

        try:
            parents, distances = shortest_distances( g, 1 )
        except NegativeCycle as c:
            # put cycle into "canonical" form
            min_edge = min( c.cycle )
            while c.cycle[ 0 ] > min_edge:
                c.cycle = c.cycle[1:] + [ c.cycle[ 0 ] ]

            self.assertListEqual( c.cycle, [(2, 3, 0),(3, 2, 0)] )
        else:
            self.fail( "Negative self-loop not detected" )

    def test_example_1( self ):
        g = nx.MultiDiGraph()
        g.add_edge(1, 2, weight = -2)
        g.add_edge(1, 3, weight = 3)
        g.add_edge(2, 4, weight = 3)
        g.add_edge(2, 6, weight = 6)
        g.add_edge(3, 2, weight = -3)
        g.add_edge(3, 5, weight = 1)
        g.add_edge(4, 2, weight = -2)
        g.add_edge(4, 3, weight = 1)
        g.add_edge(4, 5, weight = 1)
        g.add_edge(4, 6, weight = 2)
        g.add_edge(4, 7, weight = 2)
        g.add_edge(5, 3, weight = 1)
        g.add_edge(5, 7, weight = 1)
        g.add_edge(6, 7, weight = -1)
        g.add_edge(7, 6, weight = 2)

        try:
            parents, distances = shortest_distances( g, 1 )
            expected_distances = { 1: 0, 2: -2, 3: 2, 4: 1, 5: 2, 6: 3, 7: 2 }
            expected_parents = {
                1: None,
                2: (1, 2, 0),
                3: (4, 3, 0),
                4: (2, 4, 0),
                5: (4, 5, 0),
                6: (4, 6, 0),
                7: (6, 7, 0)}

            self.assertDictEqual( distances, expected_distances )
            self.assertDictEqual( parents, expected_parents )

        except NegativeCycle as c:
            self.fail( "False negative self-loop detected" )

    def test_example_2( self ):
        g = nx.MultiDiGraph()
        g.add_edge(1, 5, weight = 5)
        g.add_edge(1, 4, weight = 4)
        g.add_edge(1, 3, weight = 3)
        g.add_edge(1, 2, weight = 1)

        g.add_edge(2, 5, weight = 4)
        g.add_edge(2, 4, weight = 3)
        g.add_edge(2, 3, weight = 1)

        g.add_edge(3, 2, weight = 0)
        g.add_edge(3, 4, weight = 1)

        g.add_edge(4, 2, weight = -1)
        g.add_edge(4, 3, weight = 0)
        g.add_edge(4, 5, weight = 1)

        try:
            parents, distances = shortest_distances( g, 1 )
            expected_distances = { 1: 0, 2: 1, 3: 2, 4: 3, 5: 4 }
            expected_parents = {
                1: None,
                2: (1, 2, 0),
                3: (2, 3, 0),
                4: (3, 4, 0),
                5: (4, 5, 0)}

            self.assertDictEqual( distances, expected_distances )
            self.assertDictEqual( parents, expected_parents )

        except NegativeCycle as c:
            self.fail( "False negative self-loop detected" )

class TestLongestPaths(unittest.TestCase):

    def test_positive_self_loop(self):
        # create a small graph
        g = nx.MultiDiGraph()
        g.add_edge(1, 2, weight = -1)
        g.add_edge(2, 3, weight = 1)
        g.add_edge(2, 3, weight = -1)
        g.add_edge(3, 3, weight = 1)

        try:
            parents, distances = longest_distances( g, 1 )
        except PositiveCycle as c:
            self.assertListEqual( c.cycle, [(3, 3, 0)] )
        else:
            self.fail( "Positive self-loop not detected" )

    def test_positive_small_loop(self):
        # create a small graph
        g = nx.MultiDiGraph()
        g.add_edge(1, 2, weight = -1)
        g.add_edge(2, 3, weight = 1)
        g.add_edge(2, 3, weight = -1)
        g.add_edge(3, 2, weight = 0)

        try:
            parents, distances = longest_distances( g, 1 )
        except PositiveCycle as c:
            # put cycle into "canonical" form
            min_edge = min( c.cycle )
            while c.cycle[ 0 ] > min_edge:
                c.cycle = c.cycle[1:] + [ c.cycle[ 0 ] ]

            self.assertListEqual( c.cycle, [(2, 3, 0),(3, 2, 0)] )
        else:
            self.fail( "Positive cycle not detected" )

    def test_example_1( self ):
        g = nx.MultiDiGraph()
        g.add_edge(1, 2, weight = 2)
        g.add_edge(1, 3, weight = -3)
        g.add_edge(2, 4, weight = -3)
        g.add_edge(2, 6, weight = -6)
        g.add_edge(3, 2, weight = 3)
        g.add_edge(3, 5, weight = -1)
        g.add_edge(4, 2, weight = 2)
        g.add_edge(4, 3, weight = -1)
        g.add_edge(4, 5, weight = -1)
        g.add_edge(4, 6, weight = -2)
        g.add_edge(4, 7, weight = -2)
        g.add_edge(5, 3, weight = -1)
        g.add_edge(5, 7, weight = -1)
        g.add_edge(6, 7, weight = 1)
        g.add_edge(7, 6, weight = -2)

        try:
            parents, distances = longest_distances( g, 1 )
            expected_distances = { 1: 0, 2: 2, 3: -2, 4: -1, 5: -2, 6: -3, 7: -2 }
            expected_parents = {
                1: None,
                2: (1, 2, 0),
                3: (4, 3, 0),
                4: (2, 4, 0),
                5: (4, 5, 0),
                6: (4, 6, 0),
                7: (6, 7, 0)}

            self.assertDictEqual( distances, expected_distances )
            self.assertDictEqual( parents, expected_parents )

        except PositiveCycle as c:
            self.fail( "False positive cycle detected" )

    def test_example_2( self ):
        g = nx.MultiDiGraph()
        g.add_edge(1, 5, weight = -5)
        g.add_edge(1, 4, weight = -4)
        g.add_edge(1, 3, weight = -3)
        g.add_edge(1, 2, weight = -1)

        g.add_edge(2, 5, weight = -4)
        g.add_edge(2, 4, weight = -3)
        g.add_edge(2, 3, weight = -1)

        g.add_edge(3, 2, weight = 0)
        g.add_edge(3, 4, weight = -1)

        g.add_edge(4, 2, weight = 1)
        g.add_edge(4, 3, weight = 0)
        g.add_edge(4, 5, weight = -1)

        try:
            parents, distances = longest_distances( g, 1 )
            expected_distances = { 1: 0, 2: -1, 3: -2, 4: -3, 5: -4 }
            expected_parents = {
                1: None,
                2: (1, 2, 0),
                3: (2, 3, 0),
                4: (3, 4, 0),
                5: (4, 5, 0)}

            self.assertDictEqual( distances, expected_distances )
            self.assertDictEqual( parents, expected_parents )

        except PositiveCycle as c:
            self.fail( "False positive cycle detected" )

if __name__ == '__main__':
    unittest.main()

