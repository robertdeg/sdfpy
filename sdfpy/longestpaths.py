# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 15:32:53 2019

@author: Robert de Groote
"""
import networkx as nx

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


