"""
Diagnostic API for Deep Tree Echo

This module provides API routes for accessing diagnostic logs
and configuring the diagnostic logging system.
"""

from flask import jsonify, request, render_template
from flask_login import login_required, current_user
import logging
from datetime import datetime, timedelta

from app import app
from database import db
from models_diagnostic import ThoughtLog, DreamLog, ChatLog, DiagnosticConfig
from diagnostic_logger import diagnostic_logger

logger = logging.getLogger(__name__)

# Web interface for diagnostic logs
@app.route('/diagnostics')
@login_required
def diagnostics_dashboard():
    """Diagnostics dashboard for viewing logs."""
    return render_template('diagnostics.html')

# API routes for diagnostic logs
@app.route('/api/diagnostics/thoughts', methods=['GET'])
@login_required
def get_diagnostic_thoughts():
    """Get thought logs, optionally filtered by type, time range, etc."""
    # Get filter parameters
    thought_type = request.args.get('type')
    since = request.args.get('since')  # ISO format datetime
    limit = request.args.get('limit', default=100, type=int)
    flagged = request.args.get('flagged', default=False, type=lambda v: v.lower() == 'true')
    
    # Build query
    query = ThoughtLog.query
    
    if thought_type:
        query = query.filter_by(thought_type=thought_type)
    
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(ThoughtLog.timestamp >= since_dt)
        except ValueError:
            # Invalid datetime format, ignore the parameter
            pass
    
    if flagged:
        query = query.filter_by(flagged=True)
    
    # Order by timestamp descending (newest first)
    thoughts = query.order_by(ThoughtLog.timestamp.desc()).limit(limit).all()
    
    # Format for response
    result = []
    for thought in thoughts:
        result.append({
            'id': thought.id,
            'timestamp': thought.timestamp.isoformat(),
            'content': thought.content,
            'thought_type': thought.thought_type,
            'source': thought.source,
            'recursive_depth': thought.recursive_depth,
            'tags': thought.get_tags(),
            'flagged': thought.flagged,
            'flag_reason': thought.flag_reason
        })
    
    return jsonify(result)

@app.route('/api/diagnostics/dreams', methods=['GET'])
@login_required
def get_diagnostic_dreams():
    """Get dream logs, optionally filtered by type, time range, etc."""
    # Get filter parameters
    dream_type = request.args.get('type')
    since = request.args.get('since')  # ISO format datetime
    limit = request.args.get('limit', default=100, type=int)
    flagged = request.args.get('flagged', default=False, type=lambda v: v.lower() == 'true')
    
    # Build query
    query = DreamLog.query
    
    if dream_type:
        query = query.filter_by(dream_type=dream_type)
    
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(DreamLog.timestamp >= since_dt)
        except ValueError:
            # Invalid datetime format, ignore the parameter
            pass
    
    if flagged:
        query = query.filter_by(flagged=True)
    
    # Order by timestamp descending (newest first)
    dreams = query.order_by(DreamLog.timestamp.desc()).limit(limit).all()
    
    # Format for response
    result = []
    for dream in dreams:
        result.append({
            'id': dream.id,
            'timestamp': dream.timestamp.isoformat(),
            'title': dream.title,
            'content': dream.content,
            'dream_type': dream.dream_type,
            'emotional_tone': dream.emotional_tone,
            'coherence': dream.coherence,
            'insights': dream.get_insights(),
            'flagged': dream.flagged,
            'flag_reason': dream.flag_reason
        })
    
    return jsonify(result)

@app.route('/api/diagnostics/chats', methods=['GET'])
@login_required
def get_diagnostic_chats():
    """Get chat logs, optionally filtered by type, conversation, etc."""
    # Get filter parameters
    message_type = request.args.get('type')
    conversation_id = request.args.get('conversation_id')
    since = request.args.get('since')  # ISO format datetime
    limit = request.args.get('limit', default=100, type=int)
    flagged = request.args.get('flagged', default=False, type=lambda v: v.lower() == 'true')
    
    # Build query
    query = ChatLog.query
    
    if message_type:
        query = query.filter_by(message_type=message_type)
    
    if conversation_id:
        query = query.filter_by(conversation_id=conversation_id)
    
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(ChatLog.timestamp >= since_dt)
        except ValueError:
            # Invalid datetime format, ignore the parameter
            pass
    
    if flagged:
        query = query.filter_by(flagged=True)
    
    # Order by timestamp descending (newest first)
    chats = query.order_by(ChatLog.timestamp.desc()).limit(limit).all()
    
    # Format for response
    result = []
    for chat in chats:
        result.append({
            'id': chat.id,
            'timestamp': chat.timestamp.isoformat(),
            'message_type': chat.message_type,
            'content': chat.content,
            'conversation_id': chat.conversation_id,
            'parent_message_id': chat.parent_message_id,
            'user_id': chat.user_id,
            'processing_time_ms': chat.processing_time_ms,
            'flagged': chat.flagged,
            'flag_reason': chat.flag_reason
        })
    
    return jsonify(result)

@app.route('/api/diagnostics/statistics', methods=['GET'])
@login_required
def get_diagnostic_statistics():
    """Get statistics about diagnostic logs."""
    # Count total logs by type
    thought_count = ThoughtLog.query.count()
    dream_count = DreamLog.query.count()
    chat_count = ChatLog.query.count()
    
    # Count logs from the last 24 hours
    since_24h = datetime.utcnow() - timedelta(hours=24)
    thought_count_24h = ThoughtLog.query.filter(ThoughtLog.timestamp >= since_24h).count()
    dream_count_24h = DreamLog.query.filter(DreamLog.timestamp >= since_24h).count()
    chat_count_24h = ChatLog.query.filter(ChatLog.timestamp >= since_24h).count()
    
    # Count flagged logs
    flagged_thoughts = ThoughtLog.query.filter_by(flagged=True).count()
    flagged_dreams = DreamLog.query.filter_by(flagged=True).count()
    flagged_chats = ChatLog.query.filter_by(flagged=True).count()
    
    # Get thought type breakdown
    thought_types = db.session.query(ThoughtLog.thought_type, db.func.count(ThoughtLog.id)).\
        group_by(ThoughtLog.thought_type).all()
    thought_types_count = {t_type: count for t_type, count in thought_types}
    
    # Get dream type breakdown
    dream_types = db.session.query(DreamLog.dream_type, db.func.count(DreamLog.id)).\
        group_by(DreamLog.dream_type).all()
    dream_types_count = {d_type: count for d_type, count in dream_types}
    
    # Get chat message type breakdown
    message_types = db.session.query(ChatLog.message_type, db.func.count(ChatLog.id)).\
        group_by(ChatLog.message_type).all()
    message_types_count = {m_type: count for m_type, count in message_types}
    
    # Get configuration status
    config = diagnostic_logger.get_config()
    config_status = {
        'enabled': config.enabled if config else False,
        'log_thoughts': config.log_thoughts if config else False,
        'log_dreams': config.log_dreams if config else False,
        'log_chats': config.log_chats if config else False,
        'retention_days': config.retention_days if config else 0,
        'thought_sampling_rate': config.thought_sampling_rate if config else 1.0,
        'last_updated': config.last_updated.isoformat() if config and config.last_updated else None
    }
    
    return jsonify({
        'total_logs': {
            'thoughts': thought_count,
            'dreams': dream_count,
            'chats': chat_count,
            'total': thought_count + dream_count + chat_count
        },
        'last_24h_logs': {
            'thoughts': thought_count_24h,
            'dreams': dream_count_24h,
            'chats': chat_count_24h,
            'total': thought_count_24h + dream_count_24h + chat_count_24h
        },
        'flagged_logs': {
            'thoughts': flagged_thoughts,
            'dreams': flagged_dreams,
            'chats': flagged_chats,
            'total': flagged_thoughts + flagged_dreams + flagged_chats
        },
        'thought_types': thought_types_count,
        'dream_types': dream_types_count,
        'message_types': message_types_count,
        'config': config_status,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/diagnostics/config', methods=['GET'])
@login_required
def get_diagnostic_config():
    """Get the current diagnostic configuration."""
    config = diagnostic_logger.get_config()
    
    if not config:
        return jsonify({'error': 'Configuration not found'}), 404
    
    return jsonify({
        'id': config.id,
        'enabled': config.enabled,
        'log_thoughts': config.log_thoughts,
        'log_dreams': config.log_dreams,
        'log_chats': config.log_chats,
        'retention_days': config.retention_days,
        'thought_sampling_rate': config.thought_sampling_rate,
        'perform_analysis': config.perform_analysis,
        'analysis_delay_seconds': config.analysis_delay_seconds,
        'flagging_enabled': config.flagging_enabled,
        'flagging_criteria': config.get_flagging_criteria(),
        'last_updated': config.last_updated.isoformat() if config.last_updated else None
    })

@app.route('/api/diagnostics/config', methods=['PUT'])
@login_required
def update_diagnostic_config():
    """Update the diagnostic configuration."""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        # Update configuration
        config = diagnostic_logger.update_config(data)
        
        if not config:
            return jsonify({'error': 'Failed to update configuration'}), 500
        
        return jsonify({
            'id': config.id,
            'enabled': config.enabled,
            'log_thoughts': config.log_thoughts,
            'log_dreams': config.log_dreams,
            'log_chats': config.log_chats,
            'retention_days': config.retention_days,
            'thought_sampling_rate': config.thought_sampling_rate,
            'perform_analysis': config.perform_analysis,
            'analysis_delay_seconds': config.analysis_delay_seconds,
            'flagging_enabled': config.flagging_enabled,
            'flagging_criteria': config.get_flagging_criteria(),
            'last_updated': config.last_updated.isoformat() if config.last_updated else None
        })
    except Exception as e:
        logger.error(f"Error updating diagnostic configuration: {e}")
        return jsonify({'error': str(e)}), 500