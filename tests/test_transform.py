import unittest
import networkx as nx
import sdfpy.core as core
from sdfpy.transform import single_rate_apx, single_rate_equivalent

class TestTransformations(unittest.TestCase):

    def test_single_rate_equivalent_simple_multirate( self ):
        # create a small simple multirate graph
        g = nx.DiGraph()
        g.add_node( 1, wcet = 2 )
        g.add_node( 2, wcet = 3 )
        g.add_edge( 1, 2, production = 2, consumption = 3 )
        g.add_edge( 2, 1, production = 3, consumption = 2, tokens = 4 )
        sdfg = core.SDFGraph(g)

        # transform to single rate equivalent
        hsdfg = single_rate_equivalent( sdfg )
        self.assertIn( (1, 1), hsdfg.nodes() )
        self.assertIn( (1, 2), hsdfg.nodes() )
        self.assertIn( (1, 3), hsdfg.nodes() )
        self.assertIn( (2, 1), hsdfg.nodes() )
        self.assertIn( (2, 2), hsdfg.nodes() )
        self.assertEqual( hsdfg.number_of_nodes(), 5 )
        self.assertEqual( hsdfg.number_of_edges(), 5 )

        self.assertIn( ((1, 2), (2, 1)), hsdfg.edges() )
        self.assertIn( ((1, 3), (2, 2)), hsdfg.edges() )
        self.assertIn( ((2, 2), (1, 1)), hsdfg.edges() )
        self.assertIn( ((2, 2), (1, 2)), hsdfg.edges() )
        self.assertIn( ((2, 1), (1, 3)), hsdfg.edges() )

        toks = lambda a, b: hsdfg.get_edge_data( a, b, 0 ).get('tokens', 0)
        self.assertEqual( toks( (1, 2), (2, 1) ), 0 )
        self.assertEqual( toks( (1, 3), (2, 2) ), 0 )
        self.assertEqual( toks( (2, 2), (1, 1) ), 1 )
        self.assertEqual( toks( (2, 2), (1, 2) ), 1 )
        self.assertEqual( toks( (2, 1), (1, 3) ), 0 )

    def test_single_rate_equivalent_multi_multirate( self ):
        # create a small simple multirate graph
        g = nx.MultiDiGraph()
        g.add_node( 1, wcet = 2 )
        g.add_node( 2, wcet = 3 )
        g.add_edge( 1, 2, production = 2, consumption = 3 )
        g.add_edge( 2, 1, production = 3, consumption = 2, tokens = 4 )
        g.add_edge( 2, 1, production = 3, consumption = 2, tokens = 7 )
        sdfg = core.SDFGraph(g)

        # transform to single rate equivalent
        hsdfg = single_rate_equivalent( sdfg )
        self.assertIn( (1, 1), hsdfg.nodes() )
        self.assertIn( (1, 2), hsdfg.nodes() )
        self.assertIn( (1, 3), hsdfg.nodes() )
        self.assertIn( (2, 1), hsdfg.nodes() )
        self.assertIn( (2, 2), hsdfg.nodes() )
        self.assertEqual( hsdfg.number_of_nodes(), 5 )
        self.assertEqual( hsdfg.number_of_edges(), 8 )
        self.assertTrue( hsdfg.is_multigraph() )

        edges = hsdfg.edges( keys = True )
        self.assertIn( ((1, 2), (2, 1), 0), edges )
        self.assertIn( ((1, 3), (2, 2), 0), edges )
        self.assertIn( ((2, 2), (1, 1), 0), edges )
        self.assertIn( ((2, 2), (1, 2), 0), edges )
        self.assertIn( ((2, 1), (1, 3), 0), edges )
        self.assertIn( ((2, 1), (1, 1), 1), edges )
        self.assertIn( ((2, 1), (1, 2), 1), edges )
        self.assertIn( ((2, 2), (1, 3), 1), edges )

        toks = lambda a, b, c: hsdfg.get_edge_data( a, b, c ).get('tokens', 0)
        self.assertEqual( toks( (1, 2), (2, 1), 0 ), 0 )
        self.assertEqual( toks( (1, 3), (2, 2), 0 ), 0 )
        self.assertEqual( toks( (2, 2), (1, 1), 0 ), 1 )
        self.assertEqual( toks( (2, 2), (1, 2), 0 ), 1 )
        self.assertEqual( toks( (2, 1), (1, 3), 0 ), 0 )
        self.assertEqual( toks( (2, 1), (1, 1), 1 ), 1 )
        self.assertEqual( toks( (2, 1), (1, 2), 1 ), 1 )
        self.assertEqual( toks( (2, 2), (1, 3), 1 ), 1 )

    def test_single_rate_apx_multirate( self ):
        # create a small simple multirate graph
        g = nx.DiGraph()
        g.add_node( 1, wcet = 2 )
        g.add_node( 2, wcet = 3 )
        g.add_edge( 1, 2, production = 2, consumption = 3 )
        g.add_edge( 2, 1, production = 3, consumption = 2, tokens = 4 )
        sdfg = core.SDFGraph(g)

        # transform to single rate equivalent
        hsdfg = single_rate_apx( sdfg )

        toks = lambda a, b: hsdfg.get_edge_data( a, b, 0 ).get('tokens', 0)
        self.assertEqual( toks( 1, 2 ), -1 )
        self.assertEqual( toks( 2, 1 ), 2 )

    def test_single_rate_apx_cyclostatic( self ):
        # create a small simple multirate graph
        g = nx.DiGraph()
        g.add_node( 1, wcet = (2, 1) )
        g.add_node( 2, wcet = (3, 4) )
        g.add_edge( 1, 2, production = (2, 1), consumption = (3, 2) )
        g.add_edge( 2, 1, production = (2, 3), consumption = (0, 3), tokens = 4 )
        sdfg = core.SDFGraph(g)

        # transform to single rate equivalent
        hsdfg = single_rate_apx( sdfg )

        toks = lambda a, b: hsdfg.get_edge_data( a, b, 0 ).get('tokens', 0)
        self.assertEqual( toks( 1, 2 ), -2 )
        self.assertEqual( toks( 2, 1 ), 4 )

if __name__ == '__main__':
    unittest.main()

