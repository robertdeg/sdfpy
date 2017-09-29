import unittest
import networkx as nx
from sdfpy.mcr import max_cycle_ratio, compute_mcr_component

class TestMaxCycleRatioSingleComponent(unittest.TestCase):

    def test_self_loop(self):
        g = nx.MultiDiGraph()
        # two cycles, with cycle ratios 3 and 2
        g.add_edge( 1, 2, weight = 5, tokens = 1 )
        g.add_edge( 1, 2, weight = 1, tokens = 0 )
        g.add_edge( 2, 1, weight = 1, tokens = 1 )

        # self-loop with max. cycle ratio 4
        g.add_edge( 1, 1, weight = 4, tokens = 1 )

        # self-loop with cycle ratio 7/2
        g.add_edge( 2, 2, weight = 7, tokens = 2 )

        compute_mcr_component( g, 1 )

