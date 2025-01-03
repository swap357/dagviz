from typing import Optional, Dict, Any, List
import json
from .render import render, view as render_view

class Node:
    """Represents a node in the graph"""
    def __init__(self, name: str, label: Optional[str] = None, **attrs):
        self.name = name
        self.label = label or name
        # Convert newlines in labels to HTML line breaks
        if '\n' in self.label:
            self.label = self.label.replace('\n', '<br/>')
        # Handle shape attribute specially
        self.shape = attrs.pop('shape', 'rect')
        self.attrs = attrs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.name,
            "label": self.label,
            "shape": self.shape,
            **self.attrs
        }

class Edge:
    """Represents an edge in the graph"""
    def __init__(self, source: str, target: str, **attrs):
        self.source = source
        self.target = target
        self.attrs = attrs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            **self.attrs
        }

class Graph:
    """Base class for undirected graphs"""
    def __init__(self, name: Optional[str] = None, **attrs):
        self.name = name
        self.attrs = attrs
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

    def node(self, name: str, label: Optional[str] = None, **attrs):
        """Add a node to the graph"""
        self.nodes[name] = Node(name, label, **attrs)
        return self

    def edge(self, source: str, target: str, **attrs):
        """Add an edge to the graph"""
        self.edges.append(Edge(source, target, **attrs))
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary format"""
        return {
            "directed": isinstance(self, Digraph),
            "name": self.name,
            "attrs": self.attrs,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges]
        }

    def render(self, filename: Optional[str] = None, view: bool = True) -> Optional[str]:
        """Render the graph to a file"""
        return render(self, filename, view)

    def view(self):
        """Render the graph and open in browser"""
        render_view(self)

class Digraph(Graph):
    """Directed graph"""
    pass 