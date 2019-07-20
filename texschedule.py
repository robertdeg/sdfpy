import sys
import networkx as nx
import sdfpy.core as core
import sdfpy.mcr as mcr
import sdfpy.transform as trans
import sdfpy.schedule as schedule
import sdfpy.simulation as sse
import math
from sdfpy.integers import lcm
from fractions import Fraction

def lcm_list( xs ):
    l = 1
    for x in xs:
        l = lcm( l, x )
    return l

def max_parallelism( sdfg, time_table ):
    # go over times in time_table
    ls = list()
    table = dict()
    for v in sorted( time_table ):
        table[ v ] = (0, list())
        w = sdfg.node[ v ]['wcet'][0]
        starts = time_table[ v ]
        for s in starts:
            ls.append( (s, 1, v) )
            ls.append( (s + w, -1, v) )

    occupied = set()
    max_par = 0
    for t, i, v in sorted( ls ):
        if i > 0:
            _, xs = table[ v ]
            # find free spot
            j = 0
            while j in occupied:
                j += 1
            occupied.add( j )
            xs.append( (j, t) )
        else:
            finished, xs = table[ v ]
            if len(xs) > 0:
                a, b = xs[ finished ]
                xs[ finished ] = a, b, t
                table[ v ] = finished + 1, xs
                # free spot
                occupied.remove( a )

        max_par = max( max_par, len( occupied ))

    #import pdb; pdb.set_trace()
    return { v : table[ v ][1] for v in table }, max_par

def tex_schedule( sdfg, time_table, t_from, t_until ):
    # determine the LCM of all periods
    table, max_par = max_parallelism( sdfg, time_table )

    # set up meta
    nodes = sorted(sdfg.nodes())

    # set up styles
    styles = [
        "\\tikzstyle{firing} = [fill=blue!40, rounded corners=3pt];",
        "\\tikzstyle{lbl} = [font=\\small];",
        "",
        ""]

    # set up grid
    grid = [
        "\\draw[black!40] (0, 0) grid ({}, {}); ".format( t_until + 0, max( max_par, sdfg.number_of_nodes() )),
        ""]

    # write axis
    axis = [
        "\\draw[->, black, line width=1.5pt] (0, 0) -- ({}, 0);".format( t_until - t_from + 1 ),
        "\\draw[-, black, line width=1.5pt] (0, 0) -- (0, {});".format( max( max_par, sdfg.number_of_nodes() )),
        "\\foreach \\i in {{{},{},...,{}}} {{".format( t_from, t_from + 1, t_until ),
        "    \\draw[black, line width=1pt] (\\i, 0) -- +(0, -2.5pt);",
        "    \\node[below=4pt] at (\\i-{}, 0) {{\\i}};".format(t_from),
        "}",
        ""]

    # write blocks
    blocks = list()
    for v in table:
        runs = table[ v ]
        for row, start, finish in runs:
            blocks.append(
                "\\draw[firing] ({}, {}) rectangle ({}, {});".format( start - t_from, row, min(finish, t_until) - t_from, row + 1 ))
            blocks.append(
                "\\node[lbl] at ({}, {}) {{{}}};".format( (start + finish) / 2 - t_from, row + 0.5, v ))

    return styles + grid + axis + blocks

def compute_schedule( sdfg, stype, t_from = 0, t_until = 100 ):
    timetable = dict()
    if stype == "self-timed":
        # self-timed execution
        state_space = sse.sse_states( sdfg )
        for g in state_space:
            t, _, remaining = sse.state( g )
            if t > t_until:
                break

            if t >= t_from:
                for v in remaining:
                    wcet = sdfg.node[v]['wcet'][0]
                    bag = remaining[ v ]
                    parallel = bag.get( wcet )
                    if parallel is not None:
                        timetable[ v ] = timetable.get( v, list() ) + parallel * [ t ]
        return timetable, None
        
    elif stype == "sps":
        sps = schedule.strictly_periodic_schedule( sdfg )
        q = sdfg.repetition_vector()
        import pdb; pdb.set_trace()
        for v in sps:
            qv = q[ v ]
            t0, pv = sps[ v ]
            period = qv * pv
            firings = math.ceil(Fraction(t_until - t0, pv))
            timetable[ v ] = [ t0 + k * pv for k in range( firings ) ]

        return timetable, period
    elif stype == "optimal":
        hsdfg = trans.single_rate_equivalent( sdfg )
        mg = trans.single_rate_as_marked_graph( hsdfg )
        ratio_exact, cycle = 0, 0
        try:
            ratio_exact, cycle, forest = mcr.max_cycle_ratio( mg )
            print("Cycle: {}, MCR: {}".format( cycle, ratio_exact ))
            for root in forest.roots():
                # compute distances from root
                pass
        except Exception:
            pass
    else:
        return None, None

def write_latex( f, sdfg, timetable, t_from, t_until ):
    f.write('\n'.join([
        "\\documentclass{standalone}",
        "\\usepackage{tikz}",
        "\\usetikzlibrary{positioning,calc}",
        "\\begin{document}",
        "\\begin{tikzpicture}"] +
        tex_schedule( sdfg, timetable, t_from, t_until ) +
       ["\\end{tikzpicture}",
        "\\end{document}"]))

if __name__ == '__main__':
    if ( len(sys.argv) < 2 ):
        print( "Missing required argument: input-file" )
        sys.exit()

    if ( len(sys.argv) < 3 ):
        print( "Missing required argument: output-file" )
        sys.exit()

    sdfg = core.load_sdf_yaml( sys.argv[ 1 ] )
    print("Repetition vector: {}".format( sdfg.repetition_vector() ))
    timetable, period = compute_schedule( sdfg, "sps", 0, 91)

    # write latex
    with open(sys.argv[ 2 ], "w") as texfile:
        write_latex( texfile, sdfg, timetable, 0, 60 )

