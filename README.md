# sdfpy
SDFpy is a Python library for working with Synchronous Dataflow (SDF) graphs.
An SDF graph is a directed graph that represents a computation: the nodes represent *functions* that are applied to the values stored on incoming edges, producing new values that are put onto outgoing edges.

## Basic setup
```python
import sdfpy.core as core
```

## 
An SDF graph is a subclass of a NetworkX MultiDiGraph.

Each node has the following main attributes:
* `wcet`: a tuple that specifies the (worst-case) execution time of consecutive firings of that node
* `phases`: the hyperperiod of the node (referred to as the number of 'phases').

Each edge *(a, b)* has the following attributes:
* `tokens`: the number of tokens that reside on the edge.
* `production`: a tuple that specifies the number of tokens *produced onto* the edge by consecutive firings of *a*
* `consumption`: a tuple that specifies the number of tokens *consumed onto* the edge by consecutive firings of *b*

## Creating an SDF graph

There are multiple ways to instantiate an SDF graph:
* From a NetworkX DiGraph or MultiDiGraph
* From a JSON file
* From an XML file in the SDF3 XML format

### From a NetworkX DiGraph (or MultiDiGraph)
  ```python
  import networkx as nx
  import sdfpy.core as core
  
  g = nx.DiGraph()
  g.add_node( 'a', wcet = 1 )
  g.add_node( 'b', wcet = 2 )
  g.add_edge( 'a', 'b', production = 2, consumption = 3, tokens = 0 )
  g.add_edge( 'b', 'a', production = 3, consumption = 2, tokens = 4 )
  
  sdfg = core.SDFGraph(g)
  ```
  
### From a JSON file
Let's assume that the file 'tiny-example.json' contains the following JSON structure:
```json
{
    "actors": [{"name": "a", "wcet": 1},
               {"name": "b", "wcet": 2}],
    "channels": [
           {"from": "a",
            "to": "b",
            "production": 2,
            "consumption": 3},
           {"from": "b",
            "to": "a",
            "production": 3,
            "consumption": 2,
            "tokens": 4}]
}
```

The following code reads the file into an SDF graph object
  ```python
  import sdfpy.core as core
  
  sdfg = core.load_sdf('tiny-example.json')
  ```

### From an XML file in the SDF3 XML format
Given the file 'tiny-example.xml' has the following contents (see [this page](http://www.es.ele.tue.nl/sdf3/manuals/xml/sdf/) for a detailed description of the XML structure):
```xml
<sdf3 type="sdf" version="1.0">
<applicationGraph>
  <sdf name="g" type="G">
    <actor name="a" type="A">
      <port name="p0prod" rate="2" type="out" />
      <port name="p0cons" rate="2" type="in" />
    </actor>
    <actor name="b" type="A">
      <port name="p0cons" rate="3" type="in" />
      <port name="p0prod" rate="3" type="out" />
    <channel name="ch1" srcActor="a" srcPort="p0prod" dstActor="b" dstPort="p0cons" />
    <channel name="ch2" srcActor="b" srcPort="p0prod" dstActor="a" dstPort="p0cons" initialTokens="4" />
  </sdf>
  <sdfProperties>
    <actorProperties actor="a">
      <processor default="true" type="p1">
        <executionTime time="1" />
      </processor>
    </actorProperties>
    <actorProperties actor="b">
      <processor default="true" type="p1">
        <executionTime time="2" />
      </processor>
    </actorProperties>
  </sdfProperties>
</applicationGraph>
</sdf3>
```
The following code reads the file into an SDF graph object:
  ```python
  import sdfpy.core as core
  
  sdfg = core.load_sdf_xml('tiny-example.xml')
  ```
