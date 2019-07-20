import networkx as nx
import sdfpy.core as core
import sdfpy.schedule as schedule
import sdfpy.transform as transform
from sdfpy.integers import gcd, lcm
import sdfpy.simulation as sse
from random import seed, randrange
import itertools

if __name__ == '__main__':
    seed( 42 )
    rates, graph = generate_cycle( 9 )
    true_period = 1 / sse.find_throughput( core.SDFGraph( graph ))
    print( "Actual period = {}".format( true_period ))

    sdfg = core.SDFGraph( graph )
    apx = transform.single_rate_apx( sdfg )
    for v in sdfg:
        # measure the impact of vectorizing v 
        _, w, out_data = sdfg.out_edges( v, data = True )[ 0 ]
        u, _, in_data = sdfg.in_edges( v, data = True )[ 0 ]
        p_in, c_in, t_in = in_data['production'], in_data['consumption'], in_data.get('tokens', 0)
        p_out, c_out, t_out = out_data['production'], out_data['consumption'], out_data.get('tokens', 0)
        assert c_in == p_out, "rates must match"
        delta_apx( p_in, t_in, c_in, t_out, c_out )


