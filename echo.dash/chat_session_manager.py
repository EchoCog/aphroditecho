import os
import json
import uuid
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
# Temporarily comment out complex dependencies to avoid import errors
# from memory_management import HypergraphMemory, MemoryType, MemoryNode
# from deep_tree_echo import TreeNode

# We'll add these back once all dependencies are installed
HypergraphMemory = None  # Placeholder
MemoryType = None  # Placeholder
MemoryNode = None  # Placeholder
TreeNode = None  # Placeholder

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatPlatform(Enum):
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    WINDSURF = "windsurf"
    BROWSER = "browser"
    API = "api"
    UNKNOWN = "unknown"

class SessionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ARCHIVED = "archived"

@dataclass
class ChatMessage:
    """Represents a single chat message"""
    id: str
    session_id: str
    timestamp: float
    platform: ChatPlatform
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    echo_value: float = 0.0
    salience: float = 0.5
    parent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['platform'] = self.platform.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        """Create from dictionary"""
        data['platform'] = ChatPlatform(data['platform'])
        return cls(**data)

@dataclass
class ChatSession:
    """Represents a complete chat session"""
    id: str
    platform: ChatPlatform
    title: str
    start_time: float
    end_time: Optional[float] = None
    status: SessionStatus = SessionStatus.ACTIVE
    messages: List[ChatMessage] = field(default_factory=list)
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    total_messages: int = 0
    avg_echo_value: float = 0.0
    avg_salience: float = 0.5
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['platform'] = self.platform.value
        data['status'] = self.status.value
        data['messages'] = [msg.to_dict() for msg in self.messages]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatSession':
        """Create from dictionary"""
        data['platform'] = ChatPlatform(data['platform'])
        data['status'] = SessionStatus(data['status'])
        data['messages'] = [ChatMessage.from_dict(msg) for msg in data['messages']]
        return cls(**data)
    
    def add_message(self, message: ChatMessage):
        """Add a message to the session"""
        self.messages.append(message)
        self.total_messages = len(self.messages)
        self._update_statistics()
    
    def _update_statistics(self):
        """Update session statistics"""
        if self.messages:
            self.avg_echo_value = sum(msg.echo_value for msg in self.messages) / len(self.messages)
            self.avg_salience = sum(msg.salience for msg in self.messages) / len(self.messages)

class ChatSessionManager:
    """Manages automatic chat session saving and retrieval"""
    
    def __init__(self, storage_dir: str = "memory_storage"):
        # Set up logging first
        self.logger = logging.getLogger(__name__)
        
        self.storage_dir = Path(storage_dir)
        self.sessions_dir = self.storage_dir / "chat_sessions"
        self.indices_dir = self.storage_dir / "session_indices"
        
        # Create directories
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory integration (placeholder for now)
        if HypergraphMemory:
            self.memory_system = HypergraphMemory(storage_dir=storage_dir)
        else:
            self.memory_system = None  # Will integrate later when dependencies are available
        
        # Session tracking
        self.active_sessions: Dict[str, ChatSession] = {}
        self.session_indices: Dict[str, Dict] = {}
        self.auto_save_interval = 30  # seconds
        self.auto_save_thread = None
        self.running = False
        
        # Load existing data
        self._load_session_indices()
        self._load_active_sessions()
        
    def start_auto_save(self):
        """Start automatic session saving thread"""
        if not self.running:
            self.running = True
            self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
            self.auto_save_thread.start()
            self.logger.info("Started automatic session saving")
    
    def stop_auto_save(self):
        """Stop automatic session saving"""
        self.running = False
        if self.auto_save_thread:
            self.auto_save_thread.join()
        self.logger.info("Stopped automatic session saving")
    
    def _auto_save_loop(self):
        """Background thread for automatic saving"""
        while self.running:
            try:
                self._save_active_sessions()
                time.sleep(self.auto_save_interval)
            except Exception as e:
                self.logger.error(f"Error in auto-save loop: {str(e)}")
    
    def create_session(self, platform: ChatPlatform, title: str = None, 
                      conversation_id: str = None, metadata: Dict = None) -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        
        if title is None:
            title = f"{platform.value.title()} Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        session = ChatSession(
            id=session_id,
            platform=platform,
            title=title,
            start_time=time.time(),
            conversation_id=conversation_id,
            metadata=metadata or {}
        )
        
        self.active_sessions[session_id] = session
        self._update_session_index(session)
        
        self.logger.info(f"Created new {platform.value} session: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, 
                   platform: ChatPlatform = None, metadata: Dict = None,
                   conversation_id: str = None, parent_id: str = None) -> str:
        """Add a message to a session"""
        if session_id not in self.active_sessions:
            # Auto-create session if it doesn't exist
            if platform is None:
                platform = ChatPlatform.UNKNOWN
            session_id = self.create_session(platform)
        
        session = self.active_sessions[session_id]
        
        message_id = str(uuid.uuid4())
        message = ChatMessage(
            id=message_id,
            session_id=session_id,
            timestamp=time.time(),
            platform=session.platform,
            role=role,
            content=content,
            metadata=metadata or {},
            conversation_id=conversation_id,
            parent_id=parent_id
        )
        
        # Calculate echo value and salience
        message.echo_value = self._calculate_echo_value(content)
        message.salience = self._calculate_salience(content, role)
        
        session.add_message(message)
        
        # Store in memory system for persistent learning
        self._store_in_memory_system(message)
        
        self.logger.debug(f"Added message to session {session_id}: {role} - {len(content)} chars")
        return message_id
    
    def end_session(self, session_id: str):
        """End a chat session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_time = time.time()
            session.status = SessionStatus.ENDED
            
            # Final save
            self._save_session(session)
            self._update_session_index(session)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            self.logger.info(f"Ended session {session_id} with {session.total_messages} messages")
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID"""
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Load from disk
        return self._load_session(session_id)
    
    def search_sessions(self, query: str = None, platform: ChatPlatform = None,
                       start_date: datetime = None, end_date: datetime = None,
                       tags: List[str] = None, limit: int = 50) -> List[Dict]:
        """Search sessions with filters"""
        results = []
        
        for session_info in self.session_indices.values():
            # Filter by platform
            if platform and session_info.get('platform') != platform.value:
                continue
            
            # Filter by date range
            if start_date and session_info.get('start_time', 0) < start_date.timestamp():
                continue
            if end_date and session_info.get('start_time', 0) > end_date.timestamp():
                continue
            
            # Filter by tags
            if tags and not any(tag in session_info.get('tags', []) for tag in tags):
                continue
            
            # Text search in title
            if query and query.lower() not in session_info.get('title', '').lower():
                continue
            
            results.append(session_info)
            if len(results) >= limit:
                break
        
        # Sort by start time (newest first)
        results.sort(key=lambda x: x.get('start_time', 0), reverse=True)
        return results
    
    def get_conversation_history(self, platform: ChatPlatform = None, 
                               days: int = 7) -> List[ChatMessage]:
        """Get recent conversation history across sessions"""
        cutoff_time = time.time() - (days * 24 * 3600)
        messages = []
        
        # Get from active sessions
        for session in self.active_sessions.values():
            if platform is None or session.platform == platform:
                for msg in session.messages:
                    if msg.timestamp >= cutoff_time:
                        messages.append(msg)
        
        # Get from recent archived sessions
        recent_sessions = self.search_sessions(
            start_date=datetime.fromtimestamp(cutoff_time),
            platform=platform,
            limit=100
        )
        
        for session_info in recent_sessions:
            session = self._load_session(session_info['id'])
            if session:
                for msg in session.messages:
                    if msg.timestamp >= cutoff_time:
                        messages.append(msg)
        
        # Sort by timestamp
        messages.sort(key=lambda x: x.timestamp)
        return messages
    
    def aggregate_conversations(self, target_session_id: str = None) -> str:
        """Aggregate conversations from multiple platforms into a unified session"""
        if target_session_id is None:
            target_session_id = self.create_session(
                ChatPlatform.UNKNOWN, 
                f"Aggregated Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        
        # Get recent messages from all platforms
        all_messages = self.get_conversation_history(days=1)
        
        # Group by conversation threads
        threads = self._group_messages_by_thread(all_messages)
        
        # Merge into target session
        target_session = self.active_sessions[target_session_id]
        for thread in threads:
            for msg in thread:
                # Create a copy with new session_id
                aggregated_msg = ChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=target_session_id,
                    timestamp=msg.timestamp,
                    platform=msg.platform,
                    role=msg.role,
                    content=msg.content,
                    metadata={**msg.metadata, 'original_session': msg.session_id},
                    echo_value=msg.echo_value,
                    salience=msg.salience,
                    parent_id=msg.parent_id,
                    conversation_id=msg.conversation_id
                )
                target_session.add_message(aggregated_msg)
        
        self.logger.info(f"Aggregated {len(all_messages)} messages into session {target_session_id}")
        return target_session_id
    
    def integrate_with_existing_storage(self):
        """Integrate with existing conversation storage patterns"""
        # Check for existing selenium interface memory
        selenium_memory_file = Path("activity_logs/browser/chat_memory.json")
        if selenium_memory_file.exists():
            self._import_selenium_memory(selenium_memory_file)
        
        # Check for other memory systems
        self._import_cognitive_architecture_memory()
        self._import_evolution_memory()
    
    def _import_selenium_memory(self, memory_file: Path):
        """Import existing selenium interface conversation history"""
        try:
            with open(memory_file, 'r') as f:
                conversations = json.load(f)
            
            if conversations:
                session_id = self.create_session(
                    ChatPlatform.BROWSER,
                    "Imported Browser Session",
                    metadata={'imported_from': str(memory_file)}
                )
                
                for conv in conversations:
                    # Add user message
                    if 'message' in conv:
                        self.add_message(
                            session_id, 'user', conv['message'],
                            platform=ChatPlatform.BROWSER,
                            metadata={'timestamp': conv.get('timestamp'), 'url': conv.get('url')}
                        )
                    
                    # Add assistant response
                    if 'response' in conv and conv['response']:
                        self.add_message(
                            session_id, 'assistant', conv['response'],
                            platform=ChatPlatform.BROWSER,
                            metadata={'timestamp': conv.get('timestamp'), 'url': conv.get('url')}
                        )
                
                self.logger.info(f"Imported {len(conversations)} conversations from selenium memory")
        
        except Exception as e:
            self.logger.error(f"Error importing selenium memory: {str(e)}")
    
    def _import_cognitive_architecture_memory(self):
        """Import from cognitive architecture activity logs"""
        try:
            memory_dir = Path("memory_storage")
            if memory_dir.exists():
                activities_file = memory_dir / "activities.json"
                if activities_file.exists():
                    with open(activities_file, 'r') as f:
                        activities = json.load(f)
                    
                    # Filter for chat-related activities
                    chat_activities = [a for a in activities if 'chat' in a.get('type', '').lower()]
                    
                    if chat_activities:
                        session_id = self.create_session(
                            ChatPlatform.UNKNOWN,
                            "Imported Cognitive Activities",
                            metadata={'imported_from': 'cognitive_architecture'}
                        )
                        
                        for activity in chat_activities:
                            self.add_message(
                                session_id, 'system', str(activity.get('details', '')),
                                metadata={'activity_type': activity.get('type')}
                            )
        
        except Exception as e:
            self.logger.error(f"Error importing cognitive architecture memory: {str(e)}")
    
    def _import_evolution_memory(self):
        """Import from evolution memory cycles"""
        try:
            evolution_file = Path("memory_storage/evolution_memory.json")
            if evolution_file.exists():
                with open(evolution_file, 'r') as f:
                    evolution_data = json.load(f)
                
                cycles = evolution_data.get('cycles', [])
                if cycles:
                    session_id = self.create_session(
                        ChatPlatform.UNKNOWN,
                        "Evolution Memory Cycles",
                        metadata={'imported_from': 'evolution_memory'}
                    )
                    
                    for cycle in cycles:
                        self.add_message(
                            session_id, 'system', json.dumps(cycle),
                            metadata={'cycle_type': 'evolution'}
                        )
        
        except Exception as e:
            self.logger.error(f"Error importing evolution memory: {str(e)}")
    
    def _calculate_echo_value(self, content: str) -> float:
        """Calculate echo value for content using Deep Tree Echo system"""
        try:
            if TreeNode:
                # Create a tree node for analysis when available
                node = TreeNode(content)
                # Use ML-based analysis when dependencies are available
                word_count = len(content.split())
                complexity = min(word_count / 100.0, 1.0)  # Normalize to 0-1
                return complexity * 0.8  # Scale down for conservative estimates
            else:
                # Use simple heuristics for now
                word_count = len(content.split())
                complexity = min(word_count / 100.0, 1.0)  # Normalize to 0-1
                
                # Boost for technical terms, questions, etc.
                if any(term in content.lower() for term in ['error', 'code', 'function', 'class', 'import']):
                    complexity += 0.2
                if '?' in content:
                    complexity += 0.1
                    
                return min(complexity * 0.8, 1.0)  # Scale and cap at 1.0
        except Exception as e:
            self.logger.debug(f"Error calculating echo value: {str(e)}")
            return 0.5  # Default value
    
    def _calculate_salience(self, content: str, role: str) -> float:
        """Calculate salience (importance) of content"""
        salience = 0.5  # Base salience
        
        # Boost for questions
        if '?' in content:
            salience += 0.1
        
        # Boost for longer content
        word_count = len(content.split())
        if word_count > 50:
            salience += 0.1
        
        # Boost for user messages (more important than assistant messages)
        if role == 'user':
            salience += 0.1
        
        # Boost for content with certain keywords
        important_keywords = ['error', 'problem', 'help', 'important', 'critical', 'urgent']
        if any(keyword in content.lower() for keyword in important_keywords):
            salience += 0.2
        
        return min(salience, 1.0)
    
    def _store_in_memory_system(self, message: ChatMessage):
        """Store message in the hypergraph memory system"""
        try:
            if not self.memory_system:
                # Log for future integration when dependencies are available
                self.logger.debug(f"Memory system not available - would store: {message.role} message")
                return
            
            # Determine memory type based on role and content
            if message.role == 'user':
                memory_type = MemoryType.EPISODIC  # User experiences/questions
            elif message.role == 'assistant':
                memory_type = MemoryType.SEMANTIC  # Knowledge responses
            else:
                memory_type = MemoryType.WORKING  # System messages
            
            # Create memory node
            memory_node = MemoryNode(
                id=message.id,
                content=message.content,
                memory_type=memory_type,
                creation_time=message.timestamp,
                salience=message.salience,
                echo_value=message.echo_value,
                source=f"{message.platform.value}_chat",
                metadata={
                    'session_id': message.session_id,
                    'role': message.role,
                    'platform': message.platform.value,
                    'conversation_id': message.conversation_id,
                    **message.metadata
                }
            )
            
            # Add to memory system
            self.memory_system.add_node(memory_node)
            
            # Create associations with recent messages in the same session
            self._create_message_associations(message)
            
        except Exception as e:
            self.logger.error(f"Error storing message in memory system: {str(e)}")
    
    def _create_message_associations(self, message: ChatMessage):
        """Create associations between related messages"""
        try:
            if not self.memory_system:
                # Log associations for future implementation
                session = self.active_sessions.get(message.session_id)
                if session and len(session.messages) > 1:
                    prev_message = session.messages[-2]
                    self.logger.debug(f"Would create association: {prev_message.id} -> {message.id}")
                return
            
            # Get recent messages from the same session
            session = self.active_sessions.get(message.session_id)
            if session and len(session.messages) > 1:
                # Associate with the previous message
                prev_message = session.messages[-2]  # -1 is current message, -2 is previous
                
                self.memory_system.add_edge(
                    prev_message.id,
                    message.id,
                    "conversation_flow",
                    strength=0.8,
                    metadata={'temporal_distance': message.timestamp - prev_message.timestamp}
                )
                
                # If this is a response to a question, create stronger association
                if prev_message.role == 'user' and message.role == 'assistant':
                    self.memory_system.add_edge(
                        prev_message.id,
                        message.id,
                        "question_answer",
                        strength=0.9,
                        metadata={'response_type': 'answer'}
                    )
        
        except Exception as e:
            self.logger.error(f"Error creating message associations: {str(e)}")
    
    def _group_messages_by_thread(self, messages: List[ChatMessage]) -> List[List[ChatMessage]]:
        """Group messages into conversation threads"""
        threads = []
        current_thread = []
        
        for message in sorted(messages, key=lambda x: x.timestamp):
            # Start new thread if there's a significant time gap or platform change
            if (current_thread and 
                (message.timestamp - current_thread[-1].timestamp > 3600 or  # 1 hour gap
                 message.platform != current_thread[-1].platform)):
                threads.append(current_thread)
                current_thread = [message]
            else:
                current_thread.append(message)
        
        if current_thread:
            threads.append(current_thread)
        
        return threads
    
    def _save_session(self, session: ChatSession):
        """Save a single session to disk"""
        try:
            session_file = self.sessions_dir / f"{session.id}.json"
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving session {session.id}: {str(e)}")
    
    def _load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load a session from disk"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r') as f:
                    data = json.load(f)
                return ChatSession.from_dict(data)
        except Exception as e:
            self.logger.error(f"Error loading session {session_id}: {str(e)}")
        return None
    
    def _save_active_sessions(self):
        """Save all active sessions"""
        for session in self.active_sessions.values():
            self._save_session(session)
        self._save_session_indices()
    
    def _load_active_sessions(self):
        """Load recently active sessions"""
        # Load sessions that were active in the last 24 hours
        cutoff_time = time.time() - (24 * 3600)
        
        for session_info in self.session_indices.values():
            if (session_info.get('status') == SessionStatus.ACTIVE.value and
                session_info.get('start_time', 0) > cutoff_time):
                session = self._load_session(session_info['id'])
                if session:
                    self.active_sessions[session.id] = session
        
        self.logger.info(f"Loaded {len(self.active_sessions)} active sessions")
    
    def _update_session_index(self, session: ChatSession):
        """Update the session index with session info"""
        self.session_indices[session.id] = {
            'id': session.id,
            'platform': session.platform.value,
            'title': session.title,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'status': session.status.value,
            'total_messages': session.total_messages,
            'avg_echo_value': session.avg_echo_value,
            'avg_salience': session.avg_salience,
            'tags': session.tags,
            'metadata': session.metadata
        }
    
    def _save_session_indices(self):
        """Save session indices to disk"""
        try:
            indices_file = self.indices_dir / 'sessions.json'
            with open(indices_file, 'w') as f:
                json.dump(self.session_indices, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving session indices: {str(e)}")
    
    def _load_session_indices(self):
        """Load session indices from disk"""
        try:
            indices_file = self.indices_dir / 'sessions.json'
            if indices_file.exists():
                with open(indices_file, 'r') as f:
                    self.session_indices = json.load(f)
                self.logger.info(f"Loaded {len(self.session_indices)} session indices")
        except Exception as e:
            self.logger.error(f"Error loading session indices: {str(e)}")
            self.session_indices = {}
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics about chat sessions"""
        stats = {
            'total_sessions': len(self.session_indices),
            'active_sessions': len(self.active_sessions),
            'platforms': {},
            'total_messages': 0,
            'avg_session_length': 0,
            'most_active_platform': None,
            'recent_activity': {}
        }
        
        # Platform statistics
        for session_info in self.session_indices.values():
            platform = session_info.get('platform', 'unknown')
            if platform not in stats['platforms']:
                stats['platforms'][platform] = {'sessions': 0, 'messages': 0}
            
            stats['platforms'][platform]['sessions'] += 1
            stats['platforms'][platform]['messages'] += session_info.get('total_messages', 0)
            stats['total_messages'] += session_info.get('total_messages', 0)
        
        # Calculate averages
        if stats['total_sessions'] > 0:
            stats['avg_session_length'] = stats['total_messages'] / stats['total_sessions']
        
        # Most active platform
        if stats['platforms']:
            stats['most_active_platform'] = max(
                stats['platforms'].keys(),
                key=lambda p: stats['platforms'][p]['messages']
            )
        
        # Recent activity (last 7 days)
        cutoff_time = time.time() - (7 * 24 * 3600)
        recent_sessions = [s for s in self.session_indices.values() 
                          if s.get('start_time', 0) > cutoff_time]
        
        stats['recent_activity'] = {
            'sessions': len(recent_sessions),
            'messages': sum(s.get('total_messages', 0) for s in recent_sessions)
        }
        
        return stats

# Global session manager instance
session_manager = ChatSessionManager()

# Integration functions for existing modules
def initialize_session_manager():
    """Initialize the global session manager"""
    session_manager.integrate_with_existing_storage()
    session_manager.start_auto_save()
    logger.info("Chat session manager initialized")

def create_chat_session(platform: str, title: str = None, **kwargs) -> str:
    """Create a new chat session - convenient wrapper"""
    platform_enum = ChatPlatform(platform.lower()) if platform else ChatPlatform.UNKNOWN
    return session_manager.create_session(platform_enum, title, **kwargs)

def log_chat_message(session_id: str, role: str, content: str, **kwargs) -> str:
    """Log a chat message - convenient wrapper"""
    return session_manager.add_message(session_id, role, content, **kwargs)

def end_chat_session(session_id: str):
    """End a chat session - convenient wrapper"""
    session_manager.end_session(session_id)

def get_chat_history(platform: str = None, days: int = 7) -> List[Dict]:
    """Get chat history - convenient wrapper"""
    platform_enum = ChatPlatform(platform.lower()) if platform else None
    messages = session_manager.get_conversation_history(platform_enum, days)
    return [msg.to_dict() for msg in messages]

if __name__ == "__main__":
    # Test the session manager
    initialize_session_manager()
    
    # Create a test session
    session_id = create_chat_session("chatgpt", "Test Session")
    
    # Add some test messages
    log_chat_message(session_id, "user", "Hello, how are you?")
    log_chat_message(session_id, "assistant", "I'm doing well, thank you for asking!")
    
    # Get statistics
    stats = session_manager.get_statistics()
    print(f"Session statistics: {json.dumps(stats, indent=2)}")
    
    # End session
    end_chat_session(session_id)
    
    logger.info("Test completed successfully")
