import unittest
import networkx as nx
import sdfpy.mcr as mcr
from fractions import Fraction

def canonicalform( ls ):
    m = min( ls )
    while ls[ 0 ] > m:
        ls = ls[1:] + [ ls[ 0 ] ]

    return ls


class TestMaxCycleRatioSingleComponent(unittest.TestCase):
    def test_deadlocked_self_loop(self):
        g = nx.MultiDiGraph()

        # two cycles, with cycle ratios 3 and 2
        g.add_edge( 1, 2, weight = 5, tokens = 1 )
        g.add_edge( 1, 2, weight = 1, tokens = 0 )
        g.add_edge( 2, 1, weight = 1, tokens = 1 )

        # self-loop with max. cycle ratio 4
        g.add_edge( 1, 1, weight = 4, tokens = 1 )

        # deadlocked self-loop
        g.add_edge( 1, 1, weight = 1, tokens = 0 )

        # self-loop with cycle ratio 7/2
        g.add_edge( 2, 2, weight = 7, tokens = 2 )

        try:
            mcr.compute_mcr_component( g, 1 )
        except mcr.InfeasibleException as c:
            self.assertListEqual( canonicalform(c.cycle), [(1, 1, 1)] )
        else:
            self.fail( "Deadlocked self-loop not detected" )

    def test_deadlocked_two_cycle(self):
        g = nx.MultiDiGraph()

        # two two-cycles, with cycle ratios 3 and 2
        g.add_edge( 1, 2, weight = 5, tokens = 1 )
        g.add_edge( 1, 2, weight = 1, tokens = 0 )
        g.add_edge( 2, 1, weight = 1, tokens = 1 )

        # two-cycle with  cycle ratio 4
        g.add_edge( 2, 3, weight = 4, tokens = 1 )
        g.add_edge( 3, 2, weight = 4, tokens = 1 )

        # two-cycle with cycle ratio 4
        g.add_edge( 3, 4, weight = 7, tokens = 2 )
        g.add_edge( 4, 3, weight = 1, tokens = 0 )

        # deadlocked two-cycle
        g.add_edge( 2, 3, weight = 1, tokens = 0 )
        g.add_edge( 3, 2, weight = 1, tokens = 0 )

        try:
            mcr.compute_mcr_component( g, 1 )
        except mcr.InfeasibleException as c:
            self.assertListEqual( canonicalform(c.cycle), [(2, 3, 1), (3, 2, 1)] )
        else:
            self.fail( "Deadlocked self-loop not detected" )

    def test_simple(self):
        g = nx.MultiDiGraph()
        g.add_edge( 1, 2, weight = 15, tokens = 4 )
        g.add_edge( 1, 2, weight = 5, tokens = 2 )
        g.add_edge( 2, 1, weight = 5, tokens = 1 )      # two cycles, ratios: 20/5, 10/3
        g.add_edge( 2, 1, weight = 15, tokens = 3 )     # two cycles, ratios: 30/7, 20/5

        g.add_edge( 2, 3, weight = 5, tokens = 5 )
        g.add_edge( 2, 3, weight = 1, tokens = 0 )
        g.add_edge( 3, 2, weight = 2, tokens = 1 )      # two cycles, ratios: 7/6, 3/1
        g.add_edge( 3, 2, weight = 5, tokens = 2 )      # two cycles, ratios: 10/7, 6/2

        try:
            cycle_ratio_1, cycle_1 = mcr.compute_mcr_component( g, 1 )
            self.assertEqual( cycle_ratio_1, Fraction( 30, 7 ))

            cycle_ratio_2, cycle_2 = mcr.compute_mcr_component( g, 2 )
            self.assertEqual( cycle_ratio_2, Fraction( 30, 7 ))

            cycle_ratio_3, cycle_3 = mcr.compute_mcr_component( g, 3 )
            self.assertEqual( cycle_ratio_3, Fraction( 30, 7 ))

            self.assertListEqual( canonicalform(cycle_1), [(1, 2, 0), (2, 1, 1)] )
            self.assertListEqual( canonicalform(cycle_2), [(1, 2, 0), (2, 1, 1)] )
            self.assertListEqual( canonicalform(cycle_3), [(1, 2, 0), (2, 1, 1)] )

        except mcr.InfeasibleException as c:
            self.fail( "Incorrectly concluded deadlock" )

    def test_six_nodes(self):
        g = nx.MultiDiGraph()
        g.add_edge( 1, 2, weight =  5, tokens = 0 )
        g.add_edge( 1, 2, weight = 60, tokens = 1 )

        g.add_edge( 2, 3, weight =   5, tokens = 0 )
        g.add_edge( 2, 3, weight = 105, tokens = 2 )

        g.add_edge( 3, 4, weight =   5, tokens = 0 )
        g.add_edge( 3, 4, weight = 160, tokens = 3 )

        g.add_edge( 4, 5, weight =   5, tokens = 0 )
        g.add_edge( 4, 5, weight = 202, tokens = 4 )

        g.add_edge( 5, 6, weight =   5, tokens = 0 )
        g.add_edge( 5, 6, weight = 253, tokens = 5 )

        g.add_edge( 6, 1, weight = 5, tokens = 1 )

        try:
            cr = Fraction( 785, 16 )
            cc = [(1, 2, 1), (2, 3, 1), (3, 4, 1), (4, 5, 1), (5, 6, 1), (6, 1, 0)]

            cycle_ratio, cycle = mcr.compute_mcr_component( g, 1 )
            self.assertEqual( cycle_ratio, cr )
            self.assertListEqual( canonicalform(cycle),  cc )

            cycle_ratio, cycle = mcr.compute_mcr_component( g, 2 )
            self.assertEqual( cycle_ratio, cr )
            self.assertListEqual( canonicalform(cycle),  cc )

            cycle_ratio, cycle = mcr.compute_mcr_component( g, 3 )
            self.assertEqual( cycle_ratio, cr )
            self.assertListEqual( canonicalform(cycle),  cc )

            cycle_ratio, cycle = mcr.compute_mcr_component( g, 4 )
            self.assertEqual( cycle_ratio, cr )
            self.assertListEqual( canonicalform(cycle),  cc )

            cycle_ratio, cycle = mcr.compute_mcr_component( g, 5 )
            self.assertEqual( cycle_ratio, cr )
            self.assertListEqual( canonicalform(cycle),  cc )

            cycle_ratio, cycle = mcr.compute_mcr_component( g, 6 )
            self.assertEqual( cycle_ratio, cr )
            self.assertListEqual( canonicalform(cycle),  cc )
        except mcr.InfeasibleException as c:
            self.fail( "Incorrectly concluded deadlock" )

    def test_digraph(self):
        g = nx.DiGraph()
        g.add_edge(1, 2, weight = 5, tokens = 0 )
        g.add_edge(2, 1, weight = 5, tokens = 1 )

        g.add_edge(2, 3, weight = 15, tokens = 1 )
        g.add_edge(3, 2, weight = 16, tokens = 2 )

        g.add_edge(3, 4, weight = 15, tokens = 2 )
        g.add_edge(4, 3, weight = 16, tokens = 2 )

        cr = Fraction(31, 3)
        cc = [(2, 3), (3, 2)]

        cycle_ratio, cycle = mcr.compute_mcr_component( g, 1 )
        self.assertEqual( cycle_ratio, cr )
        self.assertListEqual( canonicalform(cycle),  cc )

if __name__ == '__main__':
    unittest.main()
