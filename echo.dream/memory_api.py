"""
Memory System API for Deep Tree Echo

This module provides API routes for interacting with the memory system,
including temporal cycles, memory nodes, and pattern matching.
"""

from flask import jsonify, request
from flask_login import login_required, current_user
import logging
import json
from datetime import datetime

from app import app
from database import db
from models_memory import (
    MemoryCycle, MemoryNode, MemoryAssociation, PatternTemplate, DreamState
)
from models import SelfReferentialNode
from temporal_processor import temporal_processor
from pattern_matcher import pattern_matcher

logger = logging.getLogger(__name__)

#
# Temporal Cycles API
#

@app.route('/api/memory/cycles', methods=['GET'])
def get_memory_cycles():
    """Get all temporal cycles, optionally filtered by type or status."""
    cycle_type = request.args.get('type')
    enabled = request.args.get('enabled')
    
    query = MemoryCycle.query
    
    if cycle_type:
        query = query.filter_by(cycle_type=cycle_type)
    
    if enabled is not None:
        enabled_bool = enabled.lower() == 'true'
        query = query.filter_by(enabled=enabled_bool)
    
    cycles = query.all()
    
    result = []
    for cycle in cycles:
        result.append({
            'id': cycle.id,
            'name': cycle.name,
            'cycle_type': cycle.cycle_type,
            'duration_ms': cycle.duration_ms,
            'variance_percent': cycle.variance_percent,
            'last_execution': cycle.last_execution.isoformat() if cycle.last_execution else None,
            'next_scheduled': cycle.next_scheduled.isoformat() if cycle.next_scheduled else None,
            'enabled': cycle.enabled,
            'description': cycle.description,
            'execution_count': cycle.execution_count,
            'avg_execution_time_ms': cycle.avg_execution_time_ms
        })
    
    return jsonify(result)

@app.route('/api/memory/cycles', methods=['POST'])
@login_required
def create_memory_cycle():
    """Create a new temporal cycle."""
    data = request.json
    
    if not data or not data.get('name') or not data.get('cycle_type') or 'duration_ms' not in data:
        return jsonify({'error': 'Name, cycle_type, and duration_ms are required'}), 400
    
    try:
        cycle = MemoryCycle(
            name=data['name'],
            cycle_type=data['cycle_type'],
            duration_ms=data['duration_ms'],
            variance_percent=data.get('variance_percent', 10.0),
            priority=data.get('priority', 5),
            enabled=data.get('enabled', True),
            description=data.get('description'),
            function_code=data.get('function_code'),
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(cycle)
        db.session.commit()
        
        # Calculate next execution time
        cycle.calculate_next_execution()
        db.session.commit()
        
        return jsonify({
            'id': cycle.id,
            'name': cycle.name,
            'cycle_type': cycle.cycle_type,
            'duration_ms': cycle.duration_ms,
            'next_scheduled': cycle.next_scheduled.isoformat() if cycle.next_scheduled else None
        }), 201
    except Exception as e:
        logger.error(f"Error creating memory cycle: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/cycles/<int:cycle_id>', methods=['GET'])
def get_memory_cycle(cycle_id):
    """Get a specific temporal cycle by ID."""
    cycle = MemoryCycle.query.get_or_404(cycle_id)
    
    last_result = cycle.get_last_result() if cycle.last_result else None
    
    return jsonify({
        'id': cycle.id,
        'name': cycle.name,
        'cycle_type': cycle.cycle_type,
        'duration_ms': cycle.duration_ms,
        'variance_percent': cycle.variance_percent,
        'last_execution': cycle.last_execution.isoformat() if cycle.last_execution else None,
        'next_scheduled': cycle.next_scheduled.isoformat() if cycle.next_scheduled else None,
        'priority': cycle.priority,
        'enabled': cycle.enabled,
        'description': cycle.description,
        'function_code': cycle.function_code,
        'execution_count': cycle.execution_count,
        'avg_execution_time_ms': cycle.avg_execution_time_ms,
        'last_result': last_result,
        'created_at': cycle.created_at.isoformat(),
        'updated_at': cycle.updated_at.isoformat(),
        'user_id': cycle.user_id
    })

@app.route('/api/memory/cycles/<int:cycle_id>', methods=['PUT'])
@login_required
def update_memory_cycle(cycle_id):
    """Update a temporal cycle."""
    cycle = MemoryCycle.query.get_or_404(cycle_id)
    
    # Check if the user is authorized to update this cycle
    if cycle.user_id and cycle.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to update this cycle'}), 403
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        if 'name' in data:
            cycle.name = data['name']
        
        if 'cycle_type' in data:
            cycle.cycle_type = data['cycle_type']
        
        if 'duration_ms' in data:
            cycle.duration_ms = data['duration_ms']
        
        if 'variance_percent' in data:
            cycle.variance_percent = data['variance_percent']
        
        if 'priority' in data:
            cycle.priority = data['priority']
        
        if 'enabled' in data:
            cycle.enabled = data['enabled']
        
        if 'description' in data:
            cycle.description = data['description']
        
        if 'function_code' in data:
            cycle.function_code = data['function_code']
        
        cycle.updated_at = datetime.utcnow()
        
        # Recalculate next execution time if needed
        if 'duration_ms' in data or 'variance_percent' in data:
            cycle.calculate_next_execution()
        
        db.session.commit()
        
        return jsonify({
            'id': cycle.id,
            'name': cycle.name,
            'cycle_type': cycle.cycle_type,
            'duration_ms': cycle.duration_ms,
            'next_scheduled': cycle.next_scheduled.isoformat() if cycle.next_scheduled else None,
            'enabled': cycle.enabled,
            'updated_at': cycle.updated_at.isoformat()
        })
    except Exception as e:
        logger.error(f"Error updating memory cycle: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/cycles/<int:cycle_id>', methods=['DELETE'])
@login_required
def delete_memory_cycle(cycle_id):
    """Delete a temporal cycle."""
    cycle = MemoryCycle.query.get_or_404(cycle_id)
    
    # Check if the user is authorized to delete this cycle
    if cycle.user_id and cycle.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to delete this cycle'}), 403
    
    try:
        db.session.delete(cycle)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Cycle deleted'})
    except Exception as e:
        logger.error(f"Error deleting memory cycle: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/cycles/<int:cycle_id>/trigger', methods=['POST'])
@login_required
def trigger_memory_cycle(cycle_id):
    """Manually trigger a temporal cycle."""
    cycle = MemoryCycle.query.get_or_404(cycle_id)
    
    try:
        # Execute cycle
        result = None
        
        # Check if cycle has a handler in the temporal processor
        if cycle.name in temporal_processor.cycle_handlers:
            handler = temporal_processor.cycle_handlers[cycle.name]
            result = handler(cycle)
        else:
            # Use default handler
            result = temporal_processor._default_cycle_handler(cycle)
        
        # Update cycle
        cycle.last_execution = datetime.utcnow()
        cycle.execution_count += 1
        
        # Store result
        if result:
            cycle.set_last_result(result)
        
        # Calculate next execution time
        cycle.calculate_next_execution()
        
        # Update temporal processor's active cycles
        if cycle_id in temporal_processor.active_cycles:
            temporal_processor.active_cycles[cycle_id] = cycle.next_scheduled
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cycle_id': cycle.id,
            'name': cycle.name,
            'last_execution': cycle.last_execution.isoformat(),
            'next_scheduled': cycle.next_scheduled.isoformat() if cycle.next_scheduled else None,
            'result': result
        })
    except Exception as e:
        logger.error(f"Error triggering memory cycle: {e}")
        return jsonify({'error': str(e)}), 500

#
# Memory Nodes API
#

@app.route('/api/memory/nodes', methods=['GET'])
def get_memory_nodes():
    """Get all memory nodes, optionally filtered by type or activation."""
    memory_type = request.args.get('type')
    min_activation = request.args.get('min_activation', type=float)
    
    query = MemoryNode.query
    
    if memory_type:
        query = query.filter_by(memory_type=memory_type)
    
    if min_activation is not None:
        query = query.filter(MemoryNode.activation_level >= min_activation)
    
    nodes = query.all()
    
    result = []
    for node in nodes:
        result.append({
            'id': node.id,
            'node_id': node.node_id,
            'memory_type': node.memory_type,
            'activation_level': node.activation_level,
            'decay_rate': node.decay_rate,
            'consolidation_stage': node.consolidation_stage,
            'emotional_valence': node.emotional_valence,
            'emotional_arousal': node.emotional_arousal,
            'salience': node.salience,
            'timestamp': node.timestamp.isoformat(),
            'source': node.source,
            'context': node.get_context(),
            'last_activated': node.last_activated.isoformat() if node.last_activated else None,
            'activation_count': node.activation_count
        })
    
    return jsonify(result)

@app.route('/api/memory/nodes', methods=['POST'])
@login_required
def create_memory_node():
    """Create a new memory node linked to a self-referential node."""
    data = request.json
    
    if not data or not data.get('node_id') or not data.get('memory_type'):
        return jsonify({'error': 'node_id and memory_type are required'}), 400
    
    try:
        # Check if base node exists
        base_node = SelfReferentialNode.query.get(data['node_id'])
        if not base_node:
            return jsonify({'error': f"Base node with ID {data['node_id']} not found"}), 404
        
        # Create context if provided
        context = data.get('context')
        context_json = None
        if context:
            context_json = json.dumps(context)
        
        node = MemoryNode(
            node_id=data['node_id'],
            memory_type=data['memory_type'],
            activation_level=data.get('activation_level', 0.5),
            decay_rate=data.get('decay_rate', 0.05),
            consolidation_stage=data.get('consolidation_stage', 0),
            emotional_valence=data.get('emotional_valence', 0.0),
            emotional_arousal=data.get('emotional_arousal', 0.0),
            salience=data.get('salience', 0.5),
            context=context_json,
            source=data.get('source', 'user')
        )
        
        db.session.add(node)
        db.session.commit()
        
        return jsonify({
            'id': node.id,
            'node_id': node.node_id,
            'memory_type': node.memory_type,
            'activation_level': node.activation_level,
            'timestamp': node.timestamp.isoformat()
        }), 201
    except Exception as e:
        logger.error(f"Error creating memory node: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/nodes/<int:node_id>', methods=['GET'])
def get_memory_node(node_id):
    """Get a specific memory node by ID."""
    node = MemoryNode.query.get_or_404(node_id)
    
    # Get base node details
    base_node = SelfReferentialNode.query.get(node.node_id)
    base_node_details = {
        'id': base_node.id,
        'name': base_node.name,
        'node_type': base_node.node_type,
        'expression': base_node.expression
    } if base_node else None
    
    # Get associations
    associations = []
    for assoc in MemoryAssociation.query.filter(
        (MemoryAssociation.source_id == node_id) | 
        (MemoryAssociation.target_id == node_id)
    ).all():
        other_id = assoc.target_id if assoc.source_id == node_id else assoc.source_id
        other_node = MemoryNode.query.get(other_id)
        
        if other_node:
            associations.append({
                'id': assoc.id,
                'other_node_id': other_id,
                'other_node_type': other_node.memory_type,
                'association_type': assoc.association_type,
                'strength': assoc.strength,
                'bidirectional': assoc.bidirectional,
                'created_at': assoc.created_at.isoformat(),
                'metadata': assoc.get_metadata() if hasattr(assoc, 'get_metadata') else {}
            })
    
    return jsonify({
        'id': node.id,
        'node_id': node.node_id,
        'memory_type': node.memory_type,
        'activation_level': node.activation_level,
        'decay_rate': node.decay_rate,
        'consolidation_stage': node.consolidation_stage,
        'emotional_valence': node.emotional_valence,
        'emotional_arousal': node.emotional_arousal,
        'salience': node.salience,
        'timestamp': node.timestamp.isoformat(),
        'source': node.source,
        'context': node.get_context(),
        'created_at': node.created_at.isoformat(),
        'updated_at': node.updated_at.isoformat(),
        'last_activated': node.last_activated.isoformat() if node.last_activated else None,
        'activation_count': node.activation_count,
        'base_node': base_node_details,
        'associations': associations
    })

@app.route('/api/memory/nodes/<int:node_id>', methods=['PUT'])
@login_required
def update_memory_node(node_id):
    """Update a memory node."""
    node = MemoryNode.query.get_or_404(node_id)
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        if 'memory_type' in data:
            node.memory_type = data['memory_type']
        
        if 'activation_level' in data:
            node.activation_level = data['activation_level']
        
        if 'decay_rate' in data:
            node.decay_rate = data['decay_rate']
        
        if 'consolidation_stage' in data:
            node.consolidation_stage = data['consolidation_stage']
        
        if 'emotional_valence' in data:
            node.emotional_valence = data['emotional_valence']
        
        if 'emotional_arousal' in data:
            node.emotional_arousal = data['emotional_arousal']
        
        if 'salience' in data:
            node.salience = data['salience']
        
        if 'context' in data:
            node.set_context(data['context'])
        
        if 'source' in data:
            node.source = data['source']
        
        node.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': node.id,
            'memory_type': node.memory_type,
            'activation_level': node.activation_level,
            'updated_at': node.updated_at.isoformat()
        })
    except Exception as e:
        logger.error(f"Error updating memory node: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/nodes/<int:node_id>', methods=['DELETE'])
@login_required
def delete_memory_node(node_id):
    """Delete a memory node."""
    node = MemoryNode.query.get_or_404(node_id)
    
    try:
        # Delete all associations involving this node
        MemoryAssociation.query.filter(
            (MemoryAssociation.source_id == node_id) | 
            (MemoryAssociation.target_id == node_id)
        ).delete()
        
        db.session.delete(node)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Memory node deleted'})
    except Exception as e:
        logger.error(f"Error deleting memory node: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/nodes/<int:node_id>/activate', methods=['POST'])
def activate_memory_node(node_id):
    """Activate a memory node."""
    node = MemoryNode.query.get_or_404(node_id)
    
    data = request.json or {}
    amount = data.get('amount', 0.5)
    
    try:
        # Activate node
        new_activation = temporal_processor.activate_memory(node_id, amount)
        
        return jsonify({
            'success': True,
            'node_id': node_id,
            'previous_activation': node.activation_level,
            'new_activation': new_activation,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error activating memory node: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/associations', methods=['GET'])
def get_memory_associations():
    """Get memory associations, optionally filtered by type or strength."""
    assoc_type = request.args.get('type')
    min_strength = request.args.get('min_strength', type=float)
    
    query = MemoryAssociation.query
    
    if assoc_type:
        query = query.filter_by(association_type=assoc_type)
    
    if min_strength is not None:
        query = query.filter(MemoryAssociation.strength >= min_strength)
    
    associations = query.all()
    
    result = []
    for assoc in associations:
        result.append({
            'id': assoc.id,
            'source_id': assoc.source_id,
            'target_id': assoc.target_id,
            'association_type': assoc.association_type,
            'strength': assoc.strength,
            'bidirectional': assoc.bidirectional,
            'created_at': assoc.created_at.isoformat(),
            'updated_at': assoc.updated_at.isoformat(),
            'metadata': assoc.get_metadata() if hasattr(assoc, 'get_metadata') else {}
        })
    
    return jsonify(result)

@app.route('/api/memory/associations', methods=['POST'])
@login_required
def create_memory_association():
    """Create a new memory association between two nodes."""
    data = request.json
    
    if not data or not data.get('source_id') or not data.get('target_id'):
        return jsonify({'error': 'source_id and target_id are required'}), 400
    
    try:
        # Check if source and target nodes exist
        source = MemoryNode.query.get(data['source_id'])
        target = MemoryNode.query.get(data['target_id'])
        
        if not source:
            return jsonify({'error': f"Source node with ID {data['source_id']} not found"}), 404
        
        if not target:
            return jsonify({'error': f"Target node with ID {data['target_id']} not found"}), 404
        
        # Check if association already exists
        existing = MemoryAssociation.query.filter_by(
            source_id=data['source_id'],
            target_id=data['target_id']
        ).first()
        
        if existing:
            return jsonify({'error': 'Association already exists between these nodes'}), 400
        
        # Create metadata if provided
        metadata = data.get('metadata')
        metadata_json = None
        if metadata:
            metadata_json = json.dumps(metadata)
        
        assoc = MemoryAssociation(
            source_id=data['source_id'],
            target_id=data['target_id'],
            association_type=data.get('association_type', 'default'),
            strength=data.get('strength', 0.5),
            bidirectional=data.get('bidirectional', True),
            metadata=metadata_json
        )
        
        db.session.add(assoc)
        db.session.commit()
        
        return jsonify({
            'id': assoc.id,
            'source_id': assoc.source_id,
            'target_id': assoc.target_id,
            'association_type': assoc.association_type,
            'strength': assoc.strength,
            'bidirectional': assoc.bidirectional,
            'created_at': assoc.created_at.isoformat()
        }), 201
    except Exception as e:
        logger.error(f"Error creating memory association: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/associations/<int:assoc_id>', methods=['GET'])
def get_memory_association(assoc_id):
    """Get a specific memory association by ID."""
    assoc = MemoryAssociation.query.get_or_404(assoc_id)
    
    return jsonify({
        'id': assoc.id,
        'source_id': assoc.source_id,
        'target_id': assoc.target_id,
        'association_type': assoc.association_type,
        'strength': assoc.strength,
        'bidirectional': assoc.bidirectional,
        'created_at': assoc.created_at.isoformat(),
        'updated_at': assoc.updated_at.isoformat(),
        'metadata': assoc.get_metadata() if hasattr(assoc, 'get_metadata') else {}
    })

@app.route('/api/memory/associations/<int:assoc_id>', methods=['PUT'])
@login_required
def update_memory_association(assoc_id):
    """Update a memory association."""
    assoc = MemoryAssociation.query.get_or_404(assoc_id)
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        if 'association_type' in data:
            assoc.association_type = data['association_type']
        
        if 'strength' in data:
            assoc.strength = data['strength']
        
        if 'bidirectional' in data:
            assoc.bidirectional = data['bidirectional']
        
        if 'metadata' in data:
            assoc.set_metadata(data['metadata'])
        
        assoc.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': assoc.id,
            'association_type': assoc.association_type,
            'strength': assoc.strength,
            'updated_at': assoc.updated_at.isoformat()
        })
    except Exception as e:
        logger.error(f"Error updating memory association: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/associations/<int:assoc_id>', methods=['DELETE'])
@login_required
def delete_memory_association(assoc_id):
    """Delete a memory association."""
    assoc = MemoryAssociation.query.get_or_404(assoc_id)
    
    try:
        db.session.delete(assoc)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Memory association deleted'})
    except Exception as e:
        logger.error(f"Error deleting memory association: {e}")
        return jsonify({'error': str(e)}), 500

#
# Pattern Templates API
#

@app.route('/api/memory/patterns', methods=['GET'])
def get_pattern_templates():
    """Get all pattern templates, optionally filtered by type."""
    pattern_type = request.args.get('type')
    
    query = PatternTemplate.query
    
    if pattern_type:
        query = query.filter_by(pattern_type=pattern_type)
    
    patterns = query.all()
    
    result = []
    for pattern in patterns:
        result.append({
            'id': pattern.id,
            'name': pattern.name,
            'pattern_type': pattern.pattern_type,
            'structure': pattern.get_structure(),
            'rules': pattern.get_rules(),
            'activation_threshold': pattern.activation_threshold,
            'description': pattern.description,
            'created_at': pattern.created_at.isoformat(),
            'user_id': pattern.user_id
        })
    
    return jsonify(result)

@app.route('/api/memory/patterns', methods=['POST'])
@login_required
def create_pattern_template():
    """Create a new pattern template."""
    data = request.json
    
    if not data or not data.get('name') or not data.get('pattern_type'):
        return jsonify({'error': 'name and pattern_type are required'}), 400
    
    try:
        # Create pattern template
        pattern = PatternTemplate(
            name=data['name'],
            pattern_type=data['pattern_type'],
            activation_threshold=data.get('activation_threshold', 0.7),
            description=data.get('description'),
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        # Set structure and rules if provided
        if 'structure' in data:
            pattern.set_structure(data['structure'])
        
        if 'rules' in data:
            pattern.set_rules(data['rules'])
        
        db.session.add(pattern)
        db.session.commit()
        
        return jsonify({
            'id': pattern.id,
            'name': pattern.name,
            'pattern_type': pattern.pattern_type,
            'created_at': pattern.created_at.isoformat()
        }), 201
    except Exception as e:
        logger.error(f"Error creating pattern template: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/patterns/<int:pattern_id>', methods=['GET'])
def get_pattern_template(pattern_id):
    """Get a specific pattern template by ID."""
    pattern = PatternTemplate.query.get_or_404(pattern_id)
    
    # Get memory nodes associated with this pattern
    memory_nodes = []
    for node in pattern.memory_nodes:
        memory_nodes.append({
            'id': node.id,
            'memory_type': node.memory_type,
            'activation_level': node.activation_level
        })
    
    return jsonify({
        'id': pattern.id,
        'name': pattern.name,
        'pattern_type': pattern.pattern_type,
        'structure': pattern.get_structure(),
        'rules': pattern.get_rules(),
        'activation_threshold': pattern.activation_threshold,
        'description': pattern.description,
        'created_at': pattern.created_at.isoformat(),
        'updated_at': pattern.updated_at.isoformat(),
        'user_id': pattern.user_id,
        'memory_nodes': memory_nodes
    })

@app.route('/api/memory/patterns/<int:pattern_id>', methods=['PUT'])
@login_required
def update_pattern_template(pattern_id):
    """Update a pattern template."""
    pattern = PatternTemplate.query.get_or_404(pattern_id)
    
    # Check if the user is authorized to update this pattern
    if pattern.user_id and pattern.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to update this pattern template'}), 403
    
    data = request.json
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        if 'name' in data:
            pattern.name = data['name']
        
        if 'pattern_type' in data:
            pattern.pattern_type = data['pattern_type']
        
        if 'structure' in data:
            pattern.set_structure(data['structure'])
        
        if 'rules' in data:
            pattern.set_rules(data['rules'])
        
        if 'activation_threshold' in data:
            pattern.activation_threshold = data['activation_threshold']
        
        if 'description' in data:
            pattern.description = data['description']
        
        pattern.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': pattern.id,
            'name': pattern.name,
            'pattern_type': pattern.pattern_type,
            'updated_at': pattern.updated_at.isoformat()
        })
    except Exception as e:
        logger.error(f"Error updating pattern template: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/patterns/<int:pattern_id>', methods=['DELETE'])
@login_required
def delete_pattern_template(pattern_id):
    """Delete a pattern template."""
    pattern = PatternTemplate.query.get_or_404(pattern_id)
    
    # Check if the user is authorized to delete this pattern
    if pattern.user_id and pattern.user_id != current_user.id:
        return jsonify({'error': 'Not authorized to delete this pattern template'}), 403
    
    try:
        db.session.delete(pattern)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Pattern template deleted'})
    except Exception as e:
        logger.error(f"Error deleting pattern template: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/patterns/<int:pattern_id>/match', methods=['POST'])
def match_pattern_template(pattern_id):
    """Match a pattern template against memory nodes."""
    pattern = PatternTemplate.query.get_or_404(pattern_id)
    
    data = request.json
    
    if not data or not data.get('node_ids'):
        return jsonify({'error': 'node_ids are required'}), 400
    
    try:
        # Get memory nodes
        node_ids = data['node_ids']
        nodes = MemoryNode.query.filter(MemoryNode.id.in_(node_ids)).all()
        
        if not nodes:
            return jsonify({'error': 'No valid memory nodes provided'}), 400
        
        # Match pattern
        match_score = pattern_matcher.match_pattern(pattern_id, nodes)
        
        return jsonify({
            'pattern_id': pattern_id,
            'pattern_name': pattern.name,
            'pattern_type': pattern.pattern_type,
            'match_score': match_score,
            'threshold': pattern.activation_threshold,
            'matched': match_score >= pattern.activation_threshold,
            'node_count': len(nodes)
        })
    except Exception as e:
        logger.error(f"Error matching pattern template: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/nodes/<int:node_id>/similar', methods=['GET'])
def find_similar_memories(node_id):
    """Find memories similar to the given node."""
    node = MemoryNode.query.get_or_404(node_id)
    
    limit = request.args.get('limit', default=10, type=int)
    threshold = request.args.get('threshold', type=float)
    
    try:
        # Find similar memories
        similar = pattern_matcher.find_similar_memories(node_id, limit, threshold)
        
        result = []
        for sim_node, score in similar:
            result.append({
                'node_id': sim_node.id,
                'memory_type': sim_node.memory_type,
                'similarity_score': score,
                'activation_level': sim_node.activation_level,
                'emotional_valence': sim_node.emotional_valence,
                'emotional_arousal': sim_node.emotional_arousal
            })
        
        return jsonify({
            'base_node_id': node_id,
            'similar_nodes': result,
            'count': len(result)
        })
    except Exception as e:
        logger.error(f"Error finding similar memories: {e}")
        return jsonify({'error': str(e)}), 500

#
# Dream States API
#

@app.route('/api/memory/dreams', methods=['GET'])
def get_dream_states():
    """Get all dream states, optionally filtered by type."""
    dream_type = request.args.get('type')
    
    query = DreamState.query
    
    if dream_type:
        query = query.filter_by(dream_type=dream_type)
    
    # Order by start time descending (most recent first)
    query = query.order_by(DreamState.start_time.desc())
    
    dreams = query.all()
    
    result = []
    for dream in dreams:
        result.append({
            'id': dream.id,
            'title': dream.title,
            'start_time': dream.start_time.isoformat() if dream.start_time else None,
            'end_time': dream.end_time.isoformat() if dream.end_time else None,
            'duration_seconds': dream.duration_seconds,
            'dream_type': dream.dream_type,
            'emotional_tone': dream.emotional_tone,
            'coherence': dream.coherence,
            'insights_count': len(dream.get_insights()) if hasattr(dream, 'get_insights') else 0,
            'new_associations_count': len(dream.get_new_associations()) if hasattr(dream, 'get_new_associations') else 0
        })
    
    return jsonify(result)

@app.route('/api/memory/dreams/<int:dream_id>', methods=['GET'])
def get_dream_state(dream_id):
    """Get a specific dream state by ID."""
    dream = DreamState.query.get_or_404(dream_id)
    
    return jsonify({
        'id': dream.id,
        'title': dream.title,
        'start_time': dream.start_time.isoformat() if dream.start_time else None,
        'end_time': dream.end_time.isoformat() if dream.end_time else None,
        'duration_seconds': dream.duration_seconds,
        'content': dream.get_content() if hasattr(dream, 'get_content') else {},
        'source_memories': dream.get_source_memories() if hasattr(dream, 'get_source_memories') else [],
        'pattern_activations': dream.get_pattern_activations() if hasattr(dream, 'get_pattern_activations') else {},
        'insights': dream.get_insights() if hasattr(dream, 'get_insights') else [],
        'new_associations': dream.get_new_associations() if hasattr(dream, 'get_new_associations') else [],
        'dream_type': dream.dream_type,
        'emotional_tone': dream.emotional_tone,
        'coherence': dream.coherence,
        'user_id': dream.user_id
    })

@app.route('/api/memory/system/status', methods=['GET'])
def get_memory_system_status():
    """Get current status of the memory system."""
    return jsonify(temporal_processor.get_system_state())

@app.route('/api/memory/system/start', methods=['POST'])
@login_required
def start_memory_system():
    """Start the temporal processor if it's not already running."""
    if not temporal_processor.running:
        # Initialize default cycles
        temporal_processor.initialize_default_cycles()
        
        # Initialize basic patterns
        pattern_matcher.initialize_basic_patterns()
        
        # Start the temporal processor
        temporal_processor.start()
        
        return jsonify({
            'success': True,
            'message': 'Memory system started',
            'state': temporal_processor.get_system_state()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Memory system is already running',
            'state': temporal_processor.get_system_state()
        })

@app.route('/api/memory/system/stop', methods=['POST'])
@login_required
def stop_memory_system():
    """Stop the temporal processor if it's running."""
    if temporal_processor.running:
        temporal_processor.stop()
        
        return jsonify({
            'success': True,
            'message': 'Memory system stopped',
            'state': temporal_processor.get_system_state()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Memory system is not running',
            'state': temporal_processor.get_system_state()
        })

# Initialize and register system with app
def init_memory_system(app):
    """Initialize the memory system and register it with the app."""
    logger.info("Initializing memory system...")
    
    # Import and register routes
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Initialize default cycles and patterns
        temporal_processor.initialize_default_cycles()
        pattern_matcher.initialize_basic_patterns()
        
        # Start the temporal processor
        if not temporal_processor.running:
            temporal_processor.start()
        
        logger.info("Memory system initialized")