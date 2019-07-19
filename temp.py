# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import sdfpy.core as core
import sdfpy.schedule as sched
import sdfpy.transform as transform
import networkx as nx

# Load the SDF graph
sdfg = core.load_sdf_yaml('examples/csdfg-small.yaml')

# Compute a single-rate approximation for the graph
apx = transform.single_rate_apx( graph, admissible )

# transform the single-rate apx to a marked graph
mg = transform.single_rate_as_marked_graph( apx, True )

# compute max. cycle ratio & critical cycle for the approximation
cycle_time, cycle, forest = mcr.max_cycle_ratio( mg )

# MCR => result should be a LPP tree that can be queried for the longest
# path (from the root of the tree) to a given node

# To build an all-pairs LPP forest, compute the MCR once, and plug this value
# in as a parameter for the LPP tree computations of the other roots



# In the critical cycle, compute for each actor
# the latency-rate characterization, for different possible
# decompositions into phases

# 
sps = sched.strictly_periodic_schedule(sdfg)
