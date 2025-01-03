import onnx
from dagviz import Digraph

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
        'Gather': 'Gath',
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

def escape_name(name):
    """Escape special characters in names"""
    return name.replace(':', '<colon>').replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

def format_shape(shape):
    """Format shape list to be more readable"""
    if not shape or shape == "?":
        return "?"
    
    def format_dim(d, pos=None):
        """Format a single dimension value with position context"""
        if isinstance(d, str):
            # Replace common dimension names
            replacements = {
                'batch_size': 'B',
                'sequence_length': 'S',
                'hidden_size': 'H',
                'num_heads': 'N',
                'head_size': 'HS',
                'vocab_size': 'V',
                'num_layers': 'L',
                'total_sequence_length': 'T'
            }
            for full, short in replacements.items():
                if full in d:
                    return short
            return d
        else:
            # Format numbers for readability
            try:
                num = int(d)
                if num >= 1024:
                    val = f"{num//1024}K" if num % 1024 == 0 else f"{num//1000}k"
                else:
                    val = str(num)
                
                # Add meaning based on position and value
                if pos is not None:
                    if num == 8 and pos in [1, -3]:  # Often num_heads
                        return f"{val}N"  # N heads
                    elif num == 64 and pos in [-1, -2]:  # Often head_dim
                        return f"{val}D"  # head Dimension
                    elif num in [2048, 4096] and pos == -1:  # Often hidden_size
                        return f"{val}H"  # Hidden size
                return val
            except (ValueError, TypeError):
                return str(d)
    
    # Format each dimension with position context
    if isinstance(shape, (list, tuple)):
        dims = []
        for i, d in enumerate(shape):
            pos = i - len(shape) if i >= 2 else i  # Position from start or end
            dims.append(format_dim(d, pos))
        
        # Special case for common tensor shapes
        if len(dims) == 4 and "N" in dims[1]:  # Attention patterns
            return f"[{dims[0]}, {dims[1]}, {dims[2]}, {dims[3]}]"  # [B, 8N, S, 64D]
        elif len(dims) == 3 and any(x.endswith('H') for x in dims):  # Hidden states
            return f"[{dims[0]}, {dims[1]}, {dims[2]}]"  # [B, S, 2KH]
            
        return f"[{', '.join(dims)}]"
    return str(shape)

def convert_onnx_model_to_graph(model_path):
    # Load the ONNX model
    model = onnx.load(model_path)
    model = onnx.shape_inference.infer_shapes(model)

    # Create a new directed graph
    G = Digraph('ONNX Model Graph', 
                graph_attrs={'rankdir': 'TB', 'splines': 'ortho'})

    # Track shapes
    shape_info = {}

    # Get shapes from initializers
    for init in model.graph.initializer:
        shape_info[init.name] = [d for d in init.dims]

    # Get shapes from inputs
    for node in model.graph.input:
        dim = node.type.tensor_type.shape.dim
        shape_info[node.name] = [d.dim_param if d.dim_value == 0 else d.dim_value for d in dim]

    # Get shapes from outputs
    for node in model.graph.output:
        dim = node.type.tensor_type.shape.dim
        shape_info[node.name] = [d.dim_param if d.dim_value == 0 else d.dim_value for d in dim]

    # Get shapes from value_info
    for node in model.graph.value_info:
        dim = node.type.tensor_type.shape.dim
        shape_info[node.name] = [d.dim_param if d.dim_value == 0 else d.dim_value for d in dim]

    # Track nodes we've drawn
    drawn = set()

    def draw_io(name):
        """Add input/output node if not already added"""
        if name not in drawn:
            # Different styles for different types of nodes
            style = {
                'style': 'filled, rounded',
                'shape': 'box',
                'margin': '0.3',
                'width': '1.8',   # Slightly wider for better text fit
                'height': '0.6',
                'fixedsize': 'true',
                'fontsize': '10'
            }
   
            # Clean and escape the name
            clean_label = clean_name(name)
            escaped_name = escape_name(name)
            shape = format_shape(shape_info.get(name, "?"))

            # Add node with shape info
            G.node(escaped_name, 
                  f"{clean_label}\\n{shape}", 
                  attrs=style)
            drawn.add(name)

    def draw():
        """Draw the graph"""
        for op_id, op in enumerate(model.graph.node):
            # Add operator node
            node_name = op.name or f"op_{op_id}"
            op_type = op.op_type
            
            if op.domain:
                if op.domain.startswith('com.microsoft'):
                    op_type = f"ms::{op_type}"
                else:
                    op_type = f"{op.domain}::{op_type}"
            
            # Clean names and create node ID
            clean_type = clean_name(op_type)
            current_op = escape_name(node_name)
            label = f"{clean_type}\\n(#{op_id})"

            G.node(current_op, 
                  label,
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
            edge_style = {'penwidth': '0.5', 'arrowsize': '0.5'}
            for input_node in op.input:
                draw_io(input_node)
                G.edge(escape_name(input_node), current_op, attrs=edge_style)
            for output_node in op.output:
                draw_io(output_node)
                G.edge(current_op, escape_name(output_node), attrs=edge_style)

    # Draw the graph
    draw()
    return G

if __name__ == "__main__":
    import sys
    
    model_path = sys.argv[1] if len(sys.argv) > 1 else './Llama-3.2-1B-Instruct/onnx/model.onnx'
    print(f"Processing model: {model_path}")
    
    G = convert_onnx_model_to_graph(model_path)
    if G:
        print("Rendering graph...")
        G.render('onnx_model_graph.html')
        G.view() 