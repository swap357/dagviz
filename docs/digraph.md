# Digraph Documentation

The `Digraph` class represents a directed graph in the dagviz library. It inherits from the base `Graph` class and provides functionality for creating and visualizing directed graphs.

## Basic Usage

```python
from dagviz import Digraph

# Create a new directed graph
G = Digraph(name="My Graph", 
            graph_attrs={'rankdir': 'TB'})

# Add nodes and edges
G.node('A', 'Node A')
G.edge('A', 'B')

# Render the graph
G.render('output.html')
```

## Constructor Parameters

### name: Optional[str]
The name of the graph. Used as the title in the visualization.
```python
G = Digraph(name="ONNX Model Graph")
```

### graph_attrs: Dict[str, Any]
Global attributes that control the graph's layout and appearance.

Common graph attributes:
- `rankdir`: Direction of graph layout
  - `'TB'` - Top to bottom (default)
  - `'LR'` - Left to right
  - `'BT'` - Bottom to top
  - `'RL'` - Right to left
- `splines`: Edge routing style
  - `'ortho'` - Orthogonal lines
  - `'curved'` - Curved lines
  - `'line'` - Straight lines
- `nodesep`: Minimum space between nodes (in pixels)
- `ranksep`: Minimum space between ranks (in pixels)
- `margin`: Graph margin (in pixels)

```python
G = Digraph(graph_attrs={
    'rankdir': 'TB',
    'splines': 'ortho',
    'nodesep': '0.5',
    'ranksep': '0.75'
})
```

## Node Methods

### node(name: str, label: Optional[str] = None, **attrs)
Add a node to the graph.

Parameters:
- `name`: Unique identifier for the node
- `label`: Display text (defaults to name if not provided)
- `**attrs`: Node attributes

Common node attributes:
- `shape`: Node shape ('box', 'circle', 'ellipse')
- `style`: Node style ('filled', 'rounded', 'dashed')
- `fillcolor`: Background color (HTML color code)
- `margin`: Node margin (in pixels)
- `width`: Node width (in inches)
- `height`: Node height (in inches)
- `fontsize`: Font size (in points)
- `fixedsize`: Whether to maintain fixed size ('true'/'false')

```python
G.node('A', 'Node A',
       attrs={
           'shape': 'box',
           'style': 'filled, rounded',
           'fillcolor': '#e8f5e9',
           'margin': '0.3',
           'width': '1.5',
           'height': '0.6',
           'fontsize': '10',
           'fixedsize': 'true'
       })
```

## Edge Methods

### edge(source: str, target: str, **attrs)
Add an edge between nodes.

Parameters:
- `source`: Name of source node
- `target`: Name of target node
- `**attrs`: Edge attributes

Common edge attributes:
- `penwidth`: Line width
- `arrowsize`: Size of arrow head
- `color`: Edge color
- `style`: Line style ('solid', 'dashed', 'dotted')
- `label`: Edge label

```python
G.edge('A', 'B',
       attrs={
           'penwidth': '0.5',
           'arrowsize': '0.5',
           'color': '#333333',
           'style': 'solid'
       })
```

## Rendering Methods

### render(filename: Optional[str] = None, view: bool = True) -> Optional[str]
Render the graph to an HTML file.

Parameters:
- `filename`: Output file path (generates temp file if None)
- `view`: Whether to open in browser after rendering

```python
# Render and view
G.render('graph.html', view=True)

# Render without viewing
G.render('graph.html', view=False)
```

### view()
Shorthand to render and view the graph.

```python
G.view()  # Renders to temp file and opens in browser
```

## Example: Complex Graph

```python
G = Digraph('Complex Graph',
            graph_attrs={
                'rankdir': 'TB',
                'splines': 'ortho',
                'nodesep': '0.5',
                'ranksep': '0.75'
            })

# Add nodes with different styles
G.node('input', 'Input',
       attrs={
           'shape': 'box',
           'style': 'filled, rounded',
           'fillcolor': '#e8f5e9',
           'margin': '0.3',
           'width': '1.5',
           'height': '0.6',
           'fixedsize': 'true'
       })

G.node('process', 'Process',
       attrs={
           'shape': 'box',
           'style': 'filled',
           'fillcolor': '#e1f5fe',
           'margin': '0.3',
           'width': '1.2',
           'height': '0.6',
           'fixedsize': 'true'
       })

# Add edges
G.edge('input', 'process',
       attrs={
           'penwidth': '0.5',
           'arrowsize': '0.5'
       })

# Render
G.render('complex_graph.html')
``` 