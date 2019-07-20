import networkx as nx
import sdfpy.core as core
import sdfpy.mcr as mcr
import uuid

from sdfpy.core import cyclic, predecessor
from fractions import Fraction
from math import gcd
from sdfpy.integers import xgcd, lcm

def sample_prates(vector, offset, period):
    """ Returns the production rates of unfolded actor [offset]
    if the producing actor is unfolded period times.
    NOTE: offset is 0-based
    """
    vector = cyclic(vector)
    pattern = [None] * (len(vector) // gcd( len(vector), period ))
    for i in range(len(pattern)):
        start = offset + i * period
        end = start + period
        pattern[i] = vector.sum(start, end)

    token_delta = vector.sum(stop = offset)
    return token_delta, cyclic(pattern)

def sample_crates(vector, offset, period):
    """ Returns the consumption rates of actor[offset]
    if the consuming actor is unfolded period times.
    NOTE: offset is 0-based
    """
    vector = cyclic(vector)
    pattern = [None] * (len(vector) // gcd( len(vector), period ))
    for i in range(len(pattern)):
        start = offset + 1 + (i - 1) * period
        end = start + period
        pattern[i] = vector.sum(start, end)

    token_delta = pattern[0] - vector.sum(stop = offset + 1)
    return token_delta, cyclic(pattern)

def predecessor_lin_bounds( **kwargs ):
    prates = kwargs.get('production')
    crates = kwargs.get('consumption')
    tokens = kwargs.get('tokens')
    g = gcd(prates.sum(), crates.sum())
    avg_prate = Fraction( prates.sum(), len(prates) )
    avg_crate = Fraction( crates.sum(), len(crates) )
    minval = None
    maxval = None
    delta = tokens

    for i in range(len(prates)):
        for j in range(len(crates)):
            val_ij = g * (delta // g) - i * avg_prate + j * avg_crate

            minval = val_ij if minval is None else min( minval, val_ij )
            maxval = val_ij if maxval is None else max( maxval, val_ij )
            delta -= crates[j]
        delta = delta + prates[i] + crates.sum()

    return maxval, minval + g - avg_prate

def unfold( sdfg, dct = None, **periods ):
    if dct is not None:
        periods.update( dct )

    result = nx.MultiDiGraph()
    for v, data in sdfg.nodes_iter( data = True ):
        Tv = periods.get(v, 1)
        for i in range(Tv):
            result.add_node( (v, i + 1) if Tv > 1 else v, wcet = data.get('wcet', core.cyclic(0))[i::Tv])

    for v, w, data in sdfg.edges_iter( data = True ):
        Tv = periods.get(v, 1)
        Tw = periods.get(w, 1)
        prates = data.get('production', core.cyclic(1))
        crates = data.get('consumption', core.cyclic(1))
        tokens = data.get('tokens', 0)
        plen = len(prates)

        # consuming actor in unfolded graph has a single phase
        # and consumption rate equal to periods_w * crates.sum()
        csum = crates.sum() * Tw // gcd(Tw, len( crates ))

        # sum of production rates in multi-rate equivalent of unfolded graph
        psum = prates.sum() * Tv // gcd(Tv, len( prates ))

        gm = gcd( csum, psum )
        gvw = gcd( csum, prates.sum() )

        # multiplicative inverse of (psum // gvw) modulo (gm // gvw)
        g_cd, mulinv, _ = xgcd( prates.sum() // gvw, gm // gvw )
        assert g_cd == 1

        # iterate consuming actors
        for j in range(Tw):
            # determine which incoming channels must be added
            incoming = set()

            # see Algorithm ? in PhD thesis
            sols = set()
            for n0 in range( len( crates ) // gcd( len( crates ), Tw )):
                for i0 in range( plen ):
                    delta_i_n = tokens + prates.sum(stop = i0 + 1) - crates.sum(stop = j + 1 + n0 * Tw )
                    delta_i1_n = tokens + prates.sum(stop = i0) - crates.sum(stop = j + 1 + n0 * Tw )
                    sol_min = (gvw - delta_i_n - 1) // gvw
                    sol_max = (gvw - delta_i1_n - 1) // gvw

                    for sol in range(sol_min, sol_max):
                        s = (i0 + sol * mulinv * plen) % gcd(Tv, plen * gm // gvw)
                        sols.add( s )

            for i_residue in sols:
                for i0 in range(i_residue, Tv, gcd(Tv, plen * gm // gvw)):
                    incoming.add( i0 )

            # compute consumption rates for incoming channels
            tokens_c, incoming_crates = sample_crates( crates, j, Tw )

            # add incoming channels:
            for i in incoming:
                # compute production rates
                tokens_p, incoming_prates = sample_prates( prates, i, Tv )

                extra_data = dict()
                if 'var' in data:
                    extra_data['var'] = data['var']

                # add channel
                vi = (v, i + 1) if Tv > 1 else v
                wj = (w, j + 1) if Tw > 1 else w
                result.add_edge( vi, wj,
                    production = incoming_prates,
                    consumption = incoming_crates,
                    tokens = tokens + tokens_c + tokens_p,
                    **extra_data)

    return core.SDFGraph( result )

def multi_rate_equivalent( sdfg ):
    result = nx.MultiDiGraph()
    for v, data in sdfg.nodes_iter( data = True ):
        phi = data.get('phases', 1)
        for i in range(phi):
            result.add_node((v, i + 1), wcet = data.get('wcet', core.cyclic(0))[i])

    for v, w, data in sdfg.edges_iter( data = True ):
        Tv = sdfg.node[v].get('phases', 1)
        Tw = sdfg.node[w].get('phases', 1)
        prates = data.get('production')
        crates = data.get('consumption')
        tokens = data.get('tokens')
        plen = len(prates)
        assert Tv == len(prates)
        assert Tw == len(crates)

        # consuming actor in unfolded graph has a single phase
        # and consumption rate equal to crates.sum()
        csum = crates.sum()

        # sum of production rates in multi-rate equivalent of unfolded graph
        psum = prates.sum()

        gvw = gcd( csum, psum )

        # iterate consuming actors
        for j in range( Tw ):
            # determine which incoming channels must be added
            # see Algorithm ? in PhD thesis
            for i in range( plen ):
                delta_i_n = tokens + prates.sum(stop = i + 1) - crates.sum(stop = j + 1 )
                delta_i1_n = tokens + prates.sum(stop = i) - crates.sum(stop = j + 1 )
                sol_min = (gvw - delta_i_n - 1) // gvw
                sol_max = (gvw - delta_i1_n - 1) // gvw

                if sol_min < sol_max:
                    # add channel
                    extra_data = dict()
                    if 'var' in data:
                        extra_data['var'] = data['var']

                    result.add_edge( (v, i + 1), (w, j + 1),
                        production = psum,
                        consumption = csum,
                        tokens = tokens + prates.sum(stop = i) + crates.sum(start = j + 1),
                        **extra_data)

    return core.SDFGraph( result )

def single_rate_equivalent( sdfg ):
    hsdfg = nx.MultiDiGraph() if sdfg.is_multigraph() else nx.DiGraph()
    multi = nx.MultiDiGraph( sdfg )
    q = sdfg.repetition_vector()
    for v in sdfg:
        assert 'wcet' in sdfg.node[v], "Missing 'wcet' attribute for node {}".format(v)
        wcets = cyclic(sdfg.node[v]['wcet'])

        for i in range(q[v]):
            hsdfg.add_node( (v, i + 1), wcet = wcets[i % len(wcets)] )

        for u, _, key, data in multi.in_edges_iter( v, data = True, keys = True ):
            prates = data.get('production')
            crates = data.get('consumption')
            tokens = data.get('tokens')
            for j in range(q[v]):
                i = predecessor(j + 1, **data)
                if sdfg.is_multigraph():
                    hsdfg.add_edge( (u, (i - 1) % q[u] + 1), (v, j + 1), key = key, tokens = (q[u] - i) // q[u] )
                else:
                    hsdfg.add_edge( (u, (i - 1) % q[u] + 1), (v, j + 1), tokens = (q[u] - i) // q[u] )

    assert hsdfg.number_of_nodes() == sum(q.values()), "Size of HSDF graph must be equal to sum of repetition vector"
    return hsdfg

def single_rate_apx( sdfg, is_pessimistic = True ):
    s = sdfg.normalisation_vector()
    hsdfg = nx.MultiDiGraph()
    for v, data in sdfg.nodes(data = True):
        wcet = data['wcet']
        hsdfg.add_node(v, wcet = max(wcet) if is_pessimistic else min(wcet))

    for v, w, data in sdfg.edges(data = True):
        lo, up = predecessor_lin_bounds( **data )
        delay = up if is_pessimistic else lo
        toks = s[ (v, w) ] * delay
        assert toks.denominator == 1, "delay({}, {}) = {}, s[({}, {})] = {}".format(v, w, delay, v, w, sdfg.s[ (v, w) ])

        h_data = dict( tokens = toks.numerator )

        # FIXME: if edge already exists, keep 
        hsdfg.add_edge( v, w, **h_data )
    return hsdfg

def single_rate_as_marked_graph( hsdfg, relate_start_times = True ):
    """ Creates a marked graph, where each edge has a weight and tokens.
    Each edge imposes a constraint between either the start or finish times of the firings of each node:
    An edge (u, v) with weight w and tokens d translates to the constraint:
        t(v, k) >= t(u, k - d) + w,
    where t(v, k) denotes the time at which the k-th firing of v starts or finish, depending on the parameter
    relate_start_times.
    """
    mg = nx.MultiDiGraph()
    
    for v, data in hsdfg.nodes(True):
        if 'wcet' not in data:
            raise SDFTransformError("Actor {} has no attribute 'wcet'".format(v))

        wcet = data['wcet']
        try:
            # assume wcet is iterable
            wcet = wcet[0]
            try:
                wcet = int(wcet)
            except ValueError:
                raise SDFTransformError("Actor {} has an invalid attribute 'wcet'".format(v))
        except IndexError:
            raise SDFTransformError("Actor {} has an empty attribute 'wcet'".format(v))
        except TypeError:
            # assume wcet can be interpreted as an integer
            try:
                wcet = int(wcet)
            except ValueError:
                raise SDFTransformError("Actor {} has an invalid attribute 'wcet'".format(v))
        
        if relate_start_times:
            for _, w, vw_data in hsdfg.out_edges( v, True ):
                mg.add_edge( v, w, weight = wcet, tokens = vw_data.get('tokens', 0))
        else:
            for u, _, uv_data in hsdfg.in_edges( v, True ):
                mg.add_edge( u, v, weight = wcet, tokens = uv_data.get('tokens', 0))

    return mg 

def fire( sdfg, firings_dict = None, **attr ):
    """ Fires actors in the SDF graph sdfg.
    Which actors to fire how many times is specified either as keyword arguments, or through
    the dictionary firings_dict.
    Keys specify which actors to fire, values specify how many times.
    Negative values "rewind" firings.

    NOTE: rate vectors are updated accordingly: if an actor with production rate vector [a,b,c]
    fires once, then the production rate vector will have changed into [b,c,a]
    """
    if firings_dict is not None:
        attr.update( firings_dict )

    for v in attr:
        firings = attr[ v ]
        if firings > 0:
            for _, w, data in sdfg.out_edges_iter( v, True ):
                prates = data.get('production')
                data['tokens'] += prates.sum(0,firings)
                data['production'] = prates[firings:]

            for v, _, data in sdfg.in_edges_iter( v, True ):
                crates = data.get('consumption')
                data['tokens'] -= crates.sum(0, firings)
                data['consumption'] = crates[firings:]

        elif firings < 0:
            # negative indices run from -1 to and including firings
            # subtract one to have correct bounds for the slices used below
            for _, w, data in sdfg.out_edges_iter( v, True ):
                prates = data.get('production')
                data['tokens'] -= prates.sum(firings, 0)
                data['production'] = prates[firings:]

            for v, _, data in sdfg.in_edges_iter( v, True ):
                crates = data.get('consumption')
                data['tokens'] += crates.sum(firings, 0)
                data['consumption'] = crates[firings:]

