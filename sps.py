import networkx as nx
import sdfpy.mcr as mcr

if __name__ == '__main__':
    g = nx.MultiDiGraph()

    g.add_edge( 'a2', 'b1', weight = 1, tokens = 1 )
    g.add_edge( 'a2', 'b2', weight = 1, tokens = 1 )

    g.add_edge( 'b1', 'c1', weight = 1, tokens = 0 )
    g.add_edge( 'b2', 'c2', weight = 1, tokens = 0 )
    g.add_edge( 'b2', 'c3', weight = 1, tokens = 0 )

    g.add_edge( 'c2', 'd1', weight = 1, tokens = 0 )
    g.add_edge( 'c3', 'd2', weight = 1, tokens = 0 )
    
    g.add_edge( 'd1', 'a1', weight = 1, tokens = 0 )
    g.add_edge( 'd2', 'a2', weight = 1, tokens = 0 )
    g.add_edge( 'd2', 'a3', weight = 1, tokens = 0 )

    # Extra edges for enforcing SPS
    g.add_edge( 'a1', 'a2', weight = 400, tokens = 0 )
    g.add_edge( 'a2', 'a3', weight = 400, tokens = 0 )
    g.add_edge( 'a3', 'a1', weight = 400, tokens = 1 )

    g.add_edge( 'b1', 'b2', weight = 600, tokens = 0 )
    g.add_edge( 'b2', 'b1', weight = 600, tokens = 1 )

    g.add_edge( 'c1', 'c2', weight = 400, tokens = 0 )
    g.add_edge( 'c2', 'c3', weight = 400, tokens = 0 )
    g.add_edge( 'c3', 'c1', weight = 400, tokens = 1 )

    g.add_edge( 'd1', 'd2', weight = 600, tokens = 0 )
    g.add_edge( 'd2', 'd1', weight = 600, tokens = 1 )

    ratio, cycle, _ = mcr.max_cycle_ratio( g )
    print( "Critical cycle: {}".format( cycle ))
    print( "MCR: {}".format( ratio ))


