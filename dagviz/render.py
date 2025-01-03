import json
import os
import tempfile
import webbrowser
from pathlib import Path
from typing import Union, Optional

# HTML template with embedded dagre-d3
_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://dagrejs.github.io/project/dagre-d3/latest/dagre-d3.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
        }}
        #graph {{
            width: 100%;
            height: 95vh;
            border: 1px solid #ccc;
            overflow: hidden;
        }}
        .node {{
            white-space: nowrap;
        }}
        .node rect, .node circle, .node ellipse {{
            stroke: #333;
            stroke-width: 1.5px;
            fill: #fff;
        }}
        .cluster rect {{
            stroke: #333;
            fill: #fff;
            fill-opacity: 0.1;
            stroke-width: 1.5px;
        }}
        .edgePath path.path {{
            stroke: #333;
            stroke-width: 1.5px;
            fill: none;
        }}
        .edgePath marker {{
            fill: #333;
        }}
        .node text {{
            font: 12px sans-serif;
            pointer-events: none;
        }}
        .node.operator rect {{
            fill: #e1f5fe;
        }}
        .node.tensor rect {{
            fill: #f3e5f5;
        }}
    </style>
</head>
<body>
    <div id="debug"></div>
    <svg id="graph" width="100%" height="95vh"></svg>
    <script>
        // Debug info
        const debug = document.getElementById('debug');
        
        try {{
            // Graph data
            const graphData = {graph_data};
            debug.innerHTML += `<p>Loaded graph data: ${{graphData.nodes.length}} nodes, ${{graphData.edges.length}} edges</p>`;

            // Create a new directed graph
            const g = new dagreD3.graphlib.Graph({{
                directed: true,
                compound: true,
                multigraph: false
            }}).setGraph({{
                rankdir: 'TB',
                align: 'UL',
                nodesep: 30,
                ranksep: 50,
                marginx: 20,
                marginy: 20
            }});

            // Add nodes
            graphData.nodes.forEach(node => {{
                const isOperator = node.class === 'node-oval';
                g.setNode(node.id, {{
                    label: node.label,
                    class: isOperator ? 'operator' : 'tensor',
                    shape: isOperator ? 'rect' : 'rect',
                    rx: 5,
                    ry: 5,
                    width: 150,
                    height: 40,
                    style: isOperator ? 'fill: #e1f5fe' : 'fill: #f3e5f5'
                }});
            }});

            // Add edges
            graphData.edges.forEach(edge => {{
                g.setEdge(edge.source, edge.target, {{
                    curve: d3.curveBasis,
                    arrowheadClass: 'arrowhead'
                }});
            }});

            // Create the renderer
            const render = new dagreD3.render();

            // Set up the SVG
            const svg = d3.select("#graph");
            const inner = svg.append("g");

            // Set up zoom support
            const zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on("zoom", (e) => {{
                    inner.attr("transform", e.transform);
                }});
            svg.call(zoom);

            // Run the renderer
            render(inner, g);

            // Center the graph
            const graphBounds = g.graph();
            const svgBounds = svg.node().getBoundingClientRect();
            const scale = Math.min(
                svgBounds.width / graphBounds.width,
                svgBounds.height / graphBounds.height,
                1
            ) * 0.9;

            const xOffset = (svgBounds.width - graphBounds.width * scale) / 2;
            const yOffset = (svgBounds.height - graphBounds.height * scale) / 2;

            svg.call(zoom.transform, 
                d3.zoomIdentity
                    .translate(xOffset, yOffset)
                    .scale(scale)
            );

            debug.innerHTML += `<p>Graph rendered successfully</p>`;

        }} catch (error) {{
            debug.innerHTML += `<p>Error: ${{error.message}}</p>`;
            console.error('Error:', error);
        }}
    </script>
</body>
</html>
'''

def render(graph, filename: Optional[str] = None, view: bool = True) -> Optional[str]:
    """Render graph to HTML file"""
    if filename is None:
        filename = tempfile.mktemp(suffix='.html')
    
    # Convert graph to JSON for embedding
    graph_data = json.dumps(graph.to_dict())
    
    # Generate HTML
    html = _TEMPLATE.format(
        title=graph.name or "Graph Visualization",
        graph_data=graph_data
    )
    
    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    if view:
        webbrowser.open(f'file://{os.path.abspath(filename)}')
    
    return filename if not view else None

def view(graph):
    """Render graph and open in browser"""
    render(graph, view=True) 