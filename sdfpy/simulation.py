import heapq as hq
import networkx as nx
from fractions import Fraction
import math

import sdfpy.schedule as sched
import sdfpy.core as core

""" Simulates a self-timed execution of a CSDF graph.
self-timed means that actors fire as soon as they are enabled.

By running a self-timed execution, the throughput of the graph can be found
by searching for a periodic phase: in the periodic phase, each firing within a graph iteration follows a periodic regime.
"""

def periodic_state( graph, time, admissible = True ):
    result = nx.MultiDiGraph()
    schedule = sched.strictly_periodic_schedule( graph, admissible )

    # compute completed and active firings
    firings = dict()
    for v, data in graph.nodes_iter( data = True ):
        start_v, period_v = schedule[ v ]
        wcets = data['wcet']

        num_phases = data['phases']
        assert num_phases == len( wcets )

        started_firings =  math.floor(( time - start_v ) / period_v ) + 1
        completed_firings = math.floor(( time - wcets[ 0 ] - start_v ) / ( period_v * num_phases )) + 1
        for i in range( 1, num_phases ):
            first_firing = start_v + i * period_v
            completed_firings = min( completed_firings, math.floor(( time - wcets[ i ] - first_firing ) / ( period_v * num_phases )) + 1 )

        # compute active firings

        idx = completed_productions
        future = dict()
        while start_time <= time:
            # firing with <0-based index> = idx has started but not completed before time
            # add it as an active firing
            future[ completion_time ] = future.get( completion_time, 0 ) + 1
            idx += 1
            start_time += period_v
            completion_time = max( completion_time, start_time + wcets[ idx ] )

        firings[ v ] = completed_productions, future

        result.add_node( v,
            wcet = wcets[completed_productions:],
            active = future )

    # compute marking
    for v, w, key, data in graph.edges_iter( keys = True, data = True ):
        crates = data['consumption']
        prates = data['production']
        tokens = data['tokens']

        v_completed, _ = firings[ v ]
        w_completed, w_active = firings[ w ]

        completed_productions = v_completed
        started_consumptions = w_completed + sum( w_active.values())

        print("({}, {}): Production = {}, consumption = {}, tokens = {}".format( v, w, prates, crates, tokens ))

        if completed_productions > 0:
            tokens += prates.sum( 0, completed_productions )
        else:
            tokens -= prates.sum( completed_productions, 0 )

        if started_consumptions > 0:
            tokens -= crates.sum( 0, started_consumptions )
        else:
            tokens += crates.sum( started_consumptions, 0 )

        result.add_edge( v, w, key,
            production = prates[completed_productions:],
            consumption = crates[started_consumptions:],
            tokens = tokens )

    return core.SDFGraph( result )

def build_simulation_graph( graph ):
    """ In the simulation graph, each actor has a list of active (parallel) firings,
    ordered by the time they finish.
    In addition to this, the graph maintains a queue that contains future actor finish times.
    """
    g = nx.MultiDiGraph( queue = list(), time = 0 )
    for v, data in graph.nodes_iter( data = True ):
        data = data.copy()
        num_phases = data[ 'phases' ]
        active = data.get('active', {0: 0})

        g.add_node( v, data,
            latest = max( t for t in active ),
            blocked_on = set())

    for v, w, key, data in graph.edges_iter( keys = True, data = True ):
        crates = data['consumption']
        tokens = data['tokens']
        data = data.copy()
        g.add_edge( v, w, key, data )

        if tokens < crates[ 0 ]:
            g.node[ w ][ 'blocked_on' ].add( (v, w, key) )

    return g

def parallel_finish_times( min_wcet, wcets, numpar ):
    first = max(0, min( len( wcets ), numpar - 1 ))
    remaining = max(0, numpar - first)

    counts = dict()
    for i in range( first ):
        min_wcet = max( wcets[ i ], min_wcet )
        counts[ min_wcet ] = counts.get( min_wcet, 0 ) + 1

    # all remaining firings copmlete at t = min_wcet
    if remaining:
        min_wcet = max( wcets[ (numpar - 1) % len( wcets )], min_wcet )
        counts[ min_wcet ] = counts.get( min_wcet, 0 ) + remaining

    return counts

def start_self_timed( graph, node ):
    queue = graph.graph['queue']
    time = graph.graph['time']

    node_data = graph.node[ node ]
    blocked_on = node_data['blocked_on']
    wcets = node_data['wcet']
    period = node_data['phases']
    latest = node_data.get('latest', time)

    # clear blocked on, we refill it below
    blocked_on.clear()

    enabled_firings = None
    for u, v, key, data in graph.in_edges_iter( node, keys = True, data = True ):
        consumption = data['consumption']
        tokens = data['tokens']
        i = 0
        while tokens >= consumption[ i ]:
            tokens -= consumption[ i ]
            i += 1

        enabled_firings = i if enabled_firings is None else min( i, enabled_firings )

    for u, v, key, data in graph.in_edges_iter( node, keys = True, data = True ):
        consumption = data['consumption']

        # consume tokens
        tokens = data['tokens'] - consumption.sum( 0, enabled_firings )

        # obtain new consumption rate vector
        new_consumption = consumption[ enabled_firings: ]

        # update changed properties
        data.update(
            tokens = tokens,
            consumption = new_consumption)

        # update blocked channels
        if tokens < new_consumption[ 0 ]:
            blocked_on.add( (u, v, key) )

    # if the number of enabled firings is higher than the period P,
    # then all firings following the Pth firing will finish in parallel
    for wcet, count in parallel_finish_times( latest - time, wcets, enabled_firings ).items():
        latest = time + wcet
        hq.heappush( queue, ( latest, node, count ))

    # shift the wcet vector
    node_data.update(
        latest = latest,
        wcet = wcets[enabled_firings:])

def finish_actor( graph, node, count):
    node_data = graph.node[ node ]

    for v, w, key, data in graph.out_edges_iter( node, keys = True, data = True ):
        production = data.get('production')
        consumption = data.get('consumption')

        consumer_data = graph.node[ w ]
        consumer_blocked_on = consumer_data['blocked_on']

        tokens = data.get('tokens') + production.sum( 0, count )

        data.update(
            production = production[count:],
            tokens = tokens)

        if tokens >= consumption[ 0 ] and (v, w, key) in consumer_blocked_on:
            # unblock
            consumer_blocked_on.remove(  (v, w, key) )
            if not consumer_blocked_on:
                start_self_timed( graph, w )

    # update number of completed firings
    completed_firings = node_data.get('completed_firings', 0)
    node_data.update( completed_firings = completed_firings + count )

def compute_hash( marking, firings ):
    hash1 = hash( frozenset( marking.items()))
    hash2 = hash( frozenset( { k : frozenset( v.items()) for k, v in firings.items() }.items()))
    return hash((hash1, hash2))

def print_latex( graph, initial_marking = None, initial_firings = None, actors = list(), channels = list() ):
    # get the graph's repetition vector
    q = graph.repetition_vector()

    # choose an arbitrary actor in the graph
    ref_actor = next(iter(q.keys()))

    # get the state space
    state_space = sse_states( graph, initial_marking, initial_firings )

    print("\\begin{tabular}{r", end = "")
    for _ in range( len(actors) + len(channels) ):
        print("c", end = "")
    print("}")

    print("t", end = "")
    for a in actors:
        print(" & ${}$".format(a), end = "")

    for a, b, _ in channels:
        print(" & $\\marking{{{}{}}}$".format( a, b ), end = "")
    print("\\\\")

    def print_state( t, marking, firings ):
        print("{}".format( t ), end = "")
        for a in actors:
            bag = firings.get( a )
            if bag:
                print(" & $\\{", end = "")
                first = True
                for remaining in sorted( bag.keys() ):
                    for _ in range( bag[ remaining ] ):
                        print("{}{}".format( "" if first else ",", remaining ), end = "")
                        first = False
                print("\\}$", end = "")
            else:
                print(" & $\\varnothing$", end = "")

        for m in channels:
            mm = marking.get( m, 0 )
            print(" & {}".format( mm ), end = "")
        print("\\\\")

    # go over the state space and compare
    history = dict()
    completed_iterations = 0
    for g in state_space:
        t, marking, firings = state( g )

        print_state( t, marking, firings )
        ref_iterations = g.node[ ref_actor ].get( 'completed_firings', 0 ) // q[ ref_actor ]
        if ref_iterations > completed_iterations:
            h = compute_hash( marking, firings ) % 59
            matches = history.get( h, None )
            if matches is None:
                matches = history[ h ] = list()

            for time, completed, m, f in matches:
                if (m, f) == (marking, firings):
                    print("\\end{tabular}")
                    print("\nsame states: t = {} and t = {}".format( t, time ))
                    return Fraction( ref_iterations - completed, t - time )

            matches.append( (t, ref_iterations, marking, firings) )

        completed_iterations = ref_iterations
    else:
        raise Exception("Deadlock detected")

def find_throughput( graph, ref_actor = None, initial_marking = None, initial_firings = None ):
    # get the graph's repetition vector
    q = graph.repetition_vector()

    # choose an arbitrary actor in the graph
    if ref_actor is None:
        ref_actor = next(iter(q.keys()))

    # get the state space
    state_space = sse_states( graph, initial_marking, initial_firings )

    # go over the state space and compare
    history = dict()
    completed_iterations = 0
    for g in state_space:
        t, marking, firings = state( g )
        # print("t = {}: firings = {}, marking = {}".format( t, firings, marking ))
        ref_iterations = g.node[ ref_actor ].get( 'completed_firings', 0 ) // q[ ref_actor ]
        if ref_iterations > completed_iterations:
            h = compute_hash( marking, firings ) % 59
            matches = history.get( h, None )
            if matches is None:
                matches = history[ h ] = list()

            for time, completed, m, f in matches:
                if (m, f) == (marking, firings):
                    print("same states: t = {} and t = {}, transient = {}".format( t, time, completed ))
                    return Fraction( ref_iterations - completed, t - time )

            matches.append( (t, ref_iterations, marking, firings) )

        completed_iterations = ref_iterations
    else:
        raise Exception("Deadlock detected")

def sse_states( graph, initial_marking = None, initial_firings = None ):
    """ Runs a self-timed execution until a periodic phase is detected.

    initial_state:  a tuple (m, fs) of a dictionary m, which represents the marking of the graph, and a dictionary fs of active firings.
    """
    if initial_marking is None:
        # start with the initial marking
        marking = dict()
        for u, v, key, data in graph.edges_iter( keys = True, data = True ):
            marking[ (u, v, key) ] = data.get('tokens')
    else:
        # copy the marking
        marking = initial_marking.copy()

    if initial_firings is None:
        # no active firings
        firings = dict()
    else:
        # copy the initial_firings
        firings = initial_firings.copy()

    # build internal data structure used for simulation
    g = build_simulation_graph( graph )
    # start enabled actors
    for v, data in g.nodes_iter( data = True ):
        blocked_on = data['blocked_on']
        if not blocked_on:
            # enable 
            start_self_timed( g, v )
    
    yield g
    while step( g ):
        yield g

def state( graph ):
    # get remaining times for active firings
    remaining_firings = dict()

    current_time = graph.graph['time']

    queue = graph.graph['queue']
    for finish_time, actor, count in queue:
        delta = finish_time - current_time
        remaining = remaining_firings.get( actor, dict() )
        remaining[ delta ] = remaining.get( delta, 0 ) + count
        remaining_firings[ actor ] = remaining

    marking = dict()
    for u, v, key, data in graph.edges_iter( keys = True, data = True ):
        if data.get('tokens', 0) > 0:
            marking[ (u, v, key) ] = data['tokens']

    return current_time, marking, remaining_firings
    
def step( graph ):
    queue = graph.graph['queue']
    if not queue:
        # no active firings -> deadlocked
        return False

    finish_time, actor, count = hq.heappop( queue )
    t = finish_time
    graph.graph.update( time = finish_time )

    # print("t = {}".format( finish_time ))
    # print("  Finshing {} firings of actor {}".format( count, actor ))
    finish_actor( graph, actor, count )

    # find more firings that finish at t
    while queue:
        finish_time, actor, count = queue[ 0 ]
        if finish_time > t:
            break

        hq.heappop( queue )
        # print("  Finshing {} firings of actor {}".format( count, actor ))
        finish_actor( graph, actor, count )

    marking = dict()
    for u, v, key, data in graph.edges_iter( keys = True, data = True ):
        if data.get('tokens', 0) > 0:
            marking[ (u, v, key) ] = data['tokens']

    return True


