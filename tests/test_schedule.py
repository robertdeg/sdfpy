import unittest
import networkx as nx
import sdfpy.core as core
import sdfpy.schedule as sched

class TestSchedule(unittest.TestCase):

    def test_strictly_periodic_feasible_schedule( self ):
        # create a small simple multirate graph
        g = nx.DiGraph()
        g.add_node( 1, wcet = 2 )
        g.add_node( 2, wcet = 3 )
        g.add_edge( 1, 2, production = 2, consumption = 3 )
        g.add_edge( 2, 1, production = 3, consumption = 2, tokens = 4 )
        sdfg = core.SDFGraph(g)

        # derive strictly periodic feasible schedule
        

if __name__ == '__main__':
    unittest.main()

