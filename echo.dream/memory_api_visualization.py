"""
Memory System Visualization API for Deep Tree Echo

This module provides API routes for visualizing the memory system.
"""

from flask import jsonify, request, Response, send_file
from io import StringIO, BytesIO
import logging
import networkx as nx
import csv
import json
import datetime

from app import app
from models_memory import MemoryNode, MemoryAssociation
from models import SelfReferentialNode

logger = logging.getLogger(__name__)

# Memory Visualization API
@app.route('/api/memory/visualization', methods=['GET'])
def get_memory_visualization():
    """
    Get memory graph visualization data. 
    This includes memory nodes, associations, activation levels, etc.
    """
    # Get min activation level or use default
    min_activation = request.args.get('min_activation', default=0.0, type=float)
    
    # Get memory type filter or use all
    memory_type = request.args.get('memory_type', default=None)
    
    # Get limit of nodes to include
    limit = request.args.get('limit', default=100, type=int)
    
    # Create a networkx graph to build the visualization
    G = nx.DiGraph()
    
    # Get memory nodes
    query = MemoryNode.query.filter(MemoryNode.activation_level >= min_activation)
    
    if memory_type:
        query = query.filter_by(memory_type=memory_type)
    
    # Order by activation level in descending order
    from sqlalchemy import desc
    memory_nodes = query.order_by(desc(MemoryNode.activation_level)).limit(limit).all()
    
    # Add nodes to graph
    node_map = {}  # Map memory node IDs to graph node IDs
    nodes = []
    
    for node in memory_nodes:
        # Try to get base node info
        base_node = SelfReferentialNode.query.get(node.node_id)
        base_name = base_node.name if base_node else f"Node {node.id}"
        
        # Create a semantic color mapping based on memory type
        group_map = {
            'semantic': 1,
            'episodic': 2,
            'procedural': 3,
            'working': 4,
            'sensory': 5
        }
        
        group = group_map.get(node.memory_type.lower() if node.memory_type else '', 0)
        
        # Add to nodes list
        node_data = {
            'id': f"node_{node.id}",
            'label': base_name,
            'group': group,
            'activation': node.activation_level,
            'memory_type': node.memory_type,
            'consolidation': node.consolidation_stage,
            'valence': node.emotional_valence,
            'arousal': node.emotional_arousal,
            'salience': node.salience
        }
        
        nodes.append(node_data)
        node_map[node.id] = f"node_{node.id}"
    
    # Get associations between these nodes
    node_ids = [node.id for node in memory_nodes]
    
    associations = []
    if node_ids:
        associations = MemoryAssociation.query.filter(
            (MemoryAssociation.source_id.in_(node_ids)) & 
            (MemoryAssociation.target_id.in_(node_ids))
        ).all()
    
    # Add edges to graph
    links = []
    
    for assoc in associations:
        if assoc.source_id in node_map and assoc.target_id in node_map:
            # Get source and target node emotional data
            source_node = next((n for n in memory_nodes if n.id == assoc.source_id), None)
            target_node = next((n for n in memory_nodes if n.id == assoc.target_id), None)
            
            # Calculate emotional tone as average of source and target valence
            # Scale from -1..1 to 0..1 for visualization purposes
            avg_valence = 0.5
            if source_node and target_node:
                avg_valence = (source_node.emotional_valence + target_node.emotional_valence) / 2
                avg_valence = (avg_valence + 1) / 2  # Scale from -1..1 to 0..1
            
            # Calculate emotional intensity as average of source and target arousal
            avg_arousal = 0.5
            if source_node and target_node:
                avg_arousal = (source_node.emotional_arousal + target_node.emotional_arousal) / 2
            
            # Add metadata from association if available
            metadata = {}
            if assoc.association_metadata:
                try:
                    metadata = json.loads(assoc.association_metadata)
                except:
                    pass
            
            link_data = {
                'source': node_map[assoc.source_id],
                'target': node_map[assoc.target_id],
                'value': assoc.strength,
                'type': assoc.association_type,
                'emotional_tone': avg_valence,      # 0 to 1 (negative to positive)
                'emotional_intensity': avg_arousal, # 0 to 1 (calm to excited)
                'metadata': metadata
            }
            links.append(link_data)
            
            # If bidirectional, add reverse link
            if assoc.bidirectional:
                reverse_link = {
                    'source': node_map[assoc.target_id],
                    'target': node_map[assoc.source_id],
                    'value': assoc.strength,
                    'type': assoc.association_type,
                    'emotional_tone': avg_valence,      # 0 to 1 (negative to positive)
                    'emotional_intensity': avg_arousal, # 0 to 1 (calm to excited)
                    'metadata': metadata
                }
                links.append(reverse_link)
    
    # If no memory nodes yet, add current graph data from existing recursive engine
    if not memory_nodes:
        # Import the engine only if we need it, to avoid circular imports
        import sys
        if 'dte_simulation' in sys.modules:
            from dte_simulation import DTESimulation
            # Create a temporary simulation instance just to get the graph structure
            temp_simulation = DTESimulation()
            if hasattr(temp_simulation, 'G'):
                for node_id in temp_simulation.G.nodes():
                    node_data = {
                        'id': str(node_id),
                        'label': str(node_id),
                        'group': 0,
                        'activation': 0.3,
                        'memory_type': 'simulation',
                        'consolidation': 0,
                        'valence': 0.0,
                        'arousal': 0.0,
                        'salience': 0.5
                    }
                    nodes.append(node_data)
                
                for source, target in temp_simulation.G.edges():
                    # Generate some simulated emotional data based on the node IDs
                    # This creates varying emotional tones for simulation data
                    try:
                        # Try converting to integers for numeric node IDs
                        source_val = int(hash(str(source)) % 100)
                        target_val = int(hash(str(target)) % 100) 
                        sim_tone = ((source_val + target_val) % 10) / 10.0
                        sim_intensity = ((source_val * target_val) % 10) / 10.0 + 0.3
                    except (ValueError, TypeError):
                        # For non-numeric node IDs, use hash of string
                        source_hash = hash(str(source)) % 100
                        target_hash = hash(str(target)) % 100
                        sim_tone = ((source_hash + target_hash) % 10) / 10.0
                        sim_intensity = ((source_hash * target_hash) % 100) / 100.0 + 0.3
                    
                    link_data = {
                        'source': str(source),
                        'target': str(target),
                        'value': 1.0,
                        'type': 'simulation',
                        'emotional_tone': sim_tone,
                        'emotional_intensity': sim_intensity
                    }
                    links.append(link_data)
    
    # Build the final visualization data
    result = {
        'nodes': nodes,
        'links': links,
        'metrics': {
            'node_count': len(nodes),
            'edge_count': len(links),
            'memory_types': {}
        }
    }
    
    # Count nodes by memory type
    memory_types = {}
    for node in nodes:
        memory_type = node.get('memory_type', 'unknown')
        if memory_type not in memory_types:
            memory_types[memory_type] = 0
        memory_types[memory_type] += 1
    
    result['metrics']['memory_types'] = memory_types
    
    # Check if we need to export the data in a specific format
    export_format = request.args.get('export', default=None)
    if export_format:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        # Handle different export formats
        if export_format.lower() == 'json':
            # Create a downloadable JSON file
            return Response(
                json.dumps(result, indent=2),
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment;filename=memory-graph-{timestamp}.json'}
            )
        
        elif export_format.lower() == 'csv':
            # Create CSV files for nodes and edges
            nodes_io = StringIO()
            links_io = StringIO()
            
            # Write nodes CSV
            nodes_writer = csv.writer(nodes_io)
            nodes_writer.writerow(['id', 'label', 'memory_type', 'group', 'activation', 'consolidation', 'valence', 'arousal', 'salience'])
            for node in nodes:
                nodes_writer.writerow([
                    node.get('id', ''),
                    node.get('label', ''),
                    node.get('memory_type', ''),
                    node.get('group', 0),
                    node.get('activation', 0),
                    node.get('consolidation', 0),
                    node.get('valence', 0),
                    node.get('arousal', 0),
                    node.get('salience', 0)
                ])
            
            # Create a zip file with both CSVs
            import zipfile
            memory_zip = BytesIO()
            with zipfile.ZipFile(memory_zip, 'w') as zf:
                zf.writestr(f'memory-nodes-{timestamp}.csv', nodes_io.getvalue())
                
                # Write links CSV
                links_writer = csv.writer(links_io)
                links_writer.writerow(['source', 'target', 'type', 'value', 'emotional_tone', 'emotional_intensity'])
                for link in links:
                    links_writer.writerow([
                        link.get('source', ''),
                        link.get('target', ''),
                        link.get('type', ''),
                        link.get('value', 1),
                        link.get('emotional_tone', 0.5),
                        link.get('emotional_intensity', 0.5)
                    ])
                
                zf.writestr(f'memory-links-{timestamp}.csv', links_io.getvalue())
            
            memory_zip.seek(0)
            return send_file(
                memory_zip,
                download_name=f'memory-graph-{timestamp}.zip',
                as_attachment=True,
                mimetype='application/zip'
            )
            
        elif export_format.lower() == 'graphml':
            # Create a NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes with attributes
            for node in nodes:
                G.add_node(
                    node['id'],
                    label=node.get('label', ''),
                    memory_type=node.get('memory_type', ''),
                    group=node.get('group', 0),
                    activation=node.get('activation', 0),
                    consolidation=node.get('consolidation', 0),
                    valence=node.get('valence', 0),
                    arousal=node.get('arousal', 0),
                    salience=node.get('salience', 0)
                )
            
            # Add edges with attributes
            for link in links:
                G.add_edge(
                    link['source'],
                    link['target'],
                    type=link.get('type', ''),
                    weight=link.get('value', 1),
                    emotional_tone=link.get('emotional_tone', 0.5),
                    emotional_intensity=link.get('emotional_intensity', 0.5)
                )
            
            # Write to GraphML format
            graphml_io = StringIO()
            nx.write_graphml(G, graphml_io)
            
            return Response(
                graphml_io.getvalue(),
                mimetype='application/xml',
                headers={'Content-Disposition': f'attachment;filename=memory-graph-{timestamp}.graphml'}
            )
    
    # Default: return JSON for the visualization
    return jsonify(result)

# Recursive Distinctions Visualization
@app.route('/api/recursive-distinctions/visualization', methods=['GET'])
def get_recursive_distinctions_visualization():
    """
    Get recursive distinctions graph visualization.
    """
    # Get all nodes and connections
    nodes = SelfReferentialNode.query.all()
    
    if not nodes:
        return jsonify({'nodes': [], 'links': [], 'metrics': {'node_count': 0, 'edge_count': 0}}), 200
    
    # Build visualization data
    node_data = []
    for node in nodes:
        node_data.append({
            'id': f"rd_{node.id}",
            'label': node.name,
            'group': {'operator': 0, 'value': 1, 'distinction': 2}.get(node.node_type, 3),
            'expression': node.expression,
            'node_type': node.node_type
        })
    
    links = []
    for node in nodes:
        for conn in node.connections:
            # Default emotional values for the connection
            emotional_tone = 0.5  # Neutral default
            emotional_intensity = 0.5  # Moderate intensity default
            
            # Adjust emotional tone based on connection type if available
            if conn.connection_type:
                if conn.connection_type.lower() in ['negation', 'contradiction', 'opposition']:
                    emotional_tone = 0.2  # More negative
                elif conn.connection_type.lower() in ['affirmation', 'inclusion', 'composition']:
                    emotional_tone = 0.8  # More positive
                
            # Add all link data
            links.append({
                'source': f"rd_{node.id}",
                'target': f"rd_{conn.target_id}",
                'value': 1.0,
                'type': conn.connection_type,
                'emotional_tone': emotional_tone,
                'emotional_intensity': emotional_intensity
            })
    
    # Build the final visualization data
    result = {
        'nodes': node_data,
        'links': links,
        'metrics': {
            'node_count': len(node_data),
            'edge_count': len(links)
        }
    }
    
    # Check if we need to export the data in a specific format
    export_format = request.args.get('export', default=None)
    if export_format:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        # Handle different export formats
        if export_format.lower() == 'json':
            # Create a downloadable JSON file
            return Response(
                json.dumps(result, indent=2),
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment;filename=recursive-distinctions-{timestamp}.json'}
            )
        
        elif export_format.lower() == 'csv':
            # Create CSV files for nodes and edges
            nodes_io = StringIO()
            links_io = StringIO()
            
            # Write nodes CSV
            nodes_writer = csv.writer(nodes_io)
            nodes_writer.writerow(['id', 'label', 'node_type', 'group', 'expression'])
            for node in node_data:
                nodes_writer.writerow([
                    node.get('id', ''),
                    node.get('label', ''),
                    node.get('node_type', ''),
                    node.get('group', 0),
                    node.get('expression', '')
                ])
            
            # Create a zip file with both CSVs
            import zipfile
            rd_zip = BytesIO()
            with zipfile.ZipFile(rd_zip, 'w') as zf:
                zf.writestr(f'rd-nodes-{timestamp}.csv', nodes_io.getvalue())
                
                # Write links CSV
                links_writer = csv.writer(links_io)
                links_writer.writerow(['source', 'target', 'type', 'value', 'emotional_tone', 'emotional_intensity'])
                for link in links:
                    links_writer.writerow([
                        link.get('source', ''),
                        link.get('target', ''),
                        link.get('type', ''),
                        link.get('value', 1),
                        link.get('emotional_tone', 0.5),
                        link.get('emotional_intensity', 0.5)
                    ])
                
                zf.writestr(f'rd-links-{timestamp}.csv', links_io.getvalue())
            
            rd_zip.seek(0)
            return send_file(
                rd_zip,
                download_name=f'recursive-distinctions-{timestamp}.zip',
                as_attachment=True,
                mimetype='application/zip'
            )
            
        elif export_format.lower() == 'graphml':
            # Create a NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes with attributes
            for node in node_data:
                G.add_node(
                    node['id'],
                    label=node.get('label', ''),
                    node_type=node.get('node_type', ''),
                    group=node.get('group', 0),
                    expression=node.get('expression', '')
                )
            
            # Add edges with attributes
            for link in links:
                G.add_edge(
                    link['source'],
                    link['target'],
                    type=link.get('type', ''),
                    weight=link.get('value', 1),
                    emotional_tone=link.get('emotional_tone', 0.5),
                    emotional_intensity=link.get('emotional_intensity', 0.5)
                )
            
            # Write to GraphML format
            graphml_io = StringIO()
            nx.write_graphml(G, graphml_io)
            
            return Response(
                graphml_io.getvalue(),
                mimetype='application/xml',
                headers={'Content-Disposition': f'attachment;filename=recursive-distinctions-{timestamp}.graphml'}
            )
    
    # Default: return JSON for the visualization
    return jsonify(result)