import onnx
from dagviz import Digraph
import sys

def truncate_name(name, max_length=40):
    """Truncate long names and add ellipsis"""
    if len(name) > max_length:
        return name[:max_length-3] + "..."
    return name

def clean_name(name, max_length=30):
    """Clean and shorten node names"""
    # Remove common prefixes
    prefixes_to_remove = ['/model/', 'model.', '/output_0', '/input_0', 'attn_mask_reformat/attn_mask_subgraph/']
    name = name.replace('\\n', '\n')  # Handle escaped newlines
    
    for prefix in prefixes_to_remove:
        if name.startswith(prefix):
            name = name[len(prefix):]
        # Also check after slashes
        name = name.replace('/' + prefix, '/')
    
    # Simplify common patterns
    replacements = {
        'layers.': 'L',
        'attention': 'attn',
        'layernorm': 'LN',
        'input_': 'in_',
        'output_': 'out_',
        'weight': 'w',
        'MatMul': 'MM',
        'ReduceSum': 'RSum',
        'Constant': 'Const',
        'Gather': 'Gather',
        'constant_nodes': 'const',
        'TensorProto': 'TP',
        'subgraph': 'sg',
        'reformat': 'fmt',
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Handle paths
    if '/' in name:
        parts = name.split('/')
        if len(parts) > 2:
            # Keep first and last meaningful parts
            filtered_parts = [p for p in parts if p and not p.isdigit()]
            if len(filtered_parts) > 2:
                name = f"{filtered_parts[0]}/../{filtered_parts[-1]}"
            else:
                name = '/'.join(filtered_parts)
    
    # Final truncation if still too long
    if len(name) > max_length:
        name = name[:max_length-3] + "..."
            
    return name

def format_shape(shape):
    """Format shape list to be more readable"""
    if not shape or shape == "?":
        return "?"
    
    # Convert shape to string representation
    if isinstance(shape, (list, tuple)):
        shape_str = ', '.join(str(d) for d in shape)
    else:
        shape_str = str(shape).replace('[', '').replace(']', '')
    
    # Replace common dimension names
    replacements = {
        'batch_size': 'B',
        'sequence_length': 'S',
        'hidden_size': 'H',
        'num_heads': 'N',
        'head_size': 'HS',
        'vocab_size': 'V',
        'num_layers': 'L',
    }
    
    for full, short in replacements.items():
        shape_str = shape_str.replace(full, short)
    
    # Format numbers for readability
    parts = []
    for part in shape_str.split(', '):
        try:
            num = int(part)
            if num > 1000:
                part = f"{num//1024}K" if num % 1024 == 0 else f"{num//1000}k"
        except ValueError:
            pass
        parts.append(part)
    
    return f"[{', '.join(parts)}]"

def convert_onnx_model_to_graph(model_path):
    try:
        # Load the ONNX model without validation
        model = onnx.load(model_path, load_external_data=False)
    except Exception as e:
        print(f"Error loading ONNX model: {e}")
        return None

    try:
        try:
            model = onnx.shape_inference.infer_shapes(model)
        except Exception as e:
            print(f"Warning: Shape inference failed: {e}")
            print("Continuing without complete shape information...")
    except Exception as e:
        print(f"Warning: Shape inference failed: {e}")
        print("Continuing without shape information...")

    # Create a new directed graph with custom settings
    dot = Digraph('ONNX Model Graph', 
                  graph_attrs={
                      'rankdir': 'TB',  # Top to bottom layout
                      'nodesep': '0.5',  # Minimum space between nodes
                      'ranksep': '0.75',  # Minimum space between ranks
                      'splines': 'ortho'  # Orthogonal lines for edges
                  },
                  node_attrs={
                      'fontname': 'Arial',
                      'fontsize': '10',
                      'height': '0.4',
                      'width': '0.4'
                  })

    # Track shapes
    shape_info = {}

    def get_shape_from_type_proto(type_proto):
        """Helper to extract shape from TypeProto"""
        try:
            if not type_proto.tensor_type.shape.dim:
                return None
            return [d.dim_value if d.dim_value > 0 else d.dim_param 
                    for d in type_proto.tensor_type.shape.dim]
        except Exception:
            return None

    # Get shapes from initializers
    for init in model.graph.initializer:
        try:
            shape_info[init.name] = [d for d in init.dims]
        except Exception:
            continue

    # Get shapes from inputs
    for input_proto in model.graph.input:
        try:
            if shape := get_shape_from_type_proto(input_proto.type):
                shape_info[input_proto.name] = shape
        except Exception:
            continue

    # Get shapes from outputs
    for output_proto in model.graph.output:
        try:
            if shape := get_shape_from_type_proto(output_proto.type):
                shape_info[output_proto.name] = shape
        except Exception:
            continue

    # Get shapes from value_info
    for value_info in model.graph.value_info:
        try:
            if shape := get_shape_from_type_proto(value_info.type):
                shape_info[value_info.name] = shape
        except Exception:
            continue

    # Track nodes we've drawn
    drawn = set()

    def add_io_node(name):
        """Add input/output node if not already added"""
        if name not in drawn:
            shape = shape_info.get(name, "?")
            node_attrs = {
                'style': 'filled, rounded',
                'shape': 'box',
                'margin': '0.3',  # Increased margin
                'fontsize': '10',
                'width': '1.5',   # Fixed width
                'height': '0.6',  # Fixed height
                'fixedsize': 'true'  # Enforce fixed size
            }
            
            # Different styles for different types of nodes
            if name in [i.name for i in model.graph.input]:
                node_attrs['fillcolor'] = '#e8f5e9'  # Green for inputs
                node_attrs['penwidth'] = '2'
                clean_label = clean_name(name)  # Clean input names too
            elif name in [o.name for o in model.graph.output]:
                node_attrs['fillcolor'] = '#ffebee'  # Red for outputs
                node_attrs['penwidth'] = '2'
                clean_label = clean_name(name)  # Clean output names too
            elif name in [i.name for i in model.graph.initializer]:
                node_attrs['fillcolor'] = '#fff3e0'  # Orange for initializers
                clean_label = clean_name(name)
            else:
                node_attrs['fillcolor'] = '#f3e5f5'  # Default purple for tensors
                clean_label = clean_name(name)
            
            # Format label with cleaned name and shape
            label = f"{clean_label}\\n{format_shape(shape)}"
                
            # Add tensor node with shape info
            dot.node(name, label, attrs=node_attrs)
            drawn.add(name)

    def process_graph(graph):
        """Process nodes in a graph, including subgraphs"""
        # Add operator nodes and edges
        for op_id, op in enumerate(graph.node):
            try:
                node_name = op.name or f"op_{op_id}"
                # Handle custom operators by including domain info
                op_type = op.op_type
                if op.domain:
                    if op.domain.startswith('com.microsoft'):
                        op_type = f"ms::{op_type}"
                    else:
                        op_type = f"{op.domain}::{op_type}"
                
                # Safely get attributes
                attrs = []
                for attr in op.attribute:
                    if attr.type in [onnx.AttributeProto.INT, onnx.AttributeProto.FLOAT, onnx.AttributeProto.STRING]:
                        try:
                            value = attr.s if attr.type == onnx.AttributeProto.STRING else \
                                   attr.i if attr.type == onnx.AttributeProto.INT else attr.f
                            # Shorten attribute values
                            if isinstance(value, float) and abs(value) < 1e-3:
                                value = f"{value:.1e}"
                            elif isinstance(value, int) and value > 1000:
                                value = f"{value//1000}k"
                            attrs.append(f"{attr.name}={value}")
                        except Exception:
                            continue
                
                # Format operator label
                attr_str = "\\n" + "\\n".join(attrs[:2]) if attrs else ""  # Show max 2 attributes
                label = f"{clean_name(op_type)}\\n(#{op_id}){attr_str}"
                
                # Add operator node with distinct style
                dot.node(node_name, 
                        label,
                        attrs={
                            'shape': 'box',
                            'style': 'filled',
                            'fillcolor': '#e1f5fe',
                            'margin': '0.3',
                            'fontsize': '10',
                            'width': '1.2',   # Fixed width
                            'height': '0.6',  # Fixed height
                            'fixedsize': 'true'  # Enforce fixed size
                        })

                # Add edges with custom style
                edge_attrs = {
                    'penwidth': '0.5',
                    'arrowsize': '0.5'
                }

                # Add edges from inputs
                for inode in op.input:
                    add_io_node(inode)
                    dot.edge(inode, node_name, attrs=edge_attrs)

                # Add edges to outputs  
                for onode in op.output:
                    add_io_node(onode)
                    dot.edge(node_name, onode, attrs=edge_attrs)

                # Process subgraphs if any
                for attr in op.attribute:
                    if attr.type == onnx.AttributeProto.GRAPH:
                        process_graph(attr.g)
            except Exception as e:
                print(f"Warning: Failed to process node {op_id}: {e}")
                continue

    # Process the main graph
    process_graph(model.graph)
    return dot

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        model_path = './Llama-3.2-1B-Instruct/onnx/model.onnx'
    
    print(f"Processing model: {model_path}")
    
    graph = convert_onnx_model_to_graph(model_path)
    if graph is None:
        sys.exit(1)
        
    print("Graph conversion complete")
    
    output_file = 'onnx_model_graph.html'
    print(f"Rendering to {output_file}")
    graph.render(output_file)
    print("Rendering complete")
    
    graph.view() 