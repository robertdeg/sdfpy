import unittest
import networkx as nx
import sdfpy.core as core

class TestLoadJSON(unittest.TestCase):
    def test_tiny_csdf(self):
        try:
            g = core.load_sdf('tests/graphs/csdfg-tiny.json')
            q = g.repetition_vector()
            s = g.normalisation_vector()
            m = g.modulus()
            self.assertEqual( m, 6, "Modulus of graph is six" )
            self.assertEqual( q['a'], 2 )
            self.assertEqual( q['b'], 3 )
            self.assertEqual( s[('a', 'b')], 1 )
            self.assertEqual( s[('b', 'a')], 1 )
            self.assertEqual( s[('b', 'b')], 2 )
            self.assertEqual( g.nodes['a']['period'], 1 )
            self.assertEqual( g.nodes['b']['period'], 3 )
        except Exception as e:
            self.fail()

    def test_small_csdf(self):
        try:
            g = core.load_sdf('tests/graphs/csdfg-small.json')
            q = g.repetition_vector()
            s = g.normalisation_vector()
            m = g.modulus()
            self.assertEqual( m, 6, "Modulus of graph is six" )
            self.assertEqual( q['a'], 2 )
            self.assertEqual( q['b'], 3 )
            self.assertEqual( q['c'], 3 )
            self.assertEqual( s[('a', 'b')], 1 )
            self.assertEqual( s[('b', 'a')], 1 )
            self.assertEqual( s[('b', 'c')], 2 )
            self.assertEqual( s[('c', 'b')], 2 )
            self.assertEqual( s[('c', 'c')], 2 )
            self.assertEqual( g.nodes['a']['period'], 1 )
            self.assertEqual( g.nodes['b']['period'], 3 )
            self.assertEqual( g.nodes['c']['period'], 1 )
        except Exception as e:
            self.fail()

class TestLoadYAML(unittest.TestCase):
    def test_csdf(self):
        try:
            g = core.load_sdf_yaml('tests/graphs/csdfg-tiny.yaml')
            q = g.repetition_vector()
            s = g.normalisation_vector()
            m = g.modulus()
            self.assertEqual( m, 6, "Modulus of graph is six" )
            self.assertEqual( q['a'], 2 )
            self.assertEqual( q['b'], 3 )
            self.assertEqual( s[('a', 'b')], 1 )
            self.assertEqual( s[('b', 'a')], 1 )
            self.assertEqual( s[('b', 'b')], 2 )
            self.assertEqual( g.nodes['a']['period'], 1 )
            self.assertEqual( g.nodes['b']['period'], 3 )
        except Exception as e:
            self.fail()

    def test_small_csdf(self):
        try:
            g = core.load_sdf_yaml('tests/graphs/csdfg-small.yaml')
            q = g.repetition_vector()
            s = g.normalisation_vector()
            m = g.modulus()
            self.assertEqual( m, 6, "Modulus of graph is six" )
            self.assertEqual( q['a'], 2 )
            self.assertEqual( q['b'], 3 )
            self.assertEqual( q['c'], 3 )
            self.assertEqual( s[('a', 'b')], 1 )
            self.assertEqual( s[('b', 'a')], 1 )
            self.assertEqual( s[('b', 'c')], 2 )
            self.assertEqual( s[('c', 'b')], 2 )
            self.assertEqual( s[('c', 'c')], 2 )
            self.assertEqual( g.nodes['a']['period'], 1 )
            self.assertEqual( g.nodes['b']['period'], 3 )
            self.assertEqual( g.nodes['c']['period'], 1 )
        except Exception as e:
            self.fail()

if __name__ == '__main__':
    unittest.main()
