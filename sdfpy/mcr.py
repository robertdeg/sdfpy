import networkx as nx

from sdfpy.graphs import PositiveCycle, longest_distances
from sdfpy.priorityq import PriorityQueue
from sdfpy.forest import Forest
from collections import deque
from fractions import Fraction

class pdistance( tuple ):
    def __new__(self, weight, tokens):
        return super().__new__(self, (weight, tokens))

    def __add__(self, value):
        return pdistance(self[0] + value[0], self[1] + value[1])
            
    def __sub__(self, value):
        return pdistance(self[0] - value[0], self[1] - value[1])

    def eval(self, ratio):
        return self[0] - self[1] * ratio

class InfeasibleException( PositiveCycle ):
    def __init__(self, cycle):
        super().__init__( cycle )

def max_cycle_ratio( g, estimate = None ):
    maxratio, arg_cycle = None, None
    for scc in nx.strongly_connected_component_subgraphs( g ):
        root = next( iter( scc.nodes() ))
        scc_mcr, cycle = compute_mcr_component( scc, root, estimate )
        if scc_mcr is None:
            continue

        if maxratio is None or scc_mcr > maxratio:
            maxratio = scc_mcr
            arg_cycle = cycle

    forest = Forest()
    for scc in nx.strongly_connected_component_subgraphs( g, False ):
        if scc.number_of_edges() == 0:
            continue

        for ( v, w, scc_data ) in scc.edges( data = True ):
            data = g.get_edge_data( v, w )

            # negate weight so that we can construct a longest paths tree for the current solution
            scc_data['w'] = data.get( 'weight', 0 ) - data.get( 'tokens', 0 ) * maxratio

        root = w
        parents, _ = longest_distances( scc, root, 'w' )
        for child in parents:
            in_edge = parents.get( child )
            if in_edge is not None:
                forest.add_edge( *in_edge )

    return maxratio, arg_cycle, forest

def compute_mcr_component( g, root, estimate = None ):
    ''' Computes the maximum cycle ratio of g.
    NOTES:
        - The weight on each edge must be non-negative
        - The number of tokens on each edge must be non-negative.
        - The graph is assumed to be strongly connected.
    '''

    # initialize:
    distances = {}
    queue = PriorityQueue()

    if estimate is None:
        # determine lower bound for mcr
        estimate = 1
        for (v, w, data) in g.edges(data=True):
            tokens = data.get('tokens', 0)
            weight = data.get('weight', 0)
            estimate = estimate + max(0, weight)

    initial_graph = nx.MultiDiGraph()
    
    # construct graph with non-parametric path weights
    for v in g:
        initial_graph.add_node( v )

    for v, w, key, data in nx.MultiDiGraph(g).edges(keys = True, data = True):
        tokens = data.get('tokens', 0)
        weight = data.get('weight', 0)
        initial_graph.add_edge( v, w, key, weight = weight - tokens * estimate, dist = pdistance(weight, tokens))

    try:
        parents, _ = longest_distances( initial_graph, root )
        # build tree from parents
        tree = Forest()
        for child in parents:
            in_edge = parents.get( child )
            if in_edge is not None:
                tree.add_edge( *in_edge )

        distances[root] = pdistance(0, 0)
        if root in tree:
            for v, w, key in tree.pre_order_edges( root ):
                dv = distances[ v ]
                data = initial_graph.get_edge_data( v, w, key )
                distances[ w ] = dv + data.get('dist')

    except PositiveCycle as ex:
        raise InfeasibleException( ex.cycle )

    # fill priority queue:
    # go over all nodes and compute their key
    # print("Distances from root {}: {}".format(root, distances))
    for v in distances:
        update_node_key( initial_graph, v, distances, queue )

    # pivot until cycle is found
    while len(queue) > 0:
        (node, (ratio, (v, w, vw_key))) = queue.pop()
        delta = distances[v] + initial_graph.get_edge_data(v, w, vw_key)['dist'] - distances[w]

        for j in tree.pre_order(w):
            # update parametric distance to j
            distances[j] += delta

            if v == j:
                # j is reachable from v -> there's a cycle!
                is_multi = g.is_multigraph()
                path = deque([ (v, w, vw_key) if is_multi else (v, w) ])
                p = v
                while p != w:
                    k, _, key = tree.parent( p )
                    path.appendleft( (k, p, key) if is_multi else (k, p) )
                    p = k
                return -ratio, list( path )
            
            # update successors of j; the node key of a successor k can only increase!
            for _, k, jk_key, data in initial_graph.out_edges(j, keys = True, data = True):
                # update priority of (j, k)
                ratio_k = None
                if k in queue:
                    ratio_k, _ = queue[k]

                delta_k = distances[j] + data['dist'] - distances[k]
                if delta_k[1] > 0:
                    r = -Fraction(delta_k[0], delta_k[1])
                    if ratio_k is None or r < ratio_k:
                        queue[k] = (r, (j, k, jk_key))

            # recompute vertex key of j
            update_node_key( initial_graph, j, distances, queue )

        tree.add_edge( v, w, vw_key )
    else:
        # no cycle found, any period is admissible
        # Note that this implies that the graph is acyclic
        return None, None

def update_node_key( g, node, pdistances, queue ):
    maxratio, argmax = None, None
    # go over all incoming edges of the node
    for u, v, key, data in g.in_edges( node, keys = True, data = True ):
        if u in pdistances:
            delta = pdistances[u] + data['dist'] - pdistances[v]
            # print("Delta for {} = {}".format((u, v), delta))
            if delta[1] > 0:
                ratio = Fraction(delta[0], delta[1])
                if argmax is None or ratio > maxratio:
                    maxratio = ratio
                    argmax = u, v, key

    # store the node key for v
    if argmax is not None:
        queue[node] = (-maxratio, argmax)
    elif node in queue:
        del queue[node]

    return maxratio
