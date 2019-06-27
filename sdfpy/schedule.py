import networkx as nx
import math

import sdfpy.transform as transform
import sdfpy.mcr as mcr
import sdfpy.core
import sdfpy.graphs as graphs
from fractions import gcd

""" A schedule defines the times at which actors fire.
Each actor fires periodically, but the periods of two actors may vary.
An actor is said to fire strictly periodically if the period is equal to one.

Given a schedule, one can derive the number of tokens on a channel as a function of elapsed time.
This allows one to identify slack time: the time between the enabling of an actor and its start.
By eliminating slack time, the schedule becomes more complex as its periodicity increases. At the same time,
however, the firing rate of actors may increase.

A schedule is a dictionary with a key for each actor in the graph.
The associated value is a
"""

def strictly_periodic_schedule( graph, admissible = True ):
    # transform the graph to its (pessimistic) single-rate aproximation
    apx = transform.single_rate_apx( graph, admissible )

    # transform the single-rate apx to a marked graph
    mg = transform.single_rate_as_marked_graph( apx, True )

    # compute max. cycle ratio for the approximation
    cycle_time, cycle, *_ = mcr.max_cycle_ratio( mg )

    # create a weighted graph representation from mg
    wg = nx.MultiDiGraph()
    for u, v, data in mg.edges_iter( data = True ):
        wg.add_edge( u, v, weight = data.get('weight', 0) - data.get('tokens', 0) * cycle_time )

    # choose a critical node
    (a, *_), *_ = cycle

    # compute the longest distances from a critical node
    parents, eigen_vector = graphs.longest_distances( wg, a )

    # compute the period for each actor
    periods = { v : (graph.modulus() // graph.repetition_vector()[ v ]) * cycle_time for v in graph }

    # transform the eigenvector to a periodic schedule for the graph
    # first element in tuple = time of first firing
    result = { v : (eigen_vector[ v ] + ( graph.modulus() // graph.repetition_vector()[ v ] - 1 ) * cycle_time, periods[ v ]) for v in periods }

    # ensure that time of first firing is non-negative
    min_start_time, _ = min( result.values() )
    return { v : (eigen_vector[ v ] - min_start_time + ( graph.modulus() // graph.repetition_vector()[ v ] - 1 ) * cycle_time, periods[ v ]) for v in periods }

