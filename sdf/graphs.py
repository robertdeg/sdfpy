import networkx as nx
from random import sample, seed
from math import ceil

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


