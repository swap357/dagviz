# dagviz

## Basic Usage

```python
from dagviz import Digraph

# Create a new directed graph
G = Digraph(name="My Graph", 
            graph_attrs={'rankdir': 'TB'})

# Add nodes
G.node('A', 'Node A')
G.node('B', 'Node B')

# Add edge between nodes
G.edge('A', 'B')

# Render the graph
G.render('output.html')
```

more: [docs/digraph.md](docs/digraph.md)