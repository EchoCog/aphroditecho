"""
Topics Module for Deep Tree Echo

This module handles the causal dimension of the user level, providing 
forum/thread/message structures for discussions and knowledge organization.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)

class UserTopics:
    """Manages user forums, threads, and messages."""
    
    def __init__(self):
        """Initialize the topics manager."""
        self.user_id = "default_user"
        
        # Data stores
        self.forums = {}  # forum_id -> forum data
        self.threads = {}  # thread_id -> thread data
        self.messages = {}  # message_id -> message data
        self.message_reactions = {}  # reaction_id -> reaction data
        
        # Relationship mappings
        self.forum_threads = {}  # forum_id -> [thread_ids]
        self.thread_messages = {}  # thread_id -> [message_ids]
        self.message_child_messages = {}  # message_id -> [child_message_ids]
        self.message_reactions_map = {}  # message_id -> [reaction_ids]
        
        logger.info("User topics module initialized")
        
    def create_forum(self, name: str, forum_type: str = "discussion",
                   description: str = None, visibility: str = "public",
                   tags: List[str] = None, attributes: Dict[str, Any] = None) -> str:
        """Create a forum for organizing discussion threads.
        
        Args:
            name: The name of the forum
            forum_type: Type of forum (discussion, Q&A, documentation, etc.)
            description: Optional description
            visibility: Visibility level (public, private, restricted)
            tags: Optional list of tags
            attributes: Optional additional attributes
            
        Returns:
            The ID of the created forum
        """
        forum_id = str(uuid.uuid4())
        
        self.forums[forum_id] = {
            "id": forum_id,
            "name": name,
            "forum_type": forum_type,
            "user_id": self.user_id,
            "description": description or f"Forum: {name}",
            "visibility": visibility,
            "tags": tags or [],
            "attributes": attributes or {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Initialize thread list
        self.forum_threads[forum_id] = []
        
        logger.info(f"Created forum '{name}' with ID {forum_id}")
        return forum_id
        
    def create_thread(self, forum_id: str, title: str, 
                    content: str = None, thread_type: str = "discussion",
                    tags: List[str] = None, attributes: Dict[str, Any] = None) -> str:
        """Create a thread within a forum.
        
        Args:
            forum_id: The ID of the parent forum
            title: The title of the thread
            content: Optional initial content/description
            thread_type: Type of thread (discussion, question, announcement, etc.)
            tags: Optional list of tags
            attributes: Optional additional attributes
            
        Returns:
            The ID of the created thread and the ID of its first message
        """
        if forum_id not in self.forums:
            logger.error(f"Forum {forum_id} not found")
            return None
            
        thread_id = str(uuid.uuid4())
        
        self.threads[thread_id] = {
            "id": thread_id,
            "title": title,
            "forum_id": forum_id,
            "user_id": self.user_id,
            "thread_type": thread_type,
            "is_pinned": False,
            "is_locked": False,
            "views": 0,
            "tags": tags or [],
            "attributes": attributes or {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_activity_at": datetime.now()
        }
        
        # Add to parent forum
        self.forum_threads[forum_id].append(thread_id)
        
        # Initialize message list
        self.thread_messages[thread_id] = []
        
        # Create initial message if content is provided
        message_id = None
        if content:
            message_id = self._create_message(thread_id, content, None, attributes)
            
        logger.info(f"Created thread '{title}' in forum '{self.forums[forum_id]['name']}'")
        return thread_id
        
    def _create_message(self, thread_id: str, content: str, parent_message_id: str = None,
                      attributes: Dict[str, Any] = None) -> str:
        """Internal helper to create a message."""
        message_id = str(uuid.uuid4())
        
        self.messages[message_id] = {
            "id": message_id,
            "thread_id": thread_id,
            "parent_message_id": parent_message_id,
            "user_id": self.user_id,
            "content": content,
            "is_edited": False,
            "is_deleted": False,
            "is_accepted_answer": False,
            "attributes": attributes or {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Add to parent thread
        self.thread_messages[thread_id].append(message_id)
        
        # Add to parent message if it exists
        if parent_message_id:
            if parent_message_id not in self.message_child_messages:
                self.message_child_messages[parent_message_id] = []
            self.message_child_messages[parent_message_id].append(message_id)
        
        # Initialize reactions list
        self.message_reactions_map[message_id] = []
        
        # Update thread last activity
        self.threads[thread_id]["last_activity_at"] = datetime.now()
        self.threads[thread_id]["updated_at"] = datetime.now()
        
        return message_id
        
    def add_message(self, thread_id: str, content: str, 
                  parent_message_id: str = None, attributes: Dict[str, Any] = None) -> str:
        """Add a message to a thread.
        
        Args:
            thread_id: The ID of the parent thread
            content: The content of the message
            parent_message_id: Optional ID of the parent message (for replies)
            attributes: Optional additional attributes
            
        Returns:
            The ID of the created message
        """
        if thread_id not in self.threads:
            logger.error(f"Thread {thread_id} not found")
            return None
            
        if parent_message_id and parent_message_id not in self.messages:
            logger.error(f"Parent message {parent_message_id} not found")
            return None
            
        if self.threads[thread_id]["is_locked"]:
            logger.error(f"Cannot add message to locked thread {thread_id}")
            return None
            
        message_id = self._create_message(thread_id, content, parent_message_id, attributes)
        
        logger.info(f"Added message to thread '{self.threads[thread_id]['title']}'")
        return message_id
        
    def add_reaction(self, message_id: str, reaction_type: str, 
                   attributes: Dict[str, Any] = None) -> str:
        """Add a reaction to a message.
        
        Args:
            message_id: The ID of the message
            reaction_type: Type of reaction (like, dislike, heart, etc.)
            attributes: Optional additional attributes
            
        Returns:
            The ID of the created reaction
        """
        if message_id not in self.messages:
            logger.error(f"Message {message_id} not found")
            return None
            
        reaction_id = str(uuid.uuid4())
        
        self.message_reactions[reaction_id] = {
            "id": reaction_id,
            "message_id": message_id,
            "user_id": self.user_id,
            "reaction_type": reaction_type,
            "attributes": attributes or {},
            "created_at": datetime.now()
        }
        
        # Add to parent message
        self.message_reactions_map[message_id].append(reaction_id)
        
        logger.info(f"Added {reaction_type} reaction to message")
        return reaction_id
        
    def edit_message(self, message_id: str, new_content: str) -> bool:
        """Edit a message's content.
        
        Args:
            message_id: The ID of the message
            new_content: The new content for the message
            
        Returns:
            True if successful, False otherwise
        """
        if message_id not in self.messages:
            logger.error(f"Message {message_id} not found")
            return False
            
        message = self.messages[message_id]
        
        if message["is_deleted"]:
            logger.error(f"Cannot edit deleted message {message_id}")
            return False
            
        message["content"] = new_content
        message["is_edited"] = True
        message["updated_at"] = datetime.now()
        
        # Update thread last activity
        thread_id = message["thread_id"]
        self.threads[thread_id]["last_activity_at"] = datetime.now()
        self.threads[thread_id]["updated_at"] = datetime.now()
        
        logger.info(f"Edited message {message_id}")
        return True
        
    def delete_message(self, message_id: str) -> bool:
        """Mark a message as deleted.
        
        Args:
            message_id: The ID of the message
            
        Returns:
            True if successful, False otherwise
        """
        if message_id not in self.messages:
            logger.error(f"Message {message_id} not found")
            return False
            
        message = self.messages[message_id]
        
        message["is_deleted"] = True
        message["updated_at"] = datetime.now()
        
        # Update thread last activity
        thread_id = message["thread_id"]
        self.threads[thread_id]["last_activity_at"] = datetime.now()
        self.threads[thread_id]["updated_at"] = datetime.now()
        
        logger.info(f"Deleted message {message_id}")
        return True
        
    def pin_thread(self, thread_id: str, pinned: bool = True) -> bool:
        """Pin or unpin a thread.
        
        Args:
            thread_id: The ID of the thread
            pinned: Whether to pin (True) or unpin (False)
            
        Returns:
            True if successful, False otherwise
        """
        if thread_id not in self.threads:
            logger.error(f"Thread {thread_id} not found")
            return False
            
        self.threads[thread_id]["is_pinned"] = pinned
        self.threads[thread_id]["updated_at"] = datetime.now()
        
        action = "Pinned" if pinned else "Unpinned"
        logger.info(f"{action} thread '{self.threads[thread_id]['title']}'")
        return True
        
    def lock_thread(self, thread_id: str, locked: bool = True) -> bool:
        """Lock or unlock a thread.
        
        Args:
            thread_id: The ID of the thread
            locked: Whether to lock (True) or unlock (False)
            
        Returns:
            True if successful, False otherwise
        """
        if thread_id not in self.threads:
            logger.error(f"Thread {thread_id} not found")
            return False
            
        self.threads[thread_id]["is_locked"] = locked
        self.threads[thread_id]["updated_at"] = datetime.now()
        
        action = "Locked" if locked else "Unlocked"
        logger.info(f"{action} thread '{self.threads[thread_id]['title']}'")
        return True
        
    def mark_as_answer(self, message_id: str, is_answer: bool = True) -> bool:
        """Mark or unmark a message as an accepted answer.
        
        Args:
            message_id: The ID of the message
            is_answer: Whether to mark as answer (True) or unmark (False)
            
        Returns:
            True if successful, False otherwise
        """
        if message_id not in self.messages:
            logger.error(f"Message {message_id} not found")
            return False
            
        message = self.messages[message_id]
        thread_id = message["thread_id"]
        
        if thread_id not in self.threads:
            logger.error(f"Thread {thread_id} not found")
            return False
            
        if self.threads[thread_id]["thread_type"] != "question":
            logger.error(f"Thread {thread_id} is not a question thread")
            return False
            
        # If marking as answer, unmark any previous answers
        if is_answer:
            for other_message_id in self.thread_messages[thread_id]:
                if other_message_id != message_id:
                    other_message = self.messages[other_message_id]
                    if other_message["is_accepted_answer"]:
                        other_message["is_accepted_answer"] = False
                        other_message["updated_at"] = datetime.now()
        
        message["is_accepted_answer"] = is_answer
        message["updated_at"] = datetime.now()
        
        action = "Marked" if is_answer else "Unmarked"
        logger.info(f"{action} message {message_id} as accepted answer")
        return True
        
    def increment_view_count(self, thread_id: str) -> bool:
        """Increment the view count for a thread.
        
        Args:
            thread_id: The ID of the thread
            
        Returns:
            True if successful, False otherwise
        """
        if thread_id not in self.threads:
            logger.error(f"Thread {thread_id} not found")
            return False
            
        self.threads[thread_id]["views"] += 1
        return True
        
    def get_forum(self, forum_id: str) -> Dict[str, Any]:
        """Get forum details by ID."""
        if forum_id not in self.forums:
            logger.error(f"Forum {forum_id} not found")
            return None
            
        return self.forums[forum_id]
        
    def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get thread details by ID."""
        if thread_id not in self.threads:
            logger.error(f"Thread {thread_id} not found")
            return None
            
        return self.threads[thread_id]
        
    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get message details by ID."""
        if message_id not in self.messages:
            logger.error(f"Message {message_id} not found")
            return None
            
        return self.messages[message_id]
        
    def get_reaction(self, reaction_id: str) -> Dict[str, Any]:
        """Get reaction details by ID."""
        if reaction_id not in self.message_reactions:
            logger.error(f"Reaction {reaction_id} not found")
            return None
            
        return self.message_reactions[reaction_id]
        
    def get_forum_threads(self, forum_id: str, include_pinned_first: bool = True) -> List[Dict[str, Any]]:
        """Get all threads within a forum.
        
        Args:
            forum_id: The ID of the forum
            include_pinned_first: Whether to sort pinned threads first
            
        Returns:
            List of thread objects
        """
        if forum_id not in self.forums:
            logger.error(f"Forum {forum_id} not found")
            return []
            
        thread_ids = self.forum_threads.get(forum_id, [])
        threads = [self.threads[thread_id] for thread_id in thread_ids if thread_id in self.threads]
        
        if include_pinned_first:
            # Sort by pinned status (pinned first) and then by last activity (newest first)
            return sorted(threads, key=lambda t: (not t["is_pinned"], -t["last_activity_at"].timestamp()))
        else:
            # Sort by last activity (newest first)
            return sorted(threads, key=lambda t: -t["last_activity_at"].timestamp())
        
    def get_thread_messages(self, thread_id: str, hierarchical: bool = False) -> List[Dict[str, Any]]:
        """Get all messages within a thread.
        
        Args:
            thread_id: The ID of the thread
            hierarchical: Whether to return messages in a hierarchical structure
            
        Returns:
            List of message objects (flat or hierarchical)
        """
        if thread_id not in self.threads:
            logger.error(f"Thread {thread_id} not found")
            return []
            
        message_ids = self.thread_messages.get(thread_id, [])
        messages = [self.messages[msg_id] for msg_id in message_ids if msg_id in self.messages]
        
        if not hierarchical:
            # Return flat list sorted by creation time
            return sorted(messages, key=lambda m: m["created_at"])
        else:
            # Return hierarchical structure
            root_messages = [m for m in messages if m["parent_message_id"] is None]
            
            # Sort root messages by creation time
            root_messages = sorted(root_messages, key=lambda m: m["created_at"])
            
            # Helper function to build the hierarchy
            def add_children(parent):
                result = dict(parent)  # Create a copy of the parent
                child_ids = self.message_child_messages.get(parent["id"], [])
                children = [self.messages[child_id] for child_id in child_ids if child_id in self.messages]
                # Sort children by creation time
                children = sorted(children, key=lambda m: m["created_at"])
                # Recursively add their children
                result["children"] = [add_children(child) for child in children]
                return result
                
            # Build the full hierarchy
            return [add_children(root) for root in root_messages]
        
    def get_message_reactions(self, message_id: str) -> Dict[str, int]:
        """Get a summary of reactions for a message.
        
        Args:
            message_id: The ID of the message
            
        Returns:
            Dictionary mapping reaction types to counts
        """
        if message_id not in self.messages:
            logger.error(f"Message {message_id} not found")
            return {}
            
        reaction_ids = self.message_reactions_map.get(message_id, [])
        reactions = [self.message_reactions[r_id] for r_id in reaction_ids if r_id in self.message_reactions]
        
        # Count reactions by type
        counts = {}
        for reaction in reactions:
            r_type = reaction["reaction_type"]
            counts[r_type] = counts.get(r_type, 0) + 1
            
        return counts
        
    def get_topics_state(self) -> Dict[str, Any]:
        """Get a summary of the topics system state."""
        return {
            "forum_count": len(self.forums),
            "thread_count": len(self.threads),
            "message_count": len(self.messages),
            "reaction_count": len(self.message_reactions),
            "active_threads": sum(1 for t in self.threads.values() 
                                 if (datetime.now() - t["last_activity_at"]).days < 30),
            "pinned_threads": sum(1 for t in self.threads.values() if t["is_pinned"]),
            "locked_threads": sum(1 for t in self.threads.values() if t["is_locked"]),
            "updated_at": datetime.now()
        }
        
    # Search and filter functions
    
    def search_threads(self, query: str) -> List[Dict[str, Any]]:
        """Search for threads by title or content."""
        query = query.lower()
        results = []
        
        for thread in self.threads.values():
            # Check if query matches thread title
            if query in thread["title"].lower():
                results.append(thread)
                continue
                
            # Check if query matches any message in the thread
            thread_id = thread["id"]
            message_ids = self.thread_messages.get(thread_id, [])
            for msg_id in message_ids:
                if msg_id in self.messages:
                    message = self.messages[msg_id]
                    if not message["is_deleted"] and query in message["content"].lower():
                        results.append(thread)
                        break
                        
        return results
        
    def find_threads_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Find threads with a specific tag."""
        tag = tag.lower()
        return [t for t in self.threads.values() if tag in [t.lower() for t in t["tags"]]]
        
    def find_threads_by_type(self, thread_type: str) -> List[Dict[str, Any]]:
        """Find threads of a specific type."""
        return [t for t in self.threads.values() if t["thread_type"] == thread_type]
        
    def get_most_active_threads(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most active threads within a time period.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of threads to return
            
        Returns:
            List of thread objects sorted by activity
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_threads = [t for t in self.threads.values() if t["last_activity_at"] >= cutoff_date]
        
        # Sort by activity (most active first)
        sorted_threads = sorted(recent_threads, key=lambda t: -t["last_activity_at"].timestamp())
        return sorted_threads[:limit]


# Create singleton instance
_topics_instance = UserTopics()

def get_topics() -> UserTopics:
    """Get the Topics instance."""
    return _topics_instance