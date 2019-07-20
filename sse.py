import sys
import networkx as nx
import sdfpy.core as core
import sdfpy.simulation as simul

if __name__ == '__main__':
    if ( len(sys.argv) < 2 ):
        print( "Missing required argument: input-file" )
        sys.exit()

    sdfg = core.load_sdf_yaml( sys.argv[ 1 ] )
    for v in sdfg:
        simul.find_throughput( sdfg, v )

