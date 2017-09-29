import networkx as nx
from random import sample, seed
from math import ceil
from collections import deque

class InfeasibleCycle(Exception):
    def __init__(self, cycle):
        self.cycle = cycle

    @property
    def cycle(self):
        return self.__cycle

    @cycle.setter
    def cycle(self, value):
        self.__cycle = value

class PositiveCycle(InfeasibleCycle):
    def __init__(self, cycle):
        super().__init__(cycle)

class NegativeCycle(InfeasibleCycle):
    def __init__(self, cycle):
        super().__init__(cycle)

def cycle_induced_subgraph(g):
    ''' Computes the subgraph that is maximally edge-induced by its cycles

    That is, every cycle that is in g is also in cycle_induced_subgraph(g).
    '''

    # gather all edges of SCCs
    return nx.DiGraph( ( edge for scc in nx.strongly_connected_component_subgraphs( g ) for edge in scc.edges_iter() ))

def dfs_edges( g, root = None ):
    if g.number_of_nodes() == 0: return
    visited = set()
    stack = list()

    root = root or next(g.nodes_iter())
    stack.append( (root, g.edges_iter( root )))
    while stack:
        (v, it) = stack[-1]
        visited.add( v )
        try:
            v, w = next(it)
            yield (v, w)
            if w not in visited:
                stack.append( (w, g.edges_iter( w )))
        except StopIteration:
            stack.pop()

def circuit_basis( g ):
    ''' Return a circuit basis for graph g.
    Graph g must be strongly connected.
    '''

    # maintain a multi-digraph to keep track of non-contracted edges
    h = nx.MultiDiGraph()

    # nodes in h are contractions of cycles in g
    # represented as tuples
    for v in g:
        h.add_node( (v, ))

    # add edges from g to h
    for u, v, in g.edges_iter():
        h.add_edge( (u, ), (v, ), edge = (u, v ) )

    # self-loops are fundamental circuits
    for u, v in g.selfloop_edges():
        assert u == v
        yield [(u, v)]
        h.remove_edge( (u,), (v,) )

    # span contains all cycles of g found so far    
    span = nx.DiGraph()

    # while the graph has non-contracted edges,
    # find a cycle using depth-first search
    while h.number_of_edges() > 0:
        # choose a random starting point
        root = next( h.nodes_iter())

        # run DFS from root
        parent = dict()
        queue = list()
        visited = dict()
        queue.append( (root, h.out_edges_iter( root, keys = True )))
        while queue:
            v, it = queue[-1]
            visited[v] = False
            try:
                _, w, idx = next( it )
                if w not in visited:
                    queue.append( (w, h.out_edges_iter( w, keys = True )))
                    parent[ w ] = v, idx
                elif not visited[ w ]:
                    # back edge, cycle found
                    cycle = list()
                    k = v
                    while k != w:
                        p, i = parent[ k ]
                        cycle.append( (p, k, i ))
                        k = p
                    cycle.reverse()
                    cycle.append( ( v, w, idx ))
                    break
            except StopIteration:
                # post visit v
                visited[v] = True
                queue.pop()
        else:
            assert False, "No cycle found, graph {} is not strongly connected".format( g.edges() )

        # reconstruct cycle in g from cycle in h
        cycle_in_g = list()
        u, v, idx = cycle[ -1 ]
        _, prev = h.get_edge_data( u, v )[ idx ].get('edge')

        for u, v, idx in cycle:
            a, b = h.get_edge_data( u, v )[ idx ].get('edge')

            if a != prev:
                # find path in span from prev to a
                nodes = next(nx.all_simple_paths( span, prev, a ))
                path = list(zip( nodes, nodes[1:] ))
                cycle_in_g.extend( path )
                span.add_edges_from( path )
                
            cycle_in_g.append( (a, b ))
            span.add_edge( a, b )

            h.remove_edge( u, v, idx )
            prev = b

        # yield cycle
        yield cycle_in_g

        if len( cycle ) > 1:
            # contract cycle
            # introduce new node
            ns = []
            for u, v, _ in cycle:
                ns.extend( list(u) )
            ns = tuple( ns )
            h.add_node( ns)

            for v, _, _ in cycle:
                for u, _, data in h.in_edges_iter( v, True ):
                    h.add_edge( u, ns, edge = data.get('edge'))

                for _, w, data in h.out_edges_iter( v, True ):
                    h.add_edge( ns, w, edge = data.get('edge'))

                h.remove_node( v )

def longest_distances( g, root, weight_attr = "weight" ):
    # maintain distances in dict
    distances = dict()
    distances[ root ] = 0

    # maintain shortest paths tree structure
    parents = dict()
    parents[ root ] = None

    # maintain a post order so that we can finish nodes
    # in topological order after each DFS
    post_order = list()

    queue = [ root ]
    while queue:
        # run DFS from nodes in queue
        visited = dict()
        while queue:
            # peek queue
            v = queue[ -1 ]
            distance_from_v = distances[ v ]
            try:
                # visit next child
                children = visited[ v ]
                try:
                    _, w, key, data = next( children )
                    weight = data.get( weight_attr )
                    distance_to_w = distances.get( w )
                    distance_via_v = distance_from_v + weight

                    admissible = (distance_to_w is None) or (distance_via_v > distance_to_w)
                    if w not in visited and admissible:
                        distances[ w ] = distance_via_v
                        parents[ w ] = v, w, key
                        queue.append( w )
                    elif admissible:
                        # w was visited before. if w is an ancestor of v,
                        # then we have found a negative cycle
                        children_w = visited[ w ]
                        if children_w is not None:
                            # w is an ancestor of v -> negative cycle found
                            # trace edges back to w
                            path = deque([ (v, w, key) ])
                            p = v
                            while p != w:
                                k, _, key = parents[ p ]
                                path.appendleft( (k, p, key) )
                                p = k

                            raise PositiveCycle( list( path ))
                except StopIteration:
                    # post visit v
                    post_order.append( v )

                    # indicate that v is post-visited
                    visited[ v ] = None
                    queue.pop()
            except KeyError:
                # not visited yet, pre-visit v
                visited[ v ] = g.out_edges_iter( v, keys = True, data = True )

        # go over nodes in reverse post order (i.e. topological order)
        visited = dict()
        while post_order:
            v = post_order.pop()
            visited[ v ] = -1
            distance_from_v = distances[ v ]

            for _, w, key, data in g.out_edges_iter( v, keys = True, data = True ):
                weight = data.get( weight_attr )
                distance_to_w = distances[ w ]
                distance_via_v = distance_from_v + weight

                if distance_via_v > distance_to_w:
                    distances[ w ] = distance_via_v
                    parents[ w ] = v, w, key

                    pos_in_queue = visited.get( w )
                    if pos_in_queue is not None and pos_in_queue < 0:
                        visited[ w ] = len( queue )
                        queue.append( w )

    return parents, distances

def shortest_distances( g, root, weight_attr = "weight" ):
    # maintain distances in dict
    distances = dict()
    distances[ root ] = 0

    # maintain shortest paths tree structure
    parents = dict()
    parents[ root ] = None

    # maintain a post order so that we can finish nodes
    # in topological order after each DFS
    post_order = list()

    queue = [ root ]
    while queue:
        # run DFS from nodes in queue
        visited = dict()
        while queue:
            # peek queue
            v = queue[ -1 ]
            distance_from_v = distances[ v ]
            try:
                # visit next child
                children = visited[ v ]
                try:
                    _, w, key, data = next( children )
                    weight = data.get( weight_attr )
                    distance_to_w = distances.get( w )
                    distance_via_v = distance_from_v + weight

                    admissible = (distance_to_w is None) or (distance_via_v < distance_to_w)
                    if w not in visited and admissible:
                        distances[ w ] = distance_via_v
                        parents[ w ] = v, w, key
                        queue.append( w )
                    elif admissible:
                        # w was visited before. if w is an ancestor of v,
                        # then we have found a negative cycle
                        children_w = visited[ w ]
                        if children_w is not None:
                            # w is an ancestor of v -> negative cycle found
                            # trace edges back to w
                            path = deque([ (v, w, key) ])
                            p = v
                            while p != w:
                                k, _, key = parents[ p ]
                                path.appendleft( (k, p, key) )
                                p = k

                            raise NegativeCycle( list( path ))
                except StopIteration:
                    # post visit v
                    post_order.append( v )

                    # indicate that v is post-visited
                    visited[ v ] = None
                    queue.pop()
            except KeyError:
                # not visited yet, pre-visit v
                visited[ v ] = g.out_edges_iter( v, keys = True, data = True )

        # go over nodes in reverse post order (i.e. topological order)
        visited = dict()
        while post_order:
            v = post_order.pop()
            visited[ v ] = -1
            distance_from_v = distances[ v ]

            for _, w, key, data in g.out_edges_iter( v, keys = True, data = True ):
                weight = data.get( weight_attr )
                distance_to_w = distances[ w ]
                distance_via_v = distance_from_v + weight

                if distance_via_v < distance_to_w:
                    distances[ w ] = distance_via_v
                    parents[ w ] = v, w, key

                    pos_in_queue = visited.get( w )
                    if pos_in_queue is not None and pos_in_queue < 0:
                        visited[ w ] = len( queue )
                        queue.append( w )

    return parents, distances

