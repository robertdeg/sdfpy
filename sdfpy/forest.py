class Node( object ):
    def __init__(self):
        self.__next_sibling = self
        self.__prev_sibling = self
        self.__first_child = None
        self.__parent = None

        self.__in_edge = None

    @property
    def next_sibling(self):
        return self.__next_sibling

    @property
    def prev_sibling(self):
        return self.__prev_sibling

    @property
    def in_edge(self):
        return self.__in_edge

    @property
    def parent(self):
        return self.__parent

    @next_sibling.setter
    def next_sibling(self, value):
        self.__next_sibling = value

    @prev_sibling.setter
    def prev_sibling(self, value):
        self.__prev_sibling = value

    @in_edge.setter
    def in_edge(self, args):
        self.__parent = args[ 0 ]
        self.__in_edge = args[ 1 ]

    def removed_child( self, child ):
        if self.__first_child == child:
            next_sibling = child.next_sibling
            if next_sibling == child:
                self.__first_child = None
            else:
                self.__first_child = next_sibling

    def unlink( self ):
        self.__next_sibling.prev_sibling = self.__prev_sibling
        self.__prev_sibling.next_sibling = self.__next_sibling
        if self.__parent is not None:
            self.__parent.removed_child( self )
            self.__parent = None

        self.__prev_sibling = self.__next_sibling = self

    def append_child( self, child ):
        if self.__first_child is None:
            self.__first_child = child
        else:
            self.__first_child.prev_sibling.add_sibling( child )

    def add_sibling( self, sib ):
        sib.next_sibling = self.__next_sibling
        self.__next_sibling.prev_sibling = sib
        self.__next_sibling = sib
        sib.prev_sibling = self

    def children( self ):
        child = self.__first_child
        if child is not None:
            yield child
            child = child.next_sibling
            while child != self.__first_child:
                yield child
                child = child.next_sibling

    def pre_order( self ):
        yield self
        for child in self.children():
            yield from child.pre_order()

    def pre_order_edges( self ):
        for child in self.children():
            yield child.in_edge
            yield from child.pre_order_edges()

class Forest( object ):

    def __init__(self):
        super().__init__()
        self.__nodes = {}
        self.__roots = {}

    def roots( self ):
        yield from self.__roots

    def parent(self, child):
        return self.__nodes[child].in_edge

    def __contains__(self, item):
        return item in self.__nodes

    def add_edge(self, *edge):
        a, b, *_ = edge
        node_a = self.__nodes.get( a )
        if node_a is None:
            self.__nodes[ a ] = node_a = Node()
            self.__roots[ a ] = node_a

        node_b = self.__nodes.get( b )
        if node_b is None:
            self.__nodes[ b ] = node_b = Node()

        node_b.unlink()
        node_a.append_child( node_b )
        node_b.in_edge = node_a, edge

        # node b can't be a root
        self.__roots.pop( b, None )

    def pre_order( self, root = None ):
        if root is not None:
            # get the Node
            yield root
            n = self.__nodes[ root ]
            for _, b, *_ in n.pre_order_edges():
                yield b
        else:
            for root in self.__roots:
                yield root
                n = self.__roots[ root ]
                for _, b, *_ in n.pre_order_edges():
                    yield b

    def pre_order_edges( self, root = None ):
        if root is not None:
            n = self.__nodes[ root ]
            yield from n.pre_order_edges()
        else:
            for r in self.__roots:
                n = self.__roots[ r ]
                yield from n.pre_order_edges()



