
# Building Custom Echo Components

## Overview

This tutorial guides you through creating custom components for the Deep Tree Echo ecosystem. You'll learn how to build cognitive modules, memory components, and integration adapters that seamlessly work with the existing architecture.

## Prerequisites

- Basic understanding of Python and object-oriented programming
- Familiarity with the AAR (Agent-Arena-Relation) system
- Development environment set up (see [Development Environment Guide](../../guides/dev/development-environment.md))

## Tutorial 1: Creating a Custom Cognitive Module

### Step 1: Define the Module Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from aphrodite.aar_core.memory import MemoryManager
from aphrodite.common.logger import get_logger

class CustomCognitiveModule(ABC):
    """Base class for custom cognitive modules"""
    
    def __init__(self, module_id: str, config: Dict[str, Any]):
        self.module_id = module_id
        self.config = config
        self.logger = get_logger(f"cognitive.{module_id}")
        self.memory_manager = MemoryManager()
        self.state = {}
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process cognitive input and return results"""
        pass
        
    @abstractmethod
    async def learn(self, feedback: Dict[str, Any]) -> None:
        """Update module based on feedback"""
        pass
        
    async def initialize(self) -> None:
        """Initialize the module"""
        self.logger.info(f"Initializing cognitive module: {self.module_id}")
        
    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.logger.info(f"Cleaning up cognitive module: {self.module_id}")
```

### Step 2: Implement a Sentiment Analysis Module

```python
import asyncio
from typing import List
import re

class SentimentAnalysisModule(CustomCognitiveModule):
    """Custom sentiment analysis cognitive module"""
    
    def __init__(self, module_id: str = "sentiment_analyzer", config: Dict[str, Any] = None):
        super().__init__(module_id, config or {})
        self.positive_words = set()
        self.negative_words = set()
        self.sentiment_history = []
        
    async def initialize(self) -> None:
        await super().initialize()
        
        # Load sentiment lexicons
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful',
            'fantastic', 'awesome', 'brilliant', 'outstanding', 'superb'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'disgusting',
            'disappointing', 'frustrating', 'annoying', 'pathetic', 'useless'
        }
        
        self.logger.info(f"Loaded {len(self.positive_words)} positive and {len(self.negative_words)} negative words")
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of input text"""
        text = input_data.get("text", "")
        if not text:
            return {"error": "No text provided for sentiment analysis"}
            
        # Tokenize and clean text
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Count sentiment words
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        # Calculate sentiment score
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            sentiment_score = 0.0
            sentiment_label = "neutral"
        else:
            sentiment_score = (positive_count - negative_count) / len(words)
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
        
        # Store in memory
        memory_record = {
            "text": text,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "positive_words_found": positive_count,
            "negative_words_found": negative_count,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.memory_manager.store_memory(
            f"sentiment_{self.module_id}_{len(self.sentiment_history)}",
            memory_record
        )
        
        self.sentiment_history.append(memory_record)
        
        # Return results
        result = {
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "confidence": min(total_sentiment_words / 10.0, 1.0),  # Confidence based on sentiment word density
            "details": {
                "positive_words": positive_count,
                "negative_words": negative_count,
                "total_words": len(words)
            }
        }
        
        self.logger.debug(f"Analyzed sentiment: {sentiment_label} (score: {sentiment_score:.3f})")
        return result
        
    async def learn(self, feedback: Dict[str, Any]) -> None:
        """Learn from feedback to improve sentiment analysis"""
        correct_sentiment = feedback.get("correct_sentiment")
        text = feedback.get("text")
        
        if not correct_sentiment or not text:
            return
            
        # Simple learning: extract words from incorrectly classified text
        words = re.findall(r'\b\w+\b', text.lower())
        
        if correct_sentiment == "positive":
            # Add words to positive lexicon
            for word in words:
                if word not in self.negative_words and len(word) > 3:
                    self.positive_words.add(word)
        elif correct_sentiment == "negative":
            # Add words to negative lexicon
            for word in words:
                if word not in self.positive_words and len(word) > 3:
                    self.negative_words.add(word)
                    
        self.logger.info(f"Updated lexicon based on feedback for: {correct_sentiment}")
        
    async def get_sentiment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sentiment analysis history"""
        return self.sentiment_history[-limit:]
```

### Step 3: Register and Use the Module

```python
from aphrodite.aar_core.gateway import AARGateway
from aphrodite.engine.deep_tree_config import DeepTreeConfig

async def demo_custom_module():
    """Demonstrate custom cognitive module usage"""
    
    # Initialize the Echo system
    config = DeepTreeConfig(debug=True)
    gateway = AARGateway(config)
    await gateway.initialize()
    
    # Create and initialize custom module
    sentiment_module = SentimentAnalysisModule()
    await sentiment_module.initialize()
    
    # Register module with the gateway
    gateway.register_cognitive_module("sentiment", sentiment_module)
    
    # Test the module
    test_texts = [
        "This is an amazing product! I love it.",
        "This is terrible. I hate everything about it.",
        "It's okay, nothing special but not bad either."
    ]
    
    for text in test_texts:
        result = await sentiment_module.process({"text": text})
        print(f"Text: {text}")
        print(f"Sentiment: {result['sentiment_label']} (score: {result['sentiment_score']:.3f})")
        print(f"Confidence: {result['confidence']:.3f}")
        print("---")
    
    # Demonstrate learning
    feedback = {
        "text": "It's okay, nothing special but not bad either.",
        "correct_sentiment": "positive"  # Provide correction
    }
    await sentiment_module.learn(feedback)
    
    # Test again with learning applied
    result = await sentiment_module.process({"text": "It's okay, nothing special but not bad either."})
    print("After learning:")
    print(f"Sentiment: {result['sentiment_label']} (score: {result['sentiment_score']:.3f})")

# Run the demo
if __name__ == "__main__":
    asyncio.run(demo_custom_module())
```

## Tutorial 2: Creating a Custom Memory Component

### Step 1: Define Memory Component Interface

```python
from aphrodite.aar_core.memory import MemoryType, BaseMemoryComponent

class CustomMemoryComponent(BaseMemoryComponent):
    """Custom memory component for specialized storage"""
    
    def __init__(self, component_id: str, config: Dict[str, Any]):
        super().__init__(component_id, config)
        self.storage = {}
        self.access_patterns = {}
        
    async def store(self, key: str, data: Dict[str, Any], memory_type: MemoryType) -> bool:
        """Store data with custom indexing"""
        try:
            # Add metadata
            enriched_data = {
                **data,
                "memory_type": memory_type.value,
                "stored_at": asyncio.get_event_loop().time(),
                "access_count": 0,
                "component_id": self.component_id
            }
            
            self.storage[key] = enriched_data
            self.access_patterns[key] = {"stores": 1, "retrievals": 0}
            
            self.logger.debug(f"Stored memory: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store memory {key}: {e}")
            return False
            
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data with access tracking"""
        if key not in self.storage:
            return None
            
        # Update access patterns
        self.storage[key]["access_count"] += 1
        self.access_patterns[key]["retrievals"] += 1
        
        self.logger.debug(f"Retrieved memory: {key}")
        return self.storage[key]
        
    async def search(self, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories with custom logic"""
        results = []
        
        for key, data in self.storage.items():
            if self._matches_query(data, query):
                results.append({
                    "key": key,
                    "data": data,
                    "relevance": self._calculate_relevance(data, query)
                })
                
        # Sort by relevance and limit
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]
        
    def _matches_query(self, data: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if data matches query criteria"""
        for key, value in query.items():
            if key not in data:
                continue
            if isinstance(value, str) and value.lower() in str(data[key]).lower():
                return True
            elif data[key] == value:
                return True
        return False
        
    def _calculate_relevance(self, data: Dict[str, Any], query: Dict[str, Any]) -> float:
        """Calculate relevance score"""
        score = 0.0
        
        # Base relevance on access patterns
        access_count = data.get("access_count", 0)
        score += min(access_count / 10.0, 0.5)
        
        # Add recency bonus
        stored_at = data.get("stored_at", 0)
        current_time = asyncio.get_event_loop().time()
        age = current_time - stored_at
        recency_score = max(0, 1.0 - (age / 3600))  # Decay over 1 hour
        score += recency_score * 0.3
        
        # Add query match score
        matches = sum(1 for key in query.keys() if key in data)
        if query:
            score += (matches / len(query)) * 0.2
            
        return score
```

### Step 2: Implement Episodic Memory Component

```python
class EpisodicMemoryComponent(CustomMemoryComponent):
    """Specialized component for episodic memories"""
    
    def __init__(self, component_id: str = "episodic_memory", config: Dict[str, Any] = None):
        super().__init__(component_id, config or {})
        self.episodes = {}
        self.temporal_index = {}
        
    async def store_episode(self, episode_id: str, events: List[Dict[str, Any]], 
                          context: Dict[str, Any] = None) -> bool:
        """Store an episodic memory"""
        episode_data = {
            "episode_id": episode_id,
            "events": events,
            "context": context or {},
            "duration": self._calculate_duration(events),
            "importance": self._calculate_importance(events, context),
            "participants": self._extract_participants(events),
            "summary": self._generate_summary(events)
        }
        
        # Store in both main storage and episode-specific storage
        await self.store(episode_id, episode_data, MemoryType.EPISODIC)
        self.episodes[episode_id] = episode_data
        
        # Update temporal index
        timestamp = episode_data.get("context", {}).get("timestamp", asyncio.get_event_loop().time())
        if timestamp not in self.temporal_index:
            self.temporal_index[timestamp] = []
        self.temporal_index[timestamp].append(episode_id)
        
        return True
        
    async def recall_episode(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """Recall a specific episode"""
        return await self.retrieve(episode_id)
        
    async def find_similar_episodes(self, events: List[Dict[str, Any]], 
                                  limit: int = 5) -> List[Dict[str, Any]]:
        """Find episodes similar to given events"""
        query_features = self._extract_features(events)
        
        similar_episodes = []
        for episode_id, episode_data in self.episodes.items():
            episode_features = self._extract_features(episode_data["events"])
            similarity = self._calculate_similarity(query_features, episode_features)
            
            if similarity > 0.1:  # Threshold for similarity
                similar_episodes.append({
                    "episode_id": episode_id,
                    "episode_data": episode_data,
                    "similarity": similarity
                })
                
        similar_episodes.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_episodes[:limit]
        
    def _calculate_duration(self, events: List[Dict[str, Any]]) -> float:
        """Calculate episode duration"""
        if len(events) < 2:
            return 0.0
            
        timestamps = [event.get("timestamp", 0) for event in events if "timestamp" in event]
        if not timestamps:
            return 0.0
            
        return max(timestamps) - min(timestamps)
        
    def _calculate_importance(self, events: List[Dict[str, Any]], context: Dict[str, Any]) -> float:
        """Calculate episode importance"""
        importance = 0.0
        
        # Based on number of events
        importance += min(len(events) / 10.0, 0.3)
        
        # Based on emotional content
        emotional_events = sum(1 for event in events if event.get("emotion"))
        importance += min(emotional_events / len(events), 0.3) if events else 0
        
        # Based on context significance
        if context and context.get("significant", False):
            importance += 0.4
            
        return importance
        
    def _extract_participants(self, events: List[Dict[str, Any]]) -> List[str]:
        """Extract participants from events"""
        participants = set()
        for event in events:
            if "actor" in event:
                participants.add(event["actor"])
            if "participants" in event:
                participants.update(event["participants"])
        return list(participants)
        
    def _generate_summary(self, events: List[Dict[str, Any]]) -> str:
        """Generate a summary of the episode"""
        if not events:
            return "Empty episode"
            
        # Simple summary based on event types and actors
        event_types = [event.get("type", "unknown") for event in events]
        actors = [event.get("actor", "unknown") for event in events]
        
        return f"Episode with {len(events)} events: {', '.join(set(event_types[:3]))} involving {', '.join(set(actors[:3]))}"
        
    def _extract_features(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features for similarity comparison"""
        features = {
            "event_types": [event.get("type") for event in events],
            "actors": [event.get("actor") for event in events],
            "objects": [event.get("object") for event in events],
            "locations": [event.get("location") for event in events],
            "emotions": [event.get("emotion") for event in events if event.get("emotion")]
        }
        
        # Count occurrences
        for key, values in features.items():
            features[key] = {value: values.count(value) for value in set(values) if value}
            
        return features
        
    def _calculate_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate similarity between feature sets"""
        similarity = 0.0
        total_weight = 0.0
        
        weights = {
            "event_types": 0.3,
            "actors": 0.25,
            "objects": 0.2,
            "locations": 0.15,
            "emotions": 0.1
        }
        
        for feature_type, weight in weights.items():
            if feature_type in features1 and feature_type in features2:
                set1 = set(features1[feature_type].keys())
                set2 = set(features2[feature_type].keys())
                
                if set1 or set2:
                    intersection = len(set1.intersection(set2))
                    union = len(set1.union(set2))
                    jaccard = intersection / union if union > 0 else 0
                    similarity += jaccard * weight
                    
                total_weight += weight
                
        return similarity / total_weight if total_weight > 0 else 0.0
```

### Step 3: Demo Usage

```python
async def demo_episodic_memory():
    """Demonstrate episodic memory component"""
    
    # Create episodic memory component
    episodic_memory = EpisodicMemoryComponent()
    
    # Store some episodes
    episode1_events = [
        {"type": "conversation", "actor": "user", "content": "Hello, how are you?", "timestamp": 1000},
        {"type": "response", "actor": "assistant", "content": "I'm doing well, thank you!", "timestamp": 1005},
        {"type": "conversation", "actor": "user", "content": "What's the weather like?", "timestamp": 1010}
    ]
    
    episode2_events = [
        {"type": "conversation", "actor": "user", "content": "Can you help me with math?", "timestamp": 2000},
        {"type": "response", "actor": "assistant", "content": "Of course! What do you need help with?", "timestamp": 2005},
        {"type": "conversation", "actor": "user", "content": "I need to solve 2x + 5 = 15", "timestamp": 2010}
    ]
    
    # Store episodes
    await episodic_memory.store_episode("greeting_conversation", episode1_events, 
                                       {"context": "casual_chat", "significant": False})
    await episodic_memory.store_episode("math_help", episode2_events, 
                                       {"context": "educational", "significant": True})
    
    # Recall an episode
    recalled = await episodic_memory.recall_episode("greeting_conversation")
    print("Recalled episode:")
    print(f"Summary: {recalled['summary']}")
    print(f"Duration: {recalled['duration']} seconds")
    print(f"Importance: {recalled['importance']:.2f}")
    
    # Find similar episodes
    query_events = [
        {"type": "conversation", "actor": "user", "content": "Hi there!"},
        {"type": "response", "actor": "assistant", "content": "Hello!"}
    ]
    
    similar = await episodic_memory.find_similar_episodes(query_events)
    print("\nSimilar episodes:")
    for episode in similar:
        print(f"- {episode['episode_id']}: similarity {episode['similarity']:.2f}")

if __name__ == "__main__":
    asyncio.run(demo_episodic_memory())
```

## Tutorial 3: Creating Integration Adapters

### Step 1: Database Integration Adapter

```python
from aphrodite.aar_core.gateway import IntegrationAdapter
import aiosqlite
from typing import AsyncGenerator

class DatabaseIntegrationAdapter(IntegrationAdapter):
    """Adapter for database integration with Echo system"""
    
    def __init__(self, db_path: str = "echo_data.db"):
        super().__init__("database_adapter")
        self.db_path = db_path
        self.connection = None
        
    async def initialize(self) -> None:
        """Initialize database connection"""
        self.connection = await aiosqlite.connect(self.db_path)
        
        # Create tables
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_input TEXT,
                assistant_response TEXT,
                timestamp REAL,
                sentiment_score REAL,
                context TEXT
            )
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS memory_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT UNIQUE,
                memory_type TEXT,
                content TEXT,
                importance REAL,
                timestamp REAL,
                access_count INTEGER DEFAULT 0
            )
        """)
        
        await self.connection.commit()
        self.logger.info("Database adapter initialized")
        
    async def store_conversation(self, session_id: str, user_input: str, 
                               assistant_response: str, metadata: Dict[str, Any] = None) -> None:
        """Store conversation in database"""
        metadata = metadata or {}
        
        await self.connection.execute("""
            INSERT INTO conversations 
            (session_id, user_input, assistant_response, timestamp, sentiment_score, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            user_input,
            assistant_response,
            asyncio.get_event_loop().time(),
            metadata.get("sentiment_score", 0.0),
            str(metadata.get("context", {}))
        ))
        
        await self.connection.commit()
        
    async def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve conversation history"""
        cursor = await self.connection.execute("""
            SELECT user_input, assistant_response, timestamp, sentiment_score, context
            FROM conversations 
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (session_id, limit))
        
        rows = await cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "user_input": row[0],
                "assistant_response": row[1],
                "timestamp": row[2],
                "sentiment_score": row[3],
                "context": row[4]
            })
            
        return list(reversed(history))  # Return in chronological order
        
    async def store_memory_record(self, memory_id: str, memory_type: str, 
                                content: Dict[str, Any], importance: float) -> None:
        """Store memory record in database"""
        await self.connection.execute("""
            INSERT OR REPLACE INTO memory_records 
            (memory_id, memory_type, content, importance, timestamp, access_count)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT access_count FROM memory_records WHERE memory_id = ?), 0))
        """, (memory_id, memory_type, str(content), importance, asyncio.get_event_loop().time(), memory_id))
        
        await self.connection.commit()
        
    async def search_memories(self, query: str, memory_type: str = None, 
                            limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory records"""
        base_query = """
            SELECT memory_id, memory_type, content, importance, timestamp, access_count
            FROM memory_records
            WHERE content LIKE ?
        """
        
        params = [f"%{query}%"]
        
        if memory_type:
            base_query += " AND memory_type = ?"
            params.append(memory_type)
            
        base_query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = await self.connection.execute(base_query, params)
        rows = await cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "memory_id": row[0],
                "memory_type": row[1],
                "content": row[2],
                "importance": row[3],
                "timestamp": row[4],
                "access_count": row[5]
            })
            
        return results
        
    async def cleanup(self) -> None:
        """Cleanup database connection"""
        if self.connection:
            await self.connection.close()
            self.logger.info("Database adapter cleaned up")
```

### Step 4: Complete Integration Example

```python
async def complete_integration_demo():
    """Demonstrate complete custom component integration"""
    
    # Initialize components
    sentiment_module = SentimentAnalysisModule()
    episodic_memory = EpisodicMemoryComponent()
    db_adapter = DatabaseIntegrationAdapter()
    
    await sentiment_module.initialize()
    await db_adapter.initialize()
    
    # Create Echo gateway and register components
    config = DeepTreeConfig(debug=True)
    gateway = AARGateway(config)
    await gateway.initialize()
    
    gateway.register_cognitive_module("sentiment", sentiment_module)
    gateway.register_memory_component("episodic", episodic_memory)
    gateway.register_integration_adapter("database", db_adapter)
    
    # Simulate a conversation
    session_id = "demo_session_001"
    conversations = [
        {"user": "Hello! How are you today?", "expected_sentiment": "positive"},
        {"user": "I'm feeling a bit frustrated with my work.", "expected_sentiment": "negative"},
        {"user": "Thanks for listening. You're very helpful!", "expected_sentiment": "positive"}
    ]
    
    for i, conv in enumerate(conversations):
        user_input = conv["user"]
        
        # Process with sentiment analysis
        sentiment_result = await sentiment_module.process({"text": user_input})
        
        # Generate response (simplified)
        assistant_response = f"I understand you're feeling {sentiment_result['sentiment_label']}. How can I help?"
        
        # Store in database
        await db_adapter.store_conversation(
            session_id, 
            user_input, 
            assistant_response,
            {"sentiment_score": sentiment_result["sentiment_score"]}
        )
        
        # Create episode events
        events = [
            {"type": "user_input", "actor": "user", "content": user_input, "timestamp": 1000 + i * 100},
            {"type": "sentiment_analysis", "actor": "system", "result": sentiment_result, "timestamp": 1005 + i * 100},
            {"type": "response", "actor": "assistant", "content": assistant_response, "timestamp": 1010 + i * 100}
        ]
        
        # Store episode
        await episodic_memory.store_episode(
            f"conversation_{session_id}_{i}",
            events,
            {"session_id": session_id, "turn": i}
        )
        
        print(f"Turn {i + 1}:")
        print(f"User: {user_input}")
        print(f"Sentiment: {sentiment_result['sentiment_label']} ({sentiment_result['sentiment_score']:.2f})")
        print(f"Assistant: {assistant_response}")
        print("---")
    
    # Demonstrate retrieval and analysis
    print("\nConversation History:")
    history = await db_adapter.get_conversation_history(session_id)
    for turn in history:
        print(f"User: {turn['user_input']}")
        print(f"Assistant: {turn['assistant_response']}")
        print(f"Sentiment: {turn['sentiment_score']:.2f}")
        print()
    
    # Search for patterns
    print("Searching for positive interactions:")
    positive_memories = await db_adapter.search_memories("positive", limit=5)
    for memory in positive_memories:
        print(f"- {memory['memory_id']}: importance {memory['importance']:.2f}")
    
    # Cleanup
    await db_adapter.cleanup()

if __name__ == "__main__":
    asyncio.run(complete_integration_demo())
```

## Best Practices

### 1. Error Handling
```python
async def safe_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = await self._internal_process(input_data)
        return {"success": True, "result": result}
    except ValidationError as e:
        self.logger.warning(f"Validation error: {e}")
        return {"success": False, "error": "invalid_input", "message": str(e)}
    except Exception as e:
        self.logger.error(f"Processing error: {e}")
        return {"success": False, "error": "processing_failed", "message": "Internal processing error"}
```

### 2. Configuration Management
```python
from pydantic import BaseModel, Field

class CustomModuleConfig(BaseModel):
    module_id: str = Field(default="custom_module")
    debug_mode: bool = Field(default=False)
    processing_timeout: float = Field(default=30.0)
    max_memory_items: int = Field(default=1000)
    
    class Config:
        env_prefix = "ECHO_CUSTOM_"
```

### 3. Testing
```python
import pytest

class TestSentimentModule:
    @pytest.fixture
    async def module(self):
        module = SentimentAnalysisModule()
        await module.initialize()
        return module
    
    @pytest.mark.asyncio
    async def test_positive_sentiment(self, module):
        result = await module.process({"text": "This is amazing!"})
        assert result["sentiment_label"] == "positive"
        assert result["sentiment_score"] > 0
    
    @pytest.mark.asyncio
    async def test_learning(self, module):
        # Test that module can learn from feedback
        await module.learn({
            "text": "okay product",
            "correct_sentiment": "positive"
        })
        # Verify learning occurred (implementation-specific)
```

### 4. Performance Monitoring
```python
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def performance_monitor(operation_name: str):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"{operation_name} completed in {duration:.3f}s")
        
        # Store performance metrics
        await store_metric(operation_name, duration)
```

## Conclusion

This tutorial covered the essential patterns for building custom Echo components:

1. **Cognitive Modules**: For processing and analyzing information
2. **Memory Components**: For specialized storage and retrieval
3. **Integration Adapters**: For connecting external systems

Key takeaways:
- Follow the abstract interfaces for consistency
- Implement proper error handling and logging
- Use configuration management for flexibility
- Write comprehensive tests
- Monitor performance and resource usage

Your custom components should integrate seamlessly with the existing Echo ecosystem while providing specialized functionality for your specific use cases.
