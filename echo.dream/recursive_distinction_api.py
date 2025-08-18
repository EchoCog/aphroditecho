"""
Recursive Distinction API Routes

This module contains Flask API routes for the recursive distinction system,
including endpoints for managing recursive distinctions, HyperGNN networks,
and self-referential nodes.
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
import json

from app import app, distinction_manager, hypergnn_manager, node_manager
from database import db
from models import RecursiveDistinction, HyperGNN, SelfReferentialNode, NodeConnection

# Recursive Distinction API Routes

@app.route('/api/distinctions', methods=['GET'])
def get_distinctions():
    """
    Get all recursive distinctions, optionally filtered by user_id.
    """
    user_id = request.args.get('user_id', type=int)
    parent_id = request.args.get('parent_id', type=int)
    
    query = RecursiveDistinction.query
    
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    
    if parent_id is not None:
        query = query.filter_by(parent_id=parent_id)
    else:
        # If no parent_id is specified, return top-level distinctions
        query = query.filter_by(parent_id=None)
    
    distinctions = query.all()
    
    result = []
    for d in distinctions:
        result.append({
            'id': d.id,
            'name': d.name,
            'expression': d.expression,
            'description': d.description,
            'created_at': d.created_at.isoformat(),
            'updated_at': d.updated_at.isoformat(),
            'user_id': d.user_id,
            'parent_id': d.parent_id,
            'metrics': d.get_metrics(),
            'child_count': d.children.count()
        })
    
    return jsonify(result)

@app.route('/api/distinctions', methods=['POST'])
@login_required
def create_distinction():
    """
    Create a new recursive distinction.
    """
    data = request.json
    
    if not data or not data.get('name') or not data.get('expression'):
        return jsonify({'error': 'Name and expression are required'}), 400
    
    try:
        distinction = distinction_manager.create_distinction(
            name=data['name'],
            expression=data['expression'],
            description=data.get('description'),
            user_id=current_user.id if current_user.is_authenticated else None,
            parent_id=data.get('parent_id')
        )
        
        return jsonify({
            'id': distinction.id,
            'name': distinction.name,
            'expression': distinction.expression,
            'description': distinction.description,
            'created_at': distinction.created_at.isoformat(),
            'updated_at': distinction.updated_at.isoformat(),
            'user_id': distinction.user_id,
            'parent_id': distinction.parent_id,
            'metrics': distinction.get_metrics()
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/distinctions/<int:distinction_id>', methods=['GET'])
def get_distinction(distinction_id):
    """
    Get a specific recursive distinction by ID.
    """
    distinction = RecursiveDistinction.query.get_or_404(distinction_id)
    
    # Get child distinctions
    children = []
    for child in distinction.children:
        children.append({
            'id': child.id,
            'name': child.name,
            'expression': child.expression
        })
    
    return jsonify({
        'id': distinction.id,
        'name': distinction.name,
        'expression': distinction.expression,
        'description': distinction.description,
        'created_at': distinction.created_at.isoformat(),
        'updated_at': distinction.updated_at.isoformat(),
        'user_id': distinction.user_id,
        'parent_id': distinction.parent_id,
        'metrics': distinction.get_metrics(),
        'children': children
    })

@app.route('/api/distinctions/<int:distinction_id>', methods=['PUT'])
@login_required
def update_distinction(distinction_id):
    """
    Update a recursive distinction.
    """
    distinction = RecursiveDistinction.query.get_or_404(distinction_id)
    
    # Check if the user is authorized to update this distinction
    if distinction.user_id and distinction.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to update this distinction'}), 403
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        if 'name' in data:
            distinction.name = data['name']
        
        if 'description' in data:
            distinction.description = data['description']
        
        if 'expression' in data:
            # Create a temporary distinction to validate the expression
            temp = distinction_manager.parser.parse(data['expression'])
            
            # If we get here, the expression is valid
            distinction.expression = data['expression']
            
            # Recalculate metrics
            metrics = distinction_manager._calculate_metrics(temp)
            distinction.set_metrics(metrics)
        
        distinction.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': distinction.id,
            'name': distinction.name,
            'expression': distinction.expression,
            'description': distinction.description,
            'updated_at': distinction.updated_at.isoformat(),
            'metrics': distinction.get_metrics()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/distinctions/<int:distinction_id>', methods=['DELETE'])
@login_required
def delete_distinction(distinction_id):
    """
    Delete a recursive distinction.
    """
    distinction = RecursiveDistinction.query.get_or_404(distinction_id)
    
    # Check if the user is authorized to delete this distinction
    if distinction.user_id and distinction.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to delete this distinction'}), 403
    
    try:
        # Check if there are children
        if distinction.children.count() > 0:
            return jsonify({'error': 'Cannot delete a distinction with children'}), 400
        
        db.session.delete(distinction)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Distinction deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/distinctions/<int:distinction_id>/evaluate', methods=['GET'])
def evaluate_distinction(distinction_id):
    """
    Evaluate a recursive distinction.
    """
    try:
        result = distinction_manager.evaluate_distinction(distinction_id)
        
        # Convert result to a JSON-serializable format
        if result is None:
            json_result = None
        elif isinstance(result, (int, float, bool, str)):
            json_result = result
        elif isinstance(result, (list, dict)):
            json_result = result
        else:
            json_result = str(result)
        
        return jsonify({
            'distinction_id': distinction_id,
            'result': json_result
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# HyperGNN API Routes

@app.route('/api/hypergnn', methods=['GET'])
def get_hypergnn_list():
    """
    Get all HyperGNN networks, optionally filtered by user_id.
    """
    user_id = request.args.get('user_id', type=int)
    
    query = HyperGNN.query
    
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    
    networks = query.all()
    
    result = []
    for network in networks:
        result.append({
            'id': network.id,
            'name': network.name,
            'created_at': network.created_at.isoformat(),
            'updated_at': network.updated_at.isoformat(),
            'user_id': network.user_id,
            'epochs_trained': network.epochs_trained
        })
    
    return jsonify(result)

@app.route('/api/hypergnn', methods=['POST'])
@login_required
def create_hypergnn():
    """
    Create a new HyperGNN network.
    """
    data = request.json
    
    if not data or not data.get('name') or not data.get('structure'):
        return jsonify({'error': 'Name and structure are required'}), 400
    
    try:
        network = hypergnn_manager.create_hypergnn(
            name=data['name'],
            structure=data['structure'],
            weights=data.get('weights'),
            parameters=data.get('parameters'),
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        return jsonify({
            'id': network.id,
            'name': network.name,
            'created_at': network.created_at.isoformat(),
            'updated_at': network.updated_at.isoformat(),
            'user_id': network.user_id,
            'epochs_trained': network.epochs_trained
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hypergnn/<int:network_id>', methods=['GET'])
def get_hypergnn(network_id):
    """
    Get a specific HyperGNN network by ID.
    """
    network = HyperGNN.query.get_or_404(network_id)
    
    return jsonify({
        'id': network.id,
        'name': network.name,
        'structure': network.get_structure(),
        'weights': network.get_weights(),
        'parameters': network.get_parameters(),
        'created_at': network.created_at.isoformat(),
        'updated_at': network.updated_at.isoformat(),
        'user_id': network.user_id,
        'epochs_trained': network.epochs_trained,
        'loss_history': network.get_loss_history()
    })

@app.route('/api/hypergnn/<int:network_id>', methods=['PUT'])
@login_required
def update_hypergnn(network_id):
    """
    Update a HyperGNN network.
    """
    network = HyperGNN.query.get_or_404(network_id)
    
    # Check if the user is authorized to update this network
    if network.user_id and network.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to update this network'}), 403
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        if 'name' in data:
            network.name = data['name']
        
        if 'structure' in data:
            network.set_structure(data['structure'])
        
        if 'weights' in data:
            network.set_weights(data['weights'])
        
        if 'parameters' in data:
            network.set_parameters(data['parameters'])
        
        network.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update in-memory cache
        hypergnn_manager.load_hypergnn(network_id)
        
        return jsonify({
            'id': network.id,
            'name': network.name,
            'updated_at': network.updated_at.isoformat()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hypergnn/<int:network_id>', methods=['DELETE'])
@login_required
def delete_hypergnn(network_id):
    """
    Delete a HyperGNN network.
    """
    network = HyperGNN.query.get_or_404(network_id)
    
    # Check if the user is authorized to delete this network
    if network.user_id and network.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to delete this network'}), 403
    
    try:
        # Remove from in-memory cache
        if network_id in hypergnn_manager.active_networks:
            del hypergnn_manager.active_networks[network_id]
        
        db.session.delete(network)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'HyperGNN network deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hypergnn/<int:network_id>/train', methods=['POST'])
@login_required
def train_hypergnn(network_id):
    """
    Record training progress for a HyperGNN network.
    """
    network = HyperGNN.query.get_or_404(network_id)
    
    # Check if the user is authorized to train this network
    if network.user_id and network.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to train this network'}), 403
    
    data = request.json
    
    if not data or 'epochs' not in data or 'loss' not in data:
        return jsonify({'error': 'Epochs and loss are required'}), 400
    
    try:
        hypergnn_manager.record_training(
            network_id,
            epochs=data['epochs'],
            loss=data['loss']
        )
        
        # Sync to database
        hypergnn_manager.sync_to_db(network_id)
        
        # Get updated network
        network = HyperGNN.query.get(network_id)
        
        return jsonify({
            'id': network.id,
            'epochs_trained': network.epochs_trained,
            'loss_history': network.get_loss_history()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Self-referential Node API Routes

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """
    Get all self-referential nodes, optionally filtered by user_id or parent_id.
    """
    user_id = request.args.get('user_id', type=int)
    parent_id = request.args.get('parent_id', type=int)
    node_type = request.args.get('node_type')
    
    query = SelfReferentialNode.query
    
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    
    if parent_id is not None:
        query = query.filter_by(parent_id=parent_id)
    elif parent_id == 0:  # Explicit 0 means get root nodes
        query = query.filter_by(parent_id=None)
    
    if node_type:
        query = query.filter_by(node_type=node_type)
    
    nodes = query.all()
    
    result = []
    for node in nodes:
        result.append({
            'id': node.id,
            'name': node.name,
            'node_type': node.node_type,
            'expression': node.expression,
            'value': node.get_value(),
            'created_at': node.created_at.isoformat(),
            'updated_at': node.updated_at.isoformat(),
            'user_id': node.user_id,
            'parent_id': node.parent_id,
            'child_count': node.children.count()
        })
    
    return jsonify(result)

@app.route('/api/nodes', methods=['POST'])
@login_required
def create_node():
    """
    Create a new self-referential node.
    """
    data = request.json
    
    if not data or not data.get('name') or not data.get('node_type'):
        return jsonify({'error': 'Name and node_type are required'}), 400
    
    try:
        node = node_manager.create_node(
            name=data['name'],
            node_type=data['node_type'],
            expression=data.get('expression'),
            value=data.get('value'),
            parent_id=data.get('parent_id'),
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        return jsonify({
            'id': node.id,
            'name': node.name,
            'node_type': node.node_type,
            'expression': node.expression,
            'value': node.get_value(),
            'created_at': node.created_at.isoformat(),
            'updated_at': node.updated_at.isoformat(),
            'user_id': node.user_id,
            'parent_id': node.parent_id
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nodes/<int:node_id>', methods=['GET'])
def get_node(node_id):
    """
    Get a specific self-referential node by ID.
    """
    node = SelfReferentialNode.query.get_or_404(node_id)
    
    # Get child nodes
    children = []
    for child in node.children:
        children.append({
            'id': child.id,
            'name': child.name,
            'node_type': child.node_type
        })
    
    # Get connections
    connections = []
    for conn in node.connections:
        # Only include connections where this node is the source
        if conn.source_id == node_id:
            connections.append({
                'id': conn.id,
                'source_id': conn.source_id,
                'target_id': conn.target_id,
                'connection_type': conn.connection_type,
                'weight': conn.weight,
                'target_name': conn.target.name
            })
    
    return jsonify({
        'id': node.id,
        'name': node.name,
        'node_type': node.node_type,
        'expression': node.expression,
        'value': node.get_value(),
        'created_at': node.created_at.isoformat(),
        'updated_at': node.updated_at.isoformat(),
        'user_id': node.user_id,
        'parent_id': node.parent_id,
        'children': children,
        'connections': connections
    })

@app.route('/api/nodes/<int:node_id>', methods=['PUT'])
@login_required
def update_node(node_id):
    """
    Update a self-referential node.
    """
    node = SelfReferentialNode.query.get_or_404(node_id)
    
    # Check if the user is authorized to update this node
    if node.user_id and node.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to update this node'}), 403
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        if 'name' in data:
            node.name = data['name']
        
        if 'node_type' in data:
            node.node_type = data['node_type']
        
        if 'expression' in data:
            # Validate expression if provided
            if data['expression']:
                temp = node_manager.parser.parse(data['expression'])
                
            node.expression = data['expression']
        
        if 'value' in data:
            # Serialize value if needed
            if data['value'] is not None:
                if isinstance(data['value'], (dict, list, int, float, bool, str)):
                    node.value = json.dumps(data['value'])
                else:
                    node.value = str(data['value'])
            else:
                node.value = None
        
        node.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': node.id,
            'name': node.name,
            'node_type': node.node_type,
            'expression': node.expression,
            'value': node.get_value(),
            'updated_at': node.updated_at.isoformat()
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nodes/<int:node_id>', methods=['DELETE'])
@login_required
def delete_node(node_id):
    """
    Delete a self-referential node.
    """
    node = SelfReferentialNode.query.get_or_404(node_id)
    
    # Check if the user is authorized to delete this node
    if node.user_id and node.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to delete this node'}), 403
    
    try:
        # Check if there are children
        if node.children.count() > 0:
            return jsonify({'error': 'Cannot delete a node with children'}), 400
        
        # Delete connections involving this node
        NodeConnection.query.filter(
            (NodeConnection.source_id == node_id) | 
            (NodeConnection.target_id == node_id)
        ).delete()
        
        db.session.delete(node)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Node deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nodes/<int:node_id>/evaluate', methods=['POST'])
def evaluate_node(node_id):
    """
    Evaluate a self-referential node.
    """
    data = request.json or {}
    args = data.get('args', [])
    
    try:
        result = node_manager.evaluate_node(node_id, args)
        
        # Convert result to a JSON-serializable format
        if result is None:
            json_result = None
        elif isinstance(result, (int, float, bool, str)):
            json_result = result
        elif isinstance(result, (list, dict)):
            json_result = result
        else:
            json_result = str(result)
        
        return jsonify({
            'node_id': node_id,
            'result': json_result
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections', methods=['POST'])
@login_required
def create_connection():
    """
    Create a new connection between nodes.
    """
    data = request.json
    
    if not data or 'source_id' not in data or 'target_id' not in data:
        return jsonify({'error': 'Source and target node IDs are required'}), 400
    
    try:
        connection = node_manager.connect_nodes(
            source_id=data['source_id'],
            target_id=data['target_id'],
            connection_type=data.get('connection_type', 'default'),
            weight=data.get('weight', 1.0),
            metadata=data.get('metadata')
        )
        
        return jsonify({
            'id': connection.id,
            'source_id': connection.source_id,
            'target_id': connection.target_id,
            'connection_type': connection.connection_type,
            'weight': connection.weight,
            'data': connection.get_conn_data() if hasattr(connection, 'get_conn_data') else {}
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections/<int:connection_id>', methods=['DELETE'])
@login_required
def delete_connection(connection_id):
    """
    Delete a connection between nodes.
    """
    connection = NodeConnection.query.get_or_404(connection_id)
    
    # Check if the user is authorized to delete this connection
    # For simplicity, we allow deletion if user owns either the source or target node
    source = SelfReferentialNode.query.get(connection.source_id)
    target = SelfReferentialNode.query.get(connection.target_id)
    
    if (source.user_id and source.user_id != current_user.id and
        target.user_id and target.user_id != current_user.id):
        return jsonify({'error': 'Not authorized to delete this connection'}), 403
    
    try:
        db.session.delete(connection)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Connection deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recursive-system', methods=['POST'])
@login_required
def build_recursive_system():
    """
    Build a recursive system of nodes from a structure definition.
    """
    data = request.json
    
    if not data or not data.get('structure'):
        return jsonify({'error': 'Structure is required'}), 400
    
    try:
        root_id = node_manager.build_recursive_system(data['structure'])
        
        root = SelfReferentialNode.query.get(root_id)
        
        return jsonify({
            'success': True,
            'root_id': root_id,
            'root_name': root.name,
            'message': f'Recursive system built successfully with root node: {root.name}'
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500