"""
Diagnostic Logging System for Deep Tree Echo

This module provides services for logging all thoughts, dreams, and chat interactions
for diagnostic and debugging purposes, with options for retention and analysis.
"""

import logging
import random
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import threading
import time

from database import db
from models_diagnostic import ThoughtLog, DreamLog, ChatLog, DiagnosticConfig
from models_memory import DreamState

logger = logging.getLogger(__name__)

class DiagnosticLogger:
    """
    Manages diagnostic logging for the Deep Tree Echo system.
    """
    def __init__(self):
        self.initialized = False
        self.config = None
        self.session_id = None
        self.background_thread = None
        self.running = False
        
        # For analysis queue
        self.analysis_queue = []
        self.analysis_lock = threading.Lock()
    
    def initialize(self):
        """Initialize the diagnostic logger."""
        from app import app
        
        with app.app_context():
            # Create session ID
            self.session_id = str(uuid.uuid4())
            
            # Load configuration
            self._load_config()
            
            # Initialize background thread for delayed analysis
            if self.config and self.config.perform_analysis:
                self.running = True
                self.background_thread = threading.Thread(target=self._analysis_worker)
                self.background_thread.daemon = True
                self.background_thread.start()
            
            self.initialized = True
            logger.info(f"Diagnostic logger initialized with session ID: {self.session_id}")
    
    def _load_config(self):
        """Load configuration from database or create default."""
        config = DiagnosticConfig.query.first()
        
        if not config:
            # Create default configuration
            config = DiagnosticConfig(
                enabled=True,
                log_thoughts=True,
                log_dreams=True,
                log_chats=True,
                retention_days=0,  # Keep indefinitely by default
                thought_sampling_rate=1.0,  # Log all thoughts
                perform_analysis=False,
                analysis_delay_seconds=3600,
                flagging_enabled=True
            )
            
            # Set default flagging criteria
            config.set_flagging_criteria({
                'keywords': ['error', 'exception', 'failure', 'crash'],
                'min_emotional_tone': -0.8,  # Flag very negative emotional tones
                'max_coherence': 0.2  # Flag very low coherence
            })
            
            db.session.add(config)
            db.session.commit()
        
        self.config = config
    
    def log_thought(self, content: str, thought_type: str = 'thought', source: str = 'system',
                  state_before: Optional[Dict] = None, state_after: Optional[Dict] = None,
                  generation_time_ms: Optional[float] = None, recursive_depth: Optional[int] = None,
                  tags: Optional[List[str]] = None) -> Optional[int]:
        """
        Log a thought to the database.
        Returns the ID of the created log entry, or None if logging is disabled.
        """
        if not self.initialized:
            self.initialize()
        
        # Check if logging is enabled
        if not self.config or not self.config.enabled or not self.config.log_thoughts:
            return None
        
        # Apply sampling rate
        if self.config.thought_sampling_rate < 1.0 and random.random() > self.config.thought_sampling_rate:
            return None
        
        try:
            # Create log entry
            log = ThoughtLog(
                timestamp=datetime.utcnow(),
                content=content,
                thought_type=thought_type,
                source=source,
                generation_time_ms=generation_time_ms,
                recursive_depth=recursive_depth,
                session_id=self.session_id
            )
            
            # Set optional fields
            if state_before:
                log.set_state_before(state_before)
            
            if state_after:
                log.set_state_after(state_after)
            
            if tags:
                log.set_tags(tags)
            
            # Flag if needed
            if self.config.flagging_enabled:
                self._check_for_flags(log)
            
            # Save to database
            db.session.add(log)
            db.session.commit()
            
            # Queue for analysis if enabled
            if self.config.perform_analysis:
                with self.analysis_lock:
                    self.analysis_queue.append(('thought', log.id))
            
            return log.id
        except Exception as e:
            logger.error(f"Error logging thought: {e}")
            return None
    
    def log_dream(self, content: Union[str, Dict], dream_type: str = 'rem', title: Optional[str] = None,
                dream_id: Optional[int] = None, start_time: Optional[datetime] = None,
                end_time: Optional[datetime] = None, duration_seconds: Optional[int] = None,
                source_memories: Optional[List[int]] = None, pattern_activations: Optional[Dict[int, float]] = None,
                insights: Optional[List[str]] = None, new_associations: Optional[List[Dict]] = None,
                emotional_tone: Optional[float] = None, coherence: Optional[float] = None) -> Optional[int]:
        """
        Log a dream to the database.
        Returns the ID of the created log entry, or None if logging is disabled.
        """
        if not self.initialized:
            self.initialize()
        
        # Check if logging is enabled
        if not self.config or not self.config.enabled or not self.config.log_dreams:
            return None
        
        try:
            # Create log entry
            log = DreamLog(
                dream_id=dream_id,
                timestamp=datetime.utcnow(),
                title=title or f"Dream {datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                dream_type=dream_type,
                start_time=start_time or datetime.utcnow(),
                end_time=end_time,
                duration_seconds=duration_seconds,
                emotional_tone=emotional_tone,
                coherence=coherence,
                session_id=self.session_id
            )
            
            # Set content
            log.set_content(content)
            
            # Set optional fields
            if source_memories:
                log.set_source_memories(source_memories)
            
            if pattern_activations:
                log.set_pattern_activations(pattern_activations)
            
            if insights:
                log.set_insights(insights)
            
            if new_associations:
                log.set_new_associations(new_associations)
            
            # Flag if needed
            if self.config.flagging_enabled:
                self._check_for_flags(log)
            
            # Save to database
            db.session.add(log)
            db.session.commit()
            
            # Queue for analysis if enabled
            if self.config.perform_analysis:
                with self.analysis_lock:
                    self.analysis_queue.append(('dream', log.id))
            
            return log.id
        except Exception as e:
            logger.error(f"Error logging dream: {e}")
            return None
    
    def log_chat(self, content: str, message_type: str = 'system',
               conversation_id: Optional[str] = None, parent_message_id: Optional[int] = None,
               user_id: Optional[int] = None, system_state: Optional[Dict] = None,
               processing_time_ms: Optional[float] = None, response_to: Optional[int] = None,
               response_type: Optional[str] = None) -> Optional[int]:
        """
        Log a chat message to the database.
        Returns the ID of the created log entry, or None if logging is disabled.
        """
        if not self.initialized:
            self.initialize()
        
        # Check if logging is enabled
        if not self.config or not self.config.enabled or not self.config.log_chats:
            return None
        
        try:
            # Create log entry
            log = ChatLog(
                timestamp=datetime.utcnow(),
                content=content,
                message_type=message_type,
                conversation_id=conversation_id or self.session_id,
                parent_message_id=parent_message_id,
                user_id=user_id,
                processing_time_ms=processing_time_ms,
                response_to=response_to,
                response_type=response_type
            )
            
            # Set system state if provided
            if system_state:
                log.set_system_state(system_state)
            
            # Flag if needed
            if self.config.flagging_enabled:
                self._check_for_flags(log)
            
            # Save to database
            db.session.add(log)
            db.session.commit()
            
            # Queue for analysis if enabled
            if self.config.perform_analysis:
                with self.analysis_lock:
                    self.analysis_queue.append(('chat', log.id))
            
            return log.id
        except Exception as e:
            logger.error(f"Error logging chat: {e}")
            return None
    
    def log_dream_state(self, dream_state: DreamState) -> Optional[int]:
        """
        Log a DreamState object to the database.
        Returns the ID of the created log entry, or None if logging is disabled.
        """
        if not dream_state:
            return None
        
        try:
            # Get dream properties
            content = dream_state.get_content() if hasattr(dream_state, 'get_content') else {}
            source_memories = dream_state.get_source_memories() if hasattr(dream_state, 'get_source_memories') else []
            pattern_activations = dream_state.get_pattern_activations() if hasattr(dream_state, 'get_pattern_activations') else {}
            insights = dream_state.get_insights() if hasattr(dream_state, 'get_insights') else []
            new_associations = dream_state.get_new_associations() if hasattr(dream_state, 'get_new_associations') else []
            
            # Log the dream
            return self.log_dream(
                content=content,
                dream_type=dream_state.dream_type,
                title=dream_state.title,
                dream_id=dream_state.id,
                start_time=dream_state.start_time,
                end_time=dream_state.end_time,
                duration_seconds=dream_state.duration_seconds,
                source_memories=source_memories,
                pattern_activations=pattern_activations,
                insights=insights,
                new_associations=new_associations,
                emotional_tone=dream_state.emotional_tone,
                coherence=dream_state.coherence
            )
        except Exception as e:
            logger.error(f"Error logging dream state: {e}")
            return None
    
    def _check_for_flags(self, log_entry: Union[ThoughtLog, DreamLog, ChatLog]):
        """Check if the log entry should be flagged based on criteria."""
        if not self.config or not self.config.flagging_criteria:
            return
        
        try:
            criteria = self.config.get_flagging_criteria()
            
            # Check keywords for all log types
            if 'keywords' in criteria and hasattr(log_entry, 'content'):
                content = log_entry.content.lower()
                for keyword in criteria['keywords']:
                    if keyword.lower() in content:
                        log_entry.flagged = True
                        log_entry.flag_reason = f"Contains keyword: {keyword}"
                        return
            
            # Dream-specific checks
            if isinstance(log_entry, DreamLog):
                # Check emotional tone
                if 'min_emotional_tone' in criteria and log_entry.emotional_tone is not None:
                    if log_entry.emotional_tone < criteria['min_emotional_tone']:
                        log_entry.flagged = True
                        log_entry.flag_reason = f"Low emotional tone: {log_entry.emotional_tone}"
                        return
                
                # Check coherence
                if 'max_coherence' in criteria and log_entry.coherence is not None:
                    if log_entry.coherence < criteria['max_coherence']:
                        log_entry.flagged = True
                        log_entry.flag_reason = f"Low coherence: {log_entry.coherence}"
                        return
        except Exception as e:
            logger.error(f"Error checking flags: {e}")
    
    def _analysis_worker(self):
        """Background worker for analyzing logged entries."""
        from app import app
        
        logger.info("Starting diagnostic analysis worker")
        
        while self.running:
            try:
                # Process queue if items available
                entries_to_process = []
                
                with self.analysis_lock:
                    # Get up to 10 entries to process
                    entries_to_process = self.analysis_queue[:10]
                    self.analysis_queue = self.analysis_queue[10:]
                
                if entries_to_process:
                    with app.app_context():
                        for entry_type, entry_id in entries_to_process:
                            self._analyze_entry(entry_type, entry_id)
                
                # Sleep before checking again
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"Error in analysis worker: {e}")
                time.sleep(5.0)  # Sleep longer on error
    
    def _analyze_entry(self, entry_type: str, entry_id: int):
        """Analyze a specific log entry."""
        try:
            if entry_type == 'thought':
                log = ThoughtLog.query.get(entry_id)
                if log:
                    # Perform analysis (placeholder)
                    analysis = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'word_count': len(log.content.split()),
                        'sentiment': self._analyze_sentiment(log.content)
                    }
                    log.set_analysis(analysis)
                    db.session.commit()
            
            elif entry_type == 'dream':
                log = DreamLog.query.get(entry_id)
                if log:
                    # Perform analysis (placeholder)
                    content = log.get_content()
                    if isinstance(content, dict) and 'narrative' in content:
                        narrative = content['narrative']
                    else:
                        narrative = str(content)
                    
                    analysis = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'word_count': len(narrative.split()) if isinstance(narrative, str) else 0,
                        'sentiment': self._analyze_sentiment(narrative) if isinstance(narrative, str) else 0.0,
                        'source_count': len(log.get_source_memories()),
                        'insight_count': len(log.get_insights())
                    }
                    log.set_analysis(analysis)
                    db.session.commit()
            
            elif entry_type == 'chat':
                log = ChatLog.query.get(entry_id)
                if log:
                    # Perform analysis (placeholder)
                    analysis = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'word_count': len(log.content.split()),
                        'sentiment': self._analyze_sentiment(log.content)
                    }
                    log.set_analysis(analysis)
                    db.session.commit()
        
        except Exception as e:
            logger.error(f"Error analyzing {entry_type} entry {entry_id}: {e}")
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Simple sentiment analysis.
        Returns a value between -1.0 (negative) and 1.0 (positive).
        """
        # This is a very basic implementation
        # In a real system, you would use a proper NLP library
        
        positive_words = ['good', 'great', 'excellent', 'positive', 'happy', 'joy', 'love', 'success']
        negative_words = ['bad', 'terrible', 'poor', 'negative', 'sad', 'fear', 'hate', 'failure']
        
        words = text.lower().split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count == 0 and negative_count == 0:
            return 0.0
        
        total = positive_count + negative_count
        return (positive_count - negative_count) / total
    
    def cleanup_old_logs(self):
        """Delete logs older than the retention period."""
        if not self.initialized:
            self.initialize()
        
        # Check if retention is enabled
        if not self.config or self.config.retention_days <= 0:
            return  # Keep logs indefinitely
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
            
            # Delete old logs
            ThoughtLog.query.filter(ThoughtLog.timestamp < cutoff_date).delete()
            DreamLog.query.filter(DreamLog.timestamp < cutoff_date).delete()
            ChatLog.query.filter(ChatLog.timestamp < cutoff_date).delete()
            
            db.session.commit()
            logger.info(f"Cleaned up logs older than {cutoff_date}")
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
    
    def get_thought_logs(self, limit: int = 100, thought_type: Optional[str] = None,
                       start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                       flagged_only: bool = False) -> List[ThoughtLog]:
        """Get thought logs based on filters."""
        query = ThoughtLog.query
        
        if thought_type:
            query = query.filter_by(thought_type=thought_type)
        
        if start_time:
            query = query.filter(ThoughtLog.timestamp >= start_time)
        
        if end_time:
            query = query.filter(ThoughtLog.timestamp <= end_time)
        
        if flagged_only:
            query = query.filter_by(flagged=True)
        
        return query.order_by(ThoughtLog.timestamp.desc()).limit(limit).all()
    
    def get_dream_logs(self, limit: int = 100, dream_type: Optional[str] = None,
                     start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                     flagged_only: bool = False) -> List[DreamLog]:
        """Get dream logs based on filters."""
        query = DreamLog.query
        
        if dream_type:
            query = query.filter_by(dream_type=dream_type)
        
        if start_time:
            query = query.filter(DreamLog.timestamp >= start_time)
        
        if end_time:
            query = query.filter(DreamLog.timestamp <= end_time)
        
        if flagged_only:
            query = query.filter_by(flagged=True)
        
        return query.order_by(DreamLog.timestamp.desc()).limit(limit).all()
    
    def get_chat_logs(self, limit: int = 100, message_type: Optional[str] = None,
                    conversation_id: Optional[str] = None, user_id: Optional[int] = None,
                    start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                    flagged_only: bool = False) -> List[ChatLog]:
        """Get chat logs based on filters."""
        query = ChatLog.query
        
        if message_type:
            query = query.filter_by(message_type=message_type)
        
        if conversation_id:
            query = query.filter_by(conversation_id=conversation_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if start_time:
            query = query.filter(ChatLog.timestamp >= start_time)
        
        if end_time:
            query = query.filter(ChatLog.timestamp <= end_time)
        
        if flagged_only:
            query = query.filter_by(flagged=True)
        
        return query.order_by(ChatLog.timestamp.desc()).limit(limit).all()
    
    def get_config(self) -> Optional[DiagnosticConfig]:
        """Get the diagnostic configuration."""
        if not self.initialized:
            self.initialize()
        
        return self.config
    
    def update_config(self, config_updates: Dict) -> Optional[DiagnosticConfig]:
        """Update the diagnostic configuration."""
        if not self.initialized:
            self.initialize()
        
        if not self.config:
            return None
        
        try:
            # Update configuration fields
            if 'enabled' in config_updates:
                self.config.enabled = bool(config_updates['enabled'])
            
            if 'log_thoughts' in config_updates:
                self.config.log_thoughts = bool(config_updates['log_thoughts'])
            
            if 'log_dreams' in config_updates:
                self.config.log_dreams = bool(config_updates['log_dreams'])
            
            if 'log_chats' in config_updates:
                self.config.log_chats = bool(config_updates['log_chats'])
            
            if 'retention_days' in config_updates:
                self.config.retention_days = int(config_updates['retention_days'])
            
            if 'thought_sampling_rate' in config_updates:
                rate = float(config_updates['thought_sampling_rate'])
                self.config.thought_sampling_rate = max(0.0, min(1.0, rate))
            
            if 'perform_analysis' in config_updates:
                new_analysis = bool(config_updates['perform_analysis'])
                
                # Start analysis thread if newly enabled
                if new_analysis and not self.config.perform_analysis and not self.running:
                    self.running = True
                    self.background_thread = threading.Thread(target=self._analysis_worker)
                    self.background_thread.daemon = True
                    self.background_thread.start()
                
                self.config.perform_analysis = new_analysis
            
            if 'analysis_delay_seconds' in config_updates:
                self.config.analysis_delay_seconds = int(config_updates['analysis_delay_seconds'])
            
            if 'flagging_enabled' in config_updates:
                self.config.flagging_enabled = bool(config_updates['flagging_enabled'])
            
            if 'flagging_criteria' in config_updates:
                self.config.set_flagging_criteria(config_updates['flagging_criteria'])
            
            # Update timestamp
            self.config.last_updated = datetime.utcnow()
            
            db.session.commit()
            return self.config
        
        except Exception as e:
            logger.error(f"Error updating diagnostic configuration: {e}")
            return None
    
    def shutdown(self):
        """Shutdown the diagnostic logger."""
        self.running = False
        
        if self.background_thread:
            self.background_thread.join(timeout=1.0)
            self.background_thread = None
        
        logger.info("Diagnostic logger shut down")

# Global instance
diagnostic_logger = DiagnosticLogger()