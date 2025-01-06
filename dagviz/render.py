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
        .node.highlight rect, .node.highlight circle, .node.highlight ellipse {{
            stroke: #4CAF50;
            stroke-width: 3px;
        }}
        .edgePath.highlight path.path {{
            stroke: #4CAF50;
            stroke-width: 2.5px;
        }}
        .node.highlight-parent rect, .node.highlight-parent circle, .node.highlight-parent ellipse {{
            stroke: #FFA000;  /* Amber 700 */
            stroke-width: 3px;
            fill: #FFE082;    /* Amber 200 */
        }}
        .node.highlight-self rect, .node.highlight-self circle, .node.highlight-self ellipse {{
            stroke: #1976D2;  /* Blue 700 */
            stroke-width: 3px;
            fill: #90CAF9;    /* Blue 200 */
        }}
        .node.highlight-child rect, .node.highlight-child circle, .node.highlight-child ellipse {{
            stroke: #388E3C;  /* Green 700 */
            stroke-width: 3px;
            fill: #A5D6A7;    /* Green 200 */
        }}
        .edgePath.highlight-parent path.path {{
            stroke: #FFA000;  /* Amber 700 */
            stroke-width: 2.5px;
        }}
        .edgePath.highlight-child path.path {{
            stroke: #388E3C;  /* Green 700 */
            stroke-width: 2.5px;
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

            // Add click and hover state management
            let activeNode = null;

            // Function to clear all highlights
            function clearHighlights() {{
                inner.selectAll(".highlight-parent").classed("highlight-parent", false);
                inner.selectAll(".highlight-self").classed("highlight-self", false);
                inner.selectAll(".highlight-child").classed("highlight-child", false);
            }}

            // Function to highlight node and its connections
            function highlightNode(node, v) {{
                clearHighlights();
                
                // Highlight the current node
                node.classed("highlight-self", true);
                
                // Find and highlight parent nodes and edges
                g.inEdges(v).forEach(e => {{
                    const edgeId = `${{e.v}}-${{e.w}}`;
                    inner.select(`g.edgePath[data-edge-id="${{edgeId}}"]`).classed("highlight-parent", true);
                    inner.select(`g.node[data-node-id="${{e.v}}"]`).classed("highlight-parent", true);
                }});

                // Find and highlight child nodes and edges
                g.outEdges(v).forEach(e => {{
                    const edgeId = `${{e.v}}-${{e.w}}`;
                    inner.select(`g.edgePath[data-edge-id="${{edgeId}}"]`).classed("highlight-child", true);
                    inner.select(`g.node[data-node-id="${{e.w}}"]`).classed("highlight-child", true);
                }});
            }}

            // Add click handler to SVG for clearing highlights when clicking outside
            svg.on("click", function(event) {{
                if (event.target.tagName === "svg") {{
                    clearHighlights();
                    activeNode = null;
                }}
            }});

            // Add node interactions
            inner.selectAll("g.node")
                .on("click", function(evt, v) {{
                    evt.stopPropagation();  // Prevent SVG click from triggering
                    const node = d3.select(this);
                    
                    if (activeNode === v) {{
                        // If clicking the same node, clear highlights
                        clearHighlights();
                        activeNode = null;
                    }} else {{
                        // Highlight new node
                        highlightNode(node, v);
                        activeNode = v;
                    }}
                }})
                .on("mouseover", function(evt, v) {{
                    // Only show hover effects if no node is currently active
                    if (!activeNode) {{
                        highlightNode(d3.select(this), v);
                    }}
                }})
                .on("mouseout", function() {{
                    // Only clear highlights if no node is currently active
                    if (!activeNode) {{
                        clearHighlights();
                    }}
                }});

            // Add data attributes to nodes and edges for selection
            inner.selectAll("g.node")
                .attr("data-node-id", d => d);
            inner.selectAll("g.edgePath")
                .attr("data-edge-id", d => `${{d.v}}-${{d.w}}`);

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