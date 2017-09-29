import unittest
from sdfpy.forest import Forest 

class TestForest(unittest.TestCase):

    def test_single_edge(self):
        tree = Forest()
        tree.add_edge( 1, 2, 3, dict(a = 1))

        self.assertListEqual( list( tree.pre_order( 1 )), [1, 2] )
        self.assertEqual( tree.parent( 2 ), (1, 2, 3, dict(a = 1)) )

    def test_multi_children(self):
        tree = Forest()
        tree.add_edge( 1, 2 )
        tree.add_edge( 1, 3 )

        self.assertEqual( tree.parent( 2 ), (1, 2) )
        self.assertEqual( tree.parent( 3 ), (1, 3) )

        self.assertListEqual( list( tree.pre_order( 1 )), [1, 2, 3] )

        tree.add_edge( 1, 4 )
        self.assertEqual( tree.parent( 4 ), (1, 4) )
        self.assertListEqual( list( tree.pre_order( 1 )), [1, 2, 3, 4] )

    def test_swap_edge(self):
        tree = Forest()
        tree.add_edge( 1, 2 )
        tree.add_edge( 2, 3 )
        tree.add_edge( 2, 4 )
        tree.add_edge( 1, 5 )
        tree.add_edge( 5, 6 )
        tree.add_edge( 5, 7 )

        self.assertListEqual( list( tree.pre_order( 1 )), [1, 2, 3, 4, 5, 6, 7] )

        tree.add_edge( 6, 4 )
        self.assertEqual( tree.parent( 4 ), (6, 4) )
        self.assertListEqual( list( tree.pre_order( 2 )), [2, 3] )
        self.assertListEqual( list( tree.pre_order( 5 )), [5, 6, 4, 7] )
        self.assertListEqual( list( tree.pre_order( 1 )), [1, 2, 3, 5, 6, 4, 7] )

    def test_swap_subtree(self):
        tree = Forest()
        tree.add_edge( 1, 2 )
        tree.add_edge( 2, 3 )
        tree.add_edge( 2, 4 )
        tree.add_edge( 1, 5 )
        tree.add_edge( 5, 6 )
        tree.add_edge( 5, 7 )
        tree.add_edge( 7, 8 )
        tree.add_edge( 7, 9 )
        self.assertListEqual( list( tree.pre_order( 1 )), [1, 2, 3, 4, 5, 6, 7, 8, 9] )

        tree.add_edge( 2, 7 )
        self.assertEqual( tree.parent( 7 ), (2, 7) )
        self.assertListEqual( list( tree.pre_order( 1 )), [1, 2, 3, 4, 7, 8, 9, 5, 6] )
        
    def test_two_trees(self):
        forest = Forest()
        forest.add_edge( 1, 2 )
        forest.add_edge( 2, 3 )
        forest.add_edge( 2, 4 )
        forest.add_edge( 1, 5 )
        forest.add_edge( 5, 6 )
        forest.add_edge( 5, 7 )
        forest.add_edge( 7, 8 )
        forest.add_edge( 7, 9 )
        self.assertListEqual( list( forest.pre_order( 1 )), [1, 2, 3, 4, 5, 6, 7, 8, 9] )

        forest.add_edge( 10, 11 )
        forest.add_edge( 10, 12 )
        forest.add_edge( 12, 13 )
        self.assertListEqual( list( forest.pre_order( 10 )), [10, 11, 12, 13] )

        self.assertSetEqual( set( forest.roots()), {1, 10} )
        po = sum([list(forest.pre_order(r)) for r in forest.roots()], [])
            
        self.assertListEqual( list( forest.pre_order()), po )

    def test_two_trees_merged(self):
        forest = Forest()
        forest.add_edge( 1, 2 )
        forest.add_edge( 2, 3 )
        forest.add_edge( 2, 4 )
        forest.add_edge( 1, 5 )
        forest.add_edge( 5, 6 )
        forest.add_edge( 5, 7 )
        forest.add_edge( 7, 8 )
        forest.add_edge( 7, 9 )
        forest.add_edge( 10, 11 )
        forest.add_edge( 10, 12 )
        forest.add_edge( 12, 13 )

        # merge the two trees together into a single tree
        forest.add_edge( 9, 10 )
        self.assertSetEqual( set( forest.roots()), {1} )
        self.assertListEqual( list( forest.pre_order()), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13] )

if __name__ == '__main__':
    unittest.main()


