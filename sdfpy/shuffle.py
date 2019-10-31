# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 15:32:53 2019

@author: Robert de Groote
"""
import networkx as nx

class SPTreeNode(object):
    def __init__(self, distance = None):
        self.parent = None
        self.adopter = None
        self.distance = distance
        self.changed = False
        self.queued = False
        
    def is_improvement(self, d):
        if self.distance is None:
            return True
        else:
            return d < self.distance

class LPTreeNode(object):
    def __init__(self, distance = None):
        self.parent = None
        self.distance = distance
        self.new_parent = None
    
    def policy_changed(self):
        if self.parent is None:
            return False
        
        return self.parent != self.new_parent
    
    def improves_policy(self, new_parent, new_distance):
        if new_distance > self.distance:
            self.new_parent = new_parent
            self.distance = new_distance
            return True
        else:
            return False

    def update_policy(self):
        self.parent = self.new_parent
        
def __keyed_edges(g, nbunch = None, data = False):
    if g.is_multigraph():
        return g.edges(nbunch, keys = True, data = data)
    elif data:
        return ((u, v, -1, d) for u, v, d in g.edges(nbunch, data = True))
    else:
        return ((u, v, -1) for u, v in g.edges(nbunch))
    
''' Shortest paths algorithm that builds incrementally
    better shortest path policies.
    A shortest path policy is simply the current best known shortest paths
    tree.
    Policy updates are done in such a way that policy-changing updates
    are postponed until all policy-preserving updates have been made.
    Consequently, in case the policy is very inaccurate (such is the case
    at the first iteration), the algorithm behaves as a breadth-first search.
    As (parts of) the policy becomes more accurate, the algorithm behaves
    more as a depth-first search.
    This could be sped up a bit by running a full DFS at the first iteration,
    building a spanning policy in the process. As a nice consequence, this would
    also mean that acyclic graphs are "solved" in the first iteration.
'''
def shortest_paths(g, root, weight = 'weight'):
    # build a first longest paths tree, rooted in root, using DFS
    # mark relaxed but non-visited nodes
    # restart DFSs from marked nodes
    # postpone DFS at nodes for which visitor is not the parent
    
    # per node in the graph, its parent in the current
    # longest paths tree
    
    # the longest distances in the current longest paths tree
    lpt = dict()
    for v in g:
        lpt[v] = SPTreeNode()
        
    lpt[root] = SPTreeNode(0)
    
    post_order = list()
    previsits = 0
    
    # DFS queue
    queue = [(root, None)]
    # Outer loop: per iteration, a depth-first delimited search followed
    # by a reversed post order visit
    while queue:
        visited = set()
        # DFS loop:
        #  per iteration, a depth-first delimited search is run
        #  from each node in the queue
        while queue:
            queue2 = list()
            # Inner loop: depth-first delimited search
            # depth-first delimited searches from adopted children
            # are postponed 
            while queue:
                # pop the current node and its edge-iterator
                v, it = queue[-1]
                node_v = lpt[v]
                # check if we're pre-visiting v
                if it is None:
                    # pre visit v
                    if v in visited:
                        raise Exception("Already visited!")
                    
                    previsits += 1
                    visited.add( v )
                    node_v.parent = node_v.adopter
                    it = iter( g.edges( v, data = True ))
                    queue[-1] = v, it
        
                node_v.changed = node_v.queued = False
                for _, w, data in it:
                    # see if the distance to w using this edge is longer
                    # than its current distance
                    node_w = lpt.get(w, SPTreeNode())
                    dw = node_v.distance + data[weight]
                    if node_w.is_improvement( dw ):
                        # update distance
                        node_w.distance = dw
                        node_w.adopter = v
                        node_w.changed = True
                        
                        # did we already visit w?
                        if w not in visited and not node_w.queued:
                            # either continue DFS with w,
                            # or postpone DFS rooted in w
                            # Is v the parent of w?
                            if node_w.parent == v:
                                # continue DFS if w has not been visited yet
                                queue.append( (w, None) )
                                break
                            else:
                                # postpone visiting w
                                queue2.append( (w, None) )
                                node_w.queued = True
                        elif node_w.parent != v:
                            # disassemble the subtree rooted in w, ma

                else:
                    # post visit v
                    queue.pop()
                    post_order.append(v)
                    node_v.queued = False
        
            # run DFS from postponed
            queue = queue2
                
        # run reverse post order traversal
        while post_order:
            v = post_order.pop()
            node_v = lpt[ v ]
            node_v.parent = node_v.adopter
            
            # check outgoing edges
            if node_v.changed:
                previsits += 1
                for _, w, data in g.edges(v, data = True):
                    node_w = lpt.get(w, SPTreeNode())
                    dw = node_v.distance + data[weight]
                    if node_w.is_improvement( dw ):
                        node_w.distance = dw
                        node_w.adopter = v
                        node_w.changed = True
                        if not node_w.queued:
                            queue.append( (w, None) )
                            node_w.queued = True
                        
            node_v.changed = False

    # return distances
    distances = dict()
    for v in g:
        distances[v] = lpt[ v ].distance
        
    return distances, previsits

if __name__ == "__main__":
    with open("/Users/grootee/graphs/grid_200_500_1", "r") as f:
        g = nx.DiGraph()
        for l in f.readlines():
            contents = l.split()
            if contents[0] == 'a':
                src = int(contents[1])
                dst = int(contents[2])
                w = int(contents[3])
                g.add_edge(src, dst, weight = w)

            elif contents[0] == 'n':
                root = int(contents[1])

        print("Root: {}".format(root))
        print("Graph has {} nodes, {} edges".format(g.number_of_nodes(), g.number_of_edges()))

        distances, scans = shortest_paths(g, root)
        print("Scans per vertex: {:.2f}".format(scans / g.number_of_nodes()))


