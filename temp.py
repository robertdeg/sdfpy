# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import sdfpy.core as core
import sdfpy.schedule as sched
import networkx as nx

sdfg = core.load_sdf_yaml('examples/csdfg-small.yaml')
sps = sched.strictly_periodic_schedule(sdfg)
