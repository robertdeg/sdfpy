import networkx as nx
import sdfpy.core as core
import sdfpy.schedule as schedule
import sdfpy.transform as transform
from sdfpy.integers import gcd, lcm
import sdfpy.simulation as sse
from random import seed, randrange
import itertools

def generate_canonical_int_vector( n, a, b ):
    vec = list()
    for _ in range( n ):
        vec.append( randrange( a, b ))

    while gcd( vec ) > 1:
        vec = list()
        for _ in range( n ):
            vec.append( randrange( a, b ))

    return vec

def generate_cycle(n = 3):
    # generate a rate-vector
    zs = generate_canonical_int_vector( n, 2, 10 )
    g = nx.MultiDiGraph()
    for i in range( n ):
        g.add_node( i + 1, wcet = 1 )

    g.add_edge( n, 1, production = zs[ n - 1 ], consumption = zs[ 0 ], gcd = gcd( zs[ n - 1 ], zs[ 0 ]) )
    for i in range( 1, n ):
        prate = zs[ i - 1 ]
        crate = zs[ i ]
        g.add_edge( i, i + 1, production = prate, consumption = crate, gcd = gcd( prate, crate ))

    apx = transform.single_rate_apx( core.SDFGraph( g ))

    tokens = 0
    for v, w, data in apx.edges_iter( data = True ):
        tokens += data.get( 'tokens', 0 )

    add_tokens( g, 1 - tokens )
    return zs, g

def add_tokens( graph, tokens ):
    n = graph.number_of_edges()
    it = itertools.cycle( graph.edges_iter( data = True ))
    while tokens > 0:
        _, _, data = next( it )
        delta = randrange( tokens + 1 )
        data['tokens'] = data.get('tokens', 0 ) + delta * data['gcd']
        tokens -= delta
    
def delta_apx( prod_in, toks_in, rate_mid, toks_out, cons_out ):
    # current nr. of tokens:
    while toks_in >= rate_mid[ 0 ]:
        toks_in -= rate_mid[ 0 ]
        toks_out += rate_mid[ 0 ]
        rate_mid = rate_mid[1:]
    
    _, hi_in = transform.predecessor_lin_bounds( production = prod_in, consumption = rate_mid, tokens = toks_in )
    _, hi_out = transform.predecessor_lin_bounds( production = rate_mid, consumption = cons_out, tokens = toks_out )

    # compute rates
    vs = vectorize( prod_in, toks_in, rate_mid )
    _, hi_in2 = transform.predecessor_lin_bounds( production = prod_in, consumption = vs, tokens = toks_in )
    _, hi_out2 = transform.predecessor_lin_bounds( production = vs, consumption = cons_out, tokens = toks_out )
    print("Vectorized {} -> {} -> {} to {}, apx {} -> {}".format( prod_in, toks_in, rate_mid, vs, hi_in + hi_out, hi_in2 + hi_out2 ))

def vectorize( ps, t, cs ):
    periods = cs.sum() // gcd( ps.sum(), cs.sum() )
    vs = list()
    for p in ps * periods:
        t += p
        if t >= cs[0]:
            # consume
            nops =-1 
            csum = 0
            while t >= cs[0]:
                t = t - cs[ 0 ]
                csum += cs[ 0 ]
                cs = cs[1:]
                nops += 1

            vs.append( csum )
            for _ in range( nops ):
                vs.append( 0 )

    return core.cyclic( vs )


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


