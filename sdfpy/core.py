from math import ceil
from functools import reduce
import networkx as nx
import json
import yaml
import sys
import re
import pdb
from fractions import Fraction
from math import gcd
from sdfpy.integers import lcm
from sdfpy.graphs import dfs_edges
import xml.etree.ElementTree as etree

class SDFGraph( nx.MultiDiGraph ):
    """ A general class for synchronous dataflow graphs.

        The widest class that can be modelled is cyclo-static dataflow (CSDF).
        A CSDF graph is a directed graph, in which nodes are allowed to have self-loops.
        Edges contain an integer number of tokens, nodes can be `fired', which results in tokens to be
        moved (consumed) from incoming edges, onto (produced) outgoing edges.

        So-called `rates' specify the number of tokens that are produced or consumed per firing of a node.
        These rates may vary per firing: the number of tokens produced onto an edge (v, w), by a firing of node v,
        is given by the production rate vector of that edge.
        Likewise, the number of tokens consumed from an edge (v, w), by a firing of node w, is specified by the
        consumption rate vector of (v, w).
        The production or consumption rate associated with the k-th firing of node v varies cyclically, and is given
        by entry (k mod N), where N is the length of the corresponding vector.

        A firing takes time. The minimum amount of time between the consumption and production of tokens (which is instantenous),
        by some firing of node v, is specified by the `execution time' associated with that firing. This execution time
        may, just like the rates, vary cyclically, and this cyclically varying pattern is defined by the node's
        execution time vector. A firing of a node is not allowed to produce tokens before any of its previous firings have
        produced their output tokens. This ensures that no tokens can `overtake' each other.

        There are thus three kinds of cyclically varying behaviours associated with a node, defined by the production, consumption,
        and execution time vectors. The hyperperiod of these three patterns is referred to as the `number of phases' of the node.

        A firing of a node is legal if the firing does not leave a negative number of tokens on the node's incoming edges.
        If we simulate legal firings indefinitely, there are a number of things that can happen:
        First of all, at some point in time a situation may be reached where no more legal firings can be simulated. This means
        that the graph is `deadlocked'.
        Secondly, it may happen that, on some cycle, the number of legal firings that one can simulate simultaneously grows indefinitely.
        If we can ensure that the first thing never happens, by adding sufficiently many tokens to the graph prior to starting
        the simulation, while the second thing does not occur on any of its cycles, then the graph is said to be `consistent'.
        Consistency is an important property, as for consistent graph one can compute a periodic schedule, and determine the
        capacity that is required for every edge, such that the schedule can be executed in bounded memory.

        Production and consumption rates, as well as number of tokens, are stored as (private) properties associated with edges.
        Execution times are stored internally per node.
    """
    def __init__(self, graph):
        super().__init__()
        self.__build( graph )
        q, s, tpi = self.__check_consistency()
        self.__q = q
        self.__s = s
        self.__tpi = tpi

    def repetition_vector(self):
        return self.__q

    def normalisation_vector( self ):
        return self.__s

    def modulus( self ):
        return self.__tpi

    def predecessor_fun( self, v, w, key = 0 ):
        return self[v][w][key].get('pred')

    def to_JSON(self):
        actors = list()
        for v, data in self.nodes( data = True ):
            wcet = data.get('wcet', 0)
            actors.append( dict(name = str(v), wcet = wcet if len(wcet) > 1 else wcet[0] ))

        channels = list()
        for v, w, data in self.edges( data = True ):
            d = dict(to = str(w))
            d['from'] = str(v)
            prates = data.get('production')
            d['production'] = prates if len(prates) > 1 else prates[0]

            prates = data.get('consumption')
            d['consumption'] = prates if len(prates) > 1 else prates[0]

            d['tokens'] = data.get('tokens')

            channels.append(d)

        root = dict(type='csdf', actors=actors, channels=channels)
        return json.dumps(root, sort_keys = True, indent = 2)

    def __successor_fun( prates, crates, tokens ):
        if len( prates ) > 1:
            raise Exception("Not implemented yet")
        elif len( crates ) > 1:
            raise Exception("Not implemented yet")
        else:
            crate = crates[ 0 ]
            prate = prates[ 0 ]
            return lambda k: (( (k - 1) * prate + tokens ) // crate ) + 1

    def __predecessor_fun( prates, crates, tokens ):
        if len( prates ) > 1:
            return lambda k: max(
                [ ((( crates.sum( 0, k ) - 1 - tokens - prates.sum(0, i)) // prates.sum() ) * plen + i + 1)
                for i in range(0, plen) ])
        elif len( crates ) > 1:
            return lambda k: (( crates.sum( 0, k ) - 1 - tokens ) // prates.sum() ) + 1
        else:
            crate = crates[ 0 ]
            prate = prates[ 0 ]
            return lambda k: (( k * crate - 1 - tokens ) // prate ) + 1

    def __build( self, graph ):
        for v, data in graph.nodes( data = True ):
            wcet = SDFGraph.__validate_vector( v, data.get('wcet', 0), 'wcet' )
            super().add_node( v, wcet = wcet, phases = len( wcet ))

        for u, v, data in graph.edges( data = True ):
            production = SDFGraph.__validate_vector( (u, v), data.get('production', 1), 'production rate' )
            consumption = SDFGraph.__validate_vector( (u, v), data.get('consumption', 1), 'consumption rates' )
            g_uv = gcd( production.sum(), consumption.sum() )

            try:
                tokens = int(data.get('tokens', 0))
            except ValueError:
                raise SDFParseError("Channel {} has an invalid token specification: {}".format( (u, v), data['tokens'] ))

            super().add_edge( u, v, production = production, consumption = consumption, tokens = tokens,
                gcd = g_uv,
                pred = SDFGraph.__predecessor_fun( production, consumption, tokens ))

            if 'capacity' in data:
                try:
                    capacity = int( data['capacity'] )
                    if capacity < tokens: raise Exception("More tokens on channel {} than specified capacity".format((u, v)))

                    # create reverse channel (w, v)
                    super().add_edge(v, u, production = consumption, consumption = production, tokens = capacity - tokens,
                        gcd = g_uv,
                        pred = SDFGraph.__predecessor_fun( consumption, production, capacity - tokens ))
                        # succ = SDFGraph.__successor_fun( consumption, production, capacity - tokens ))

                except ValueError:
                    # create reverse channel (w, v)
                    raise SDFParseError("Channel {} has an invalid capacity specification: {}".format( (u, v), data['capacity'] ))

        # update phases
        for v, data in self.nodes( data = True ):
            phases = data['phases']
            for u, _, edge_data in self.in_edges( v, True ):
                phases = lcm( phases, len( edge_data['consumption'] ))

            for _, w, edge_data in self.out_edges( v, True ):
                phases = lcm( phases, len( edge_data['production'] ))

            data['period'] = data['phases'] = phases

    def add_node(self, n, attr_dict = None, **attr):
        if attr_dict is not None:
            attr_dict.update( attr )
        else:
            attr_dict = attr

        assert n not in self.node, "Node already present, remove first"

        wcet = attr_dict['wcet'] = SDFGraph.validate_vector(n, attr_dict.get('wcet', 0), 'wcet')
        super().add_node( n, attr_dict)

        # set period and phases
        self.node[ n ]['period'] = self.node[ n ]['phases'] = len(wcet)

    def period(self, v):
        return self.node[v].get('period')

    def phases( self, v ):
        return self.node[v].get('phases')

    def rates( self, v, w ):
        data = self[v][w]
        return data['prates'], data['crates']

    def tokens( self, v, w ):
        data = self[v][w]
        return data['tokens']
        
    def print( self ):
        print("Nodes:")
        for v, data in self.nodes( data = True ):
            print("  {} with wcet {}".format(v, list(data.get('wcet'))))
        print("Edges:")
        for v, w, data in self.edges( data = True ):
            print("  ({}, {}) with production rate {}, consumption rate {}, and {} tokens".format(
                v, w, list(data.get('production')), list(data.get('consumption')), data.get('tokens')))

    def add_edge(self, u, v, attr_dict = None, **attr):
        assert attr_dict is None, "FIXME: add_edge does not deal with attr_dict"

        production = attr['production'] = SDFGraph.validate_vector( (u, v), attr.get('production', 1), 'production rate' )
        assert type(production) is cyclic

        # update phases
        try:
            phases_u = self.node[u].get('phases', 1)
            self.node[ u ]['phases'] = lcm( len(production), phases_u )
        except KeyError:
            super().add_node( u, wcet = cyclic( 0 ), phases = len( production ), period = 1 )

        consumption = attr['consumption'] = SDFGraph.validate_vector( (u, v), attr.get('consumption', 1), 'consumption rates' )
        assert type(consumption) is cyclic

        # update phases
        try:
            phases_v = self.node[v].get('phases', 1)
            self.node[ v ]['phases'] = lcm( len(consumption), phases_v )
        except KeyError:
            super().add_node( v, wcet = cyclic( 0 ), phases = len( consumption ), period = 1 )

        try:
            tokens = int(attr.get('tokens', 0))
            assert tokens >= 0
            attr['tokens'] = tokens
        except ValueError:
            raise SDFParseError("Channel {} has an invalid number of tokens: {}".format( (u, v), attr['tokens'] ))

        if (self.has_edge(u, v)):
            # FIXME: replace parallel edges by single edge
            # insert auxilary node

            pr = attr.get('production')
            cr = attr.get('consumption')
            toks = attr.get('tokens')

            aux, c = "aux_0", 0
            while aux in self.node:
                c += 1
                aux = "aux_{}".format(c)

            self.add_node( aux, wcet = 0 )
            self.add_edge(u, aux, production = pr, consumption = 1, tokens = toks)
            self.add_edge(aux, v, production = 1, consumption = cr)
            print("WARNING: added node {} to prevent parallel edge ({}, {})".format( aux, u, v ))
        else:
            super().add_edge(u, v, attr_dict, **attr)

        if 'capacity' in attr:
            try:
                capacity = int(attr['capacity'])
                if capacity < tokens: raise Exception("Tokens on channel {} violates specified capacity".format((u, v)))

                del self.get_edge_data(u, v)['capacity']

                # create reverse channel (w, v)
                self.add_edge(v, u, production = attr['consumption'], consumption = attr['production'], tokens = capacity - tokens)

            except ValueError:
                del self.get_edge_data(u, v)['capacity']

                # create reverse channel (w, v)
                self.add_edge(v, u, production = attr['consumption'], consumption = attr['production'], var = attr['capacity'])

    def prune_parallel_edges( self ):
        multi = dict()
        for v, w, key, data in self.edges( keys = True, data = True ):
            prates = data.get('production')
            crates = data.get('consumption')
            tokens = data.get('tokens')
            if len( prates ) == len( crates ) == 1:
                tokens = tokens // data.get('gcd')
                if (v, w) in multi:
                    multi[ (v, w) ].append( (tokens, key ))
                else:
                    multi[ (v, w) ] = [(tokens, key)]

        removed = 0
        for v, w in multi:
            lst = iter(sorted( multi[ (v, w) ]))

            # skip first entry, this is the edge we retain
            next( lst )
            for _, key in lst:
                self.remove_edge( v, w, key )
                removed += 1
            
        return removed
            
    def __check_consistency(self):
        node_lcm_rates = {}

        for v, w, data in self.edges( data = True ):
            prates = data.get('production')
            crates = data.get('consumption')

            if prates.sum() <= 0 or len(prates) == 0:
                raise Exception("({}, {}) has an invalid production rate vector (sum = {})".format(v, w, prates.sum()))

            if crates.sum() <= 0 or len(crates) == 0:
                raise Exception("({}, {}) has an invalid consumption rate vector (sum = {})".format(v, w, crates.sum()))

            avg_prate = Fraction(prates.sum(), len(prates))
            avg_crate = Fraction(crates.sum(), len(crates))

            node_lcm_rates[v] = lcm(lcm(node_lcm_rates.get(v, 1), prates.sum()), avg_prate.denominator)
            if node_lcm_rates[v] == 0:
                raise Exception("LCM of rates associated with actor {} is zero", v)

            node_lcm_rates[w] = lcm(lcm(node_lcm_rates.get(w, 1), crates.sum()), avg_crate.denominator)
            if node_lcm_rates[w] == 0:
                raise Exception("LCM of rates associated with actor {} is zero", w)

        fractional_q = {}
        undirected = self.to_undirected()
        for v, w, key in dfs_edges( undirected ):
            # if self does not cantain (v, w), it must contains (w, v)
            if not self.has_edge( v, w, key ):
                v, w = w, v
            
            # get rates of channel (v, w)
            data = self.get_edge_data( v, w, key )
            p_vw, c_vw = data.get('production'), data.get('consumption')
            v_period = self.node[ v ]['period']
            w_period = self.node[ w ]['period']

            # if there is an edge (w, v) in sdfg, check whether it's consistent with (v, w)
            if v != w and self.has_edge(w, v):
                data_reverse = self.get_edge_data(w, v, 0)
                p_wv, c_wv = data_reverse.get('production'), data_reverse.get('consumption')
                if p_vw.sum( 0, v_period ) * p_wv.sum( 0, w_period ) != c_vw.sum( 0, w_period ) * c_wv.sum( 0, v_period ):
                    raise Exception("Inconsistent cycle: [{},{},{}]".format( v, w, v ))

            # check consistency of (v, w) with rest of the self
            if (v in fractional_q) and (w in fractional_q):
                if p_vw.sum( 0, v_period ) * fractional_q[v] != c_vw.sum( 0, w_period ) * fractional_q[w]:
                    raise Exception("Inconsistent edge: ({},{})".format( v, w ))

            elif (v in fractional_q):
                fractional_q[w] = fractional_q[v] * Fraction(p_vw.sum( 0, v_period ), c_vw.sum( 0, w_period ))

            elif (w in fractional_q):
                fractional_q[v] = fractional_q[w] * Fraction(c_vw.sum( 0, w_period ), p_vw.sum( 0, v_period ))

            else:
                fractional_q[v] = 1
                fractional_q[w] = Fraction(p_vw.sum( 0, v_period ), c_vw.sum( 0, w_period ))
            
        # compute the LCM of the denominators in the fractional repetition vector
        m = 1
        for f in fractional_q.values():
            m = lcm(m, Fraction(f).denominator)

        # multiply all fractions with the LCM of their denominators to obtain the repetition vector
        q = {}
        tpi = 1
        for k in fractional_q:
            f = fractional_q[k] 
            q[k] = int(f * m * self.phases(k))
            assert (node_lcm_rates[k] * f * m).denominator == 1
            tpi = lcm( tpi, (node_lcm_rates[k] * f * m).numerator )

        s = {}
        for v, w, data in self.edges(data = True):
            prate, crate = data.get('production'), data.get('consumption')
            s[ (v, w) ] = (tpi * len(prate)) // (q[v] * prate.sum())

        return q, s, tpi

    def __validate_vector(vector_name, vector, description = "property"):
        if type(vector) is str:
            m = re.match(r'\[([^]]*)\]', vector);
            if not m:
                raise SDFParseError("String expression for {} of {} must be comma-separated list enclosed in square brackets".format(description, vector_name))

            lst = []
            for substr in m.group(1).split(','):
                substr = substr.strip()
                m = re.match(r'(\d+)(?:\s*\*\s*(\d+)|$)', substr)
                if not m:
                    raise SDFParseError("Items in {} list of {} must be of form '<int>' or '<int> * <int>'".format(description, vector_name))

                if m.group(2):
                    lst = lst + ([int(m.group(2))] * int(m.group(1)))
                else:
                    lst.append(int(m.group(1)))

            if not lst:
                raise SDFParseError("Empty {} list for {}".format(description, channel))

            vector = cyclic(lst)
        else:
            try:
                it = iter(vector[:])
                lst = []
                for number in it:
                    try:
                        number = int(number)
                        lst.append(number)
                    except ValueError:
                        raise SDFParseError("{} has an invalid {} entry: {}".format( vector_name, description, number) )

                if not vector:
                    raise SDFParseError("Empty {} list for {}".format(description, vector_name))

                vector = cyclic(lst)
            except TypeError:
                try:
                    vector = cyclic(int(vector))
                except ValueError:
                    raise SDFParseError("{} has an invalid {}: {}".format( vector_name, description, vector) )

        return vector


class cyclic( tuple ):
    def __new__(self, *arg):
        try:
            return super().__new__(self, tuple(*arg))
        except TypeError as e:
            return super().__new__(self, tuple(arg))

    def __init__(self, *arg):
        self.__sum = sum(self)
    
    def __getitem__(self, idx):
        if type(idx) is slice:
            start = idx.start or 0
            start_mod = start % len(self)

            step = idx.step or 1
            period = len(self) // gcd( step, len(self) )

            pattern = []
            for i in range(period):
                if (idx.stop or 1) > 0:
                    pattern.append(super().__getitem__((start + i * step) % len(self)))
                else:
                    pattern.append(super().__getitem__((start - i * step) % len(self)))
            
            if idx.stop is not None:
                # return tuple
                if idx.stop >= 0:
                    result_len = max(0, 1 + (idx.stop - start - 1) // step)
                    num_periods = result_len // period
                    mod_periods = result_len % period
                    return tuple( pattern * num_periods + pattern[:mod_periods] )
                else:
                    result_len = max(0, 1 + (start - idx.stop - 1) // step)
                    num_periods = result_len // period
                    mod_periods = result_len % period
                    return tuple( pattern * num_periods + pattern[:mod_periods] )
            else:
                # return cyclic pattern
                return cyclic( pattern )
        else:
            return super().__getitem__(idx % len(self))

    def sum(self, start = 0, stop = None, step = 1):
        start_mod = start % len(self)
        period = len(self) // gcd( step, len(self) )

        pattern = self
        psum = self.__sum
        if start_mod > 0 or step != 1:
            pattern = []
            psum = 0
            for i in range(period):
                elem = super().__getitem__((start + i * step) % len(self))
                psum += elem
                pattern.append(elem)
        
        if stop is None:
            stop = len(self)

        # return tuple
        result_len = max(0, 1 + (stop - start - 1) // step)
        num_periods = result_len // period
        mod_periods = result_len % period
        return num_periods * psum + sum(pattern[:mod_periods])
    
class SDFParseError(Exception):
    pass

def predecessor(k = None, **kwargs):
    """ Computes the last producing firing that enables a consuming firing,
    for a CSDF channel with the specified production and consumption rates,
    and tokens.
    
    k       the number of consuming firings.
            if k is not specified, the function returns a function that takes a parameter k
            and computes predecessor(k)
    """
    prates = kwargs['production']
    crates = kwargs['consumption']
    tokens = kwargs['tokens']

    plen = len(prates)
    clen = len(crates)
    csum = crates.sum()
    psum = prates.sum()

    if k is None:
        if plen > 1:
            return lambda k: max(
                [ ((((k // clen) * csum + crates.sum(0, k % clen) - 1 - tokens - prates.sum(0, i)) // psum) * plen + i + 1)
                for i in range(0, plen) ])
        elif clen > 1:
            return lambda k: (((k // clen) * csum + crates.sum(0, k % clen) - 1 - tokens) // psum) + 1
        else:
            return lambda k: ((k * csum - 1 - tokens) // psum) + 1
    else:
        maxval = None
        numerator = (k // clen) * csum + crates.sum(0, k % clen) - tokens - 1
        for i in range(0, plen):
            val_i = (numerator // psum) * plen + i + 1
            if not maxval or val_i > maxval:
                maxval = val_i
            numerator -= prates[i]

        return maxval

def chain(*predfuns):
    return reduce(lambda f, g: lambda x: g(f(x)), reversed(predfuns))

def load_sdf_xml(filename):
    tree = etree.parse(filename)
    root = tree.getroot()
    if root.tag != 'sdf3':
        raise SDFParseError("Missing sdf3 root element")
    if not 'type' in root.keys():
        raise SDFParseError("Missing attribute 'type'")
    graph_type = root.get('type')
    if graph_type not in ['sdf', 'csdf']:
        raise SDFParseError("Don't know how to deal with graph type {}".format(graph_type))
    if not 'version' in root.keys():
        raise SDFParseError("Missing attribute 'version'")
    if root.get('version') != '1.0':
        raise SDFParseError("Don't know how to deal with version {}".format(root.get('version')))
    app_graph = root.find('applicationGraph')
    if app_graph is None:
        raise SDFParseError("Missing 'applicationGraph' element")
    sdf_graph = app_graph.find(graph_type)
    sdf_graph_properties = app_graph.find('{}Properties'.format(graph_type))
    if sdf_graph is None:
        raise SDFParseError("Missing '{}' element".format(graph_type))
    if sdf_graph_properties is None:
        raise SDFParseError("Missing '{}Properties' element".format(graph_type))

    # Create empty directed graph
    sdfg = nx.MultiDiGraph()

    # go over all actors and look up each actor's properties
    for actor_element in sdf_graph.findall("actor"):
        name = actor_element.get('name')
        times = sdf_graph_properties.find("actorProperties[@actor='{}']/processor[@default='true']/executionTime[@time]".format(name))
        if times is None:
            print("Warning: no execution time found for actor {}, assuming 1".format(name))
            times = '1'

        wcet = list()
        assert times is not None
        for t in times.get('time').split(','):
            try:
                wcet.append(int(t))
            except ValueError:
                raise SDFParseError("Invalid execution time for actor {}".format(name))
        sdfg.add_node( name, wcet = wcet )

    # go over channels
    for channel_element in sdf_graph.findall("channel"):
        src = channel_element.get('srcActor'), channel_element.get('srcPort')
        assert src[0] is not None, "channel has no srcActor"
        assert src[1] is not None, "channel has no srcPort"
        src_port = sdf_graph.find("actor[@name='{}']/port[@name='{}']".format( *src ))
        if src_port is None:
            raise SDFParseError("Unknown actor/port: {}/{}".format( *src))
        assert 'type' in src_port.attrib and src_port.attrib['type'] == 'out'
        production = list()
        for rate in src_port.get('rate', '1').split(','):
            try:
                production.append(int(rate))
            except ValueError:
                raise SDFParseError("Invalid rate for actor/port {}/{}".format(*src))

        dst = channel_element.get('dstActor'), channel_element.get('dstPort')
        dst_port = sdf_graph.find("actor[@name='{}']/port[@name='{}']".format( *dst ))
        if dst_port is None:
            raise SDFParseError("Unknown actor/port: {}/{}".format(*dst))
        assert 'type' in dst_port.attrib and dst_port.attrib['type'] == 'in'
        consumption = list()
        for rate in dst_port.get('rate', '1').split(','):
            try:
                consumption.append(int(rate))
            except ValueError:
                raise SDFParseError("Invalid rate for actor/port {}/{}".format(*dst))

        try:
            tokens = int(channel_element.get('initialTokens', 0))
        except ValueError:
            raise SDFParseError("Invalid initialTokens attribute for channel {}".format(channel_element.get('name')))

        sdfg.add_edge( src[0], dst[0], production = cyclic(production), consumption = cyclic(consumption), tokens = tokens )

    return SDFGraph( sdfg )

def write_sdf_json( g, filename ):
    with open(filename, 'w') as outfile:
        outfile.write( g.to_JSON())

def write_sdf_xml( g, filename ):
    root = etree.Element('sdf3', type = 'sdf', version = '1.0')
    ag = etree.SubElement(root, 'applicationGraph')
    sdf = etree.SubElement(ag, 'sdf', name = 'g', type = 'G')
    sdfprops = etree.SubElement(ag, 'sdfProperties')
    ports = dict()
    actors = dict()
    for v, data in g.nodes( data = True ):
        wcet = ','.join(map(str, data['wcet']))
        ports[ v ] = 0
        actors[ v ] = etree.SubElement(sdf, 'actor', name = '{}'.format(v), type = 'A')
        actorprops = etree.SubElement(sdfprops, 'actorProperties', actor = '{}'.format(v))
        processor = etree.SubElement(actorprops, 'processor', type = 'p1', default = 'true')
        etree.SubElement( processor, 'executionTime', time = '{}'.format( wcet ))

    cidx = 0
    for v, w, data in g.edges( data = True ):
        cidx += 1
        prates = ','.join(map( str, data.get('production', [1])))
        crates = ','.join(map( str, data.get('consumption', [1])))

        # add source port
        srcport = etree.SubElement( actors[v], 'port', name = 'p{}prod'.format( ports[v] ), type = 'out', rate = prates)
        dstport = etree.SubElement( actors[w], 'port', name = 'p{}cons'.format( ports[w] ), type = 'in', rate = crates)
        xmldata = dict(
            srcActor = '{}'.format(v), srcPort = 'p{}prod'.format( ports[ v ]),
            dstActor = '{}'.format(w), dstPort = 'p{}cons'.format( ports[ w ]))
        ports[ v ] += 1; ports[ w ] += 1

        if data['tokens'] != 0:
            xmldata['initialTokens'] = '{}'.format(data['tokens'])

        channel = etree.SubElement(sdf, 'channel', name = 'ch{}'.format(cidx), **xmldata)

    tree = etree.ElementTree( root )
    tree.write( filename,  )
    
def load_sdf_yaml(filename):
    with open(filename, 'r') as stream:
        try:
            contents = yaml.load( stream )
            if 'graph' not in contents:
                raise SDFParseError("Missing field: 'graph'")

            graph = contents.get('graph')
        except yaml.YAMLError as exc:
            raise SDFParseError("YAML error", exc)

        if 'actors' not in graph:
            raise SDFParseError("Missing field: 'actors'")

        if 'channels' not in graph:
            raise SDFParseError("Missing field: 'channels'")

        # Create empty directed graph
        sdfg = nx.MultiDiGraph()

        for actor in graph['actors']:
            if 'name' not in actor:
                raise Exception("Missing field in actor: 'name'")

            name = actor['name']

            if 'wcet' not in actor:
                print("Warning: assuming constant wcet of 1 for actor '{}'".format(name), file=sys.stderr)
                wcet = 1
            else:
                wcet = actor['wcet']
                
            sdfg.add_node(name, wcet = wcet)

        for channel in graph['channels']:
            if 'from' not in channel: raise Exception("Missing field in channel: 'from'")
            if 'to' not in channel: raise Exception("Missing field in channel: 'to'")

            (v, w) = (channel['from'], channel['to'])
            if v not in sdfg: raise Exception("Unknown source actor '{}' specified in channel".format(v))
            if w not in sdfg: raise Exception("Unknown destination actor '{}' specified in channel".format(w))

            sdfg.add_edge(v, w, **channel)

        return SDFGraph( sdfg )

def load_sdf(filename):
    with open( filename, 'r' ) as stream:
        data = json.load( stream )

        if 'actors' not in data:
            raise SDFParseError("Missing field: 'actors'")

        if 'channels' not in data:
            raise SDFParseError("Missing field: 'channels'")

        # Create empty directed graph
        sdfg = nx.MultiDiGraph()

        for actor in data['actors']:
            if 'name' not in actor:
                raise Exception("Missing field in actor: 'name'")

            name = actor['name']

            if 'wcet' not in actor:
                print("Warning: assuming constant wcet of 1 for actor '{}'".format(name), file=sys.stderr)
                wcet = 1
            else:
                wcet = actor['wcet']
                
            sdfg.add_node(name, wcet = wcet)

        for channel in data['channels']:
            if 'from' not in channel: raise Exception("Missing field in channel: 'from'")
            if 'to' not in channel: raise Exception("Missing field in channel: 'to'")

            (v, w) = (channel['from'], channel['to'])
            if v not in sdfg: raise Exception("Unknown source actor '{}' specified in channel".format(v))
            if w not in sdfg: raise Exception("Unknown destination actor '{}' specified in channel".format(w))

            sdfg.add_edge(v, w, **channel)

            # remove unnecessary elements
            #del sdfg.get_edge_data(v, w)['from']
            #del sdfg.get_edge_data(v, w)['to']

        return SDFGraph( sdfg )



