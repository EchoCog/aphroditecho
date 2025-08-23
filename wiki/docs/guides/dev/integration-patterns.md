
# Integration Patterns & Best Practices

## Overview

This guide outlines proven patterns and best practices for integrating with the Deep Tree Echo ecosystem. These patterns ensure robust, maintainable, and scalable integrations across different system components.

## Core Integration Patterns

### 1. Gateway Pattern

The Gateway pattern provides a unified entry point for external systems to interact with Echo components.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from aphrodite.aar_core.gateway import AARGateway

class IntegrationGateway(ABC):
    """Base class for all integration gateways"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.aar_gateway = AARGateway(config)
        self.active_connections = {}
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the gateway and its connections"""
        pass
    
    @abstractmethod
    async def process_external_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming requests from external systems"""
        pass
    
    async def connect_to_echo_system(self) -> bool:
        """Establish connection to Echo cognitive core"""
        try:
            await self.aar_gateway.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Echo system: {e}")
            return False

class APIIntegrationGateway(IntegrationGateway):
    """Gateway for REST API integrations"""
    
    async def initialize(self):
        await self.connect_to_echo_system()
        self.setup_api_endpoints()
    
    async def process_external_request(self, request):
        # Transform external request to Echo format
        echo_request = self.transform_to_echo_format(request)
        
        # Process through Echo system
        result = await self.aar_gateway.process_cognitive_input(echo_request)
        
        # Transform Echo response to external format
        return self.transform_from_echo_format(result)
    
    def transform_to_echo_format(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform external request format to Echo internal format"""
        return {
            "type": request.get("message_type", "text"),
            "content": request.get("data", ""),
            "context": {
                "external_source": request.get("source", "api"),
                "timestamp": request.get("timestamp"),
                "session_id": request.get("session_id")
            }
        }
    
    def transform_from_echo_format(self, echo_response: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Echo response to external format"""
        return {
            "success": echo_response.get("status") == "success",
            "data": echo_response.get("cognitive_response", {}),
            "metadata": {
                "processing_time": echo_response.get("processing_time"),
                "confidence": echo_response.get("confidence", 0.0)
            }
        }
```

### 2. Event-Driven Integration Pattern

Use events for loose coupling between systems:

```python
from aphrodite.aar_core.events import EventBus, EventHandler
from typing import Callable
import asyncio

class EventDrivenIntegration:
    def __init__(self):
        self.event_bus = EventBus()
        self.external_handlers = {}
        self.echo_handlers = {}
    
    def register_external_handler(self, event_type: str, handler: Callable):
        """Register handler for events from external systems"""
        if event_type not in self.external_handlers:
            self.external_handlers[event_type] = []
        self.external_handlers[event_type].append(handler)
    
    def register_echo_handler(self, event_type: str, handler: Callable):
        """Register handler for events from Echo system"""
        self.event_bus.register(event_type, handler)
    
    async def emit_to_external(self, event_type: str, data: Dict[str, Any]):
        """Emit event to external systems"""
        handlers = self.external_handlers.get(event_type, [])
        tasks = [handler(data) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def emit_to_echo(self, event_type: str, data: Dict[str, Any]):
        """Emit event to Echo system"""
        await self.event_bus.emit(event_type, data)

# Example usage
class WebSocketIntegration(EventDrivenIntegration):
    def __init__(self, websocket_manager):
        super().__init__()
        self.websocket_manager = websocket_manager
        self.setup_integration_handlers()
    
    def setup_integration_handlers(self):
        # Handle Echo system events and forward to WebSocket
        self.register_echo_handler("agent.message", self.forward_agent_message)
        self.register_echo_handler("memory.update", self.forward_memory_update)
        
        # Handle WebSocket events and forward to Echo
        self.register_external_handler("user.message", self.process_user_message)
    
    async def forward_agent_message(self, event_data):
        await self.websocket_manager.broadcast({
            "type": "agent_message",
            "agent_id": event_data.get("agent_id"),
            "message": event_data.get("message")
        })
    
    async def process_user_message(self, message_data):
        await self.emit_to_echo("user.input", {
            "content": message_data.get("message"),
            "user_id": message_data.get("user_id")
        })
```

### 3. Adapter Pattern

Adapt different data formats and protocols:

```python
from abc import ABC, abstractmethod
from typing import Any

class DataAdapter(ABC):
    """Base adapter for data format transformations"""
    
    @abstractmethod
    def to_echo_format(self, external_data: Any) -> Dict[str, Any]:
        """Convert external data to Echo internal format"""
        pass
    
    @abstractmethod
    def from_echo_format(self, echo_data: Dict[str, Any]) -> Any:
        """Convert Echo data to external format"""
        pass

class JSONAdapter(DataAdapter):
    def to_echo_format(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "json_input",
            "content": json_data,
            "metadata": {
                "format": "json",
                "schema_version": "1.0"
            }
        }
    
    def from_echo_format(self, echo_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "result": echo_data.get("cognitive_response", {}),
            "status": echo_data.get("status", "unknown"),
            "timestamp": echo_data.get("timestamp")
        }

class ProtocolBufferAdapter(DataAdapter):
    def __init__(self, proto_class):
        self.proto_class = proto_class
    
    def to_echo_format(self, proto_message) -> Dict[str, Any]:
        # Convert protobuf to dict
        message_dict = MessageToDict(proto_message)
        return {
            "type": "protobuf_input",
            "content": message_dict,
            "metadata": {
                "format": "protobuf",
                "message_type": proto_message.DESCRIPTOR.name
            }
        }
    
    def from_echo_format(self, echo_data: Dict[str, Any]):
        # Convert back to protobuf
        response = self.proto_class()
        ParseDict(echo_data.get("cognitive_response", {}), response)
        return response
```

### 4. Plugin Integration Pattern

Create pluggable integrations:

```python
from aphrodite.plugins.base import BasePlugin
from typing import List, Optional

class IntegrationPlugin(BasePlugin):
    """Base class for integration plugins"""
    
    def __init__(self):
        super().__init__()
        self.integrations: List[IntegrationGateway] = []
        self.adapters: Dict[str, DataAdapter] = {}
    
    async def initialize(self, config: Dict[str, Any]):
        await super().initialize(config)
        await self.setup_integrations()
    
    @abstractmethod
    async def setup_integrations(self):
        """Setup specific integrations"""
        pass
    
    def register_adapter(self, format_type: str, adapter: DataAdapter):
        self.adapters[format_type] = adapter
    
    def get_adapter(self, format_type: str) -> Optional[DataAdapter]:
        return self.adapters.get(format_type)

class DatabaseIntegrationPlugin(IntegrationPlugin):
    async def setup_integrations(self):
        # Setup database connections
        self.db_gateway = DatabaseGateway(self.config.get("database", {}))
        self.integrations.append(self.db_gateway)
        
        # Register adapters
        self.register_adapter("sql", SQLAdapter())
        self.register_adapter("nosql", NoSQLAdapter())
    
    async def query_database(self, query: str, format_type: str = "sql"):
        adapter = self.get_adapter(format_type)
        if not adapter:
            raise ValueError(f"No adapter found for format: {format_type}")
        
        # Transform query to Echo format
        echo_query = adapter.to_echo_format({"query": query})
        
        # Process through Echo system
        result = await self.aar_gateway.process_cognitive_input(echo_query)
        
        # Transform result back
        return adapter.from_echo_format(result)
```

## Memory Integration Patterns

### Distributed Memory Pattern

```python
from aphrodite.aar_core.memory import MemoryManager, DistributedMemoryCoordinator

class DistributedMemoryIntegration:
    def __init__(self, nodes: List[str]):
        self.coordinator = DistributedMemoryCoordinator(nodes)
        self.local_manager = MemoryManager()
        self.replication_factor = 2
    
    async def store_distributed_memory(self, memory_id: str, memory_data: Dict[str, Any]):
        """Store memory across multiple nodes"""
        # Calculate target nodes
        target_nodes = self.coordinator.select_nodes(memory_id, self.replication_factor)
        
        # Store locally first
        await self.local_manager.store_memory(memory_id, memory_data)
        
        # Replicate to other nodes
        replication_tasks = []
        for node in target_nodes:
            if node != self.coordinator.local_node_id:
                task = self.coordinator.replicate_to_node(node, memory_id, memory_data)
                replication_tasks.append(task)
        
        # Wait for replication
        results = await asyncio.gather(*replication_tasks, return_exceptions=True)
        
        # Handle replication failures
        failures = [r for r in results if isinstance(r, Exception)]
        if failures:
            self.logger.warning(f"Replication failures: {len(failures)}")
        
        return len(results) - len(failures) >= self.replication_factor - 1
    
    async def retrieve_distributed_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve memory with fallback to other nodes"""
        # Try local first
        memory = await self.local_manager.retrieve_memory(memory_id)
        if memory:
            return memory
        
        # Try other nodes
        nodes = self.coordinator.get_nodes_for_memory(memory_id)
        for node in nodes:
            try:
                memory = await self.coordinator.retrieve_from_node(node, memory_id)
                if memory:
                    # Cache locally for future access
                    await self.local_manager.store_memory(memory_id, memory)
                    return memory
            except Exception as e:
                self.logger.warning(f"Failed to retrieve from node {node}: {e}")
        
        return None
```

### Memory Synchronization Pattern

```python
from asyncio import Lock
from datetime import datetime

class MemorySynchronization:
    def __init__(self, memory_managers: List[MemoryManager]):
        self.managers = memory_managers
        self.sync_lock = Lock()
        self.last_sync = {}
    
    async def synchronize_memories(self, sync_policy: str = "merge"):
        """Synchronize memories across all managers"""
        async with self.sync_lock:
            if sync_policy == "merge":
                await self._merge_synchronization()
            elif sync_policy == "latest":
                await self._latest_wins_synchronization()
            elif sync_policy == "conflict_resolution":
                await self._conflict_resolution_synchronization()
    
    async def _merge_synchronization(self):
        """Merge memories from all managers"""
        all_memories = {}
        
        # Collect all memories
        for manager in self.managers:
            memories = await manager.get_all_memories()
            for memory_id, memory_data in memories.items():
                if memory_id not in all_memories:
                    all_memories[memory_id] = []
                all_memories[memory_id].append((manager, memory_data))
        
        # Merge and distribute
        for memory_id, memory_versions in all_memories.items():
            merged_memory = await self._merge_memory_versions(memory_versions)
            
            # Update all managers with merged version
            for manager in self.managers:
                await manager.update_memory(memory_id, merged_memory)
    
    async def _merge_memory_versions(self, versions: List[Tuple[MemoryManager, Dict]]):
        """Merge different versions of the same memory"""
        if len(versions) == 1:
            return versions[0][1]
        
        # Implement merging logic based on importance, recency, etc.
        base_memory = versions[0][1]
        for _, memory in versions[1:]:
            # Merge importance scores
            base_memory["importance"] = max(
                base_memory.get("importance", 0),
                memory.get("importance", 0)
            )
            
            # Merge content (application-specific logic)
            if "content" in memory:
                base_memory["content"] = self._merge_content(
                    base_memory.get("content", {}),
                    memory["content"]
                )
        
        base_memory["last_sync"] = datetime.now().isoformat()
        return base_memory
```

## API Integration Best Practices

### Rate Limiting and Circuit Breaker

```python
import asyncio
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    async def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    async def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self) -> bool:
        now = datetime.now()
        
        # Remove old requests
        cutoff_time = now - timedelta(seconds=self.time_window)
        self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
        
        # Check if we can make a new request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False

class ResilientAPIIntegration:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.get("failure_threshold", 5),
            recovery_timeout=config.get("recovery_timeout", 60)
        )
        self.rate_limiter = RateLimiter(
            max_requests=config.get("max_requests", 100),
            time_window=config.get("time_window", 60)
        )
    
    async def make_api_call(self, endpoint: str, data: Dict[str, Any]):
        # Check rate limit
        if not await self.rate_limiter.acquire():
            raise Exception("Rate limit exceeded")
        
        # Make call through circuit breaker
        return await self.circuit_breaker.call(self._actual_api_call, endpoint, data)
    
    async def _actual_api_call(self, endpoint: str, data: Dict[str, Any]):
        # Implement actual API call logic
        pass
```

### Monitoring and Observability

```python
from dataclasses import dataclass
from typing import Dict, List
import time

@dataclass
class IntegrationMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    response_times: List[float] = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []

class IntegrationMonitor:
    def __init__(self):
        self.metrics: Dict[str, IntegrationMetrics] = {}
        self.alerts = []
    
    def record_request(self, integration_name: str, success: bool, response_time: float):
        if integration_name not in self.metrics:
            self.metrics[integration_name] = IntegrationMetrics()
        
        metrics = self.metrics[integration_name]
        metrics.total_requests += 1
        metrics.response_times.append(response_time)
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Calculate average response time
        metrics.average_response_time = sum(metrics.response_times) / len(metrics.response_times)
        
        # Check for alerts
        self._check_alert_conditions(integration_name, metrics)
    
    def _check_alert_conditions(self, integration_name: str, metrics: IntegrationMetrics):
        # High failure rate
        if metrics.total_requests > 10:
            failure_rate = metrics.failed_requests / metrics.total_requests
            if failure_rate > 0.1:  # 10% failure rate
                self._create_alert(integration_name, "high_failure_rate", failure_rate)
        
        # High response time
        if metrics.average_response_time > 5.0:  # 5 seconds
            self._create_alert(integration_name, "high_response_time", metrics.average_response_time)
    
    def _create_alert(self, integration_name: str, alert_type: str, value: float):
        alert = {
            "integration": integration_name,
            "type": alert_type,
            "value": value,
            "timestamp": time.time()
        }
        self.alerts.append(alert)
        # In production, send to alerting system

# Usage example
monitor = IntegrationMonitor()

async def monitored_integration_call(integration_name: str, func, *args, **kwargs):
    start_time = time.time()
    success = False
    
    try:
        result = await func(*args, **kwargs)
        success = True
        return result
    except Exception as e:
        raise e
    finally:
        response_time = time.time() - start_time
        monitor.record_request(integration_name, success, response_time)
```

## Testing Integration Patterns

### Integration Test Framework

```python
import pytest
from unittest.mock import Mock, AsyncMock
from contextlib import asynccontextmanager

class IntegrationTestFramework:
    def __init__(self):
        self.mock_services = {}
        self.test_data = {}
    
    def mock_external_service(self, service_name: str, responses: Dict[str, Any]):
        """Mock external service responses"""
        mock_service = AsyncMock()
        for method, response in responses.items():
            getattr(mock_service, method).return_value = response
        
        self.mock_services[service_name] = mock_service
        return mock_service
    
    @asynccontextmanager
    async def test_environment(self, config: Dict[str, Any]):
        """Setup test environment with mocked dependencies"""
        # Setup test Echo system
        test_gateway = AARGateway(config)
        await test_gateway.initialize()
        
        try:
            yield test_gateway
        finally:
            await test_gateway.cleanup()

# Example integration test
class TestAPIIntegration:
    @pytest.fixture
    async def test_framework(self):
        framework = IntegrationTestFramework()
        
        # Mock external API
        framework.mock_external_service("external_api", {
            "get_data": {"status": "success", "data": "test_data"},
            "post_data": {"status": "created", "id": "123"}
        })
        
        return framework
    
    @pytest.mark.asyncio
    async def test_api_integration_flow(self, test_framework):
        config = {"test_mode": True}
        
        async with test_framework.test_environment(config) as gateway:
            # Test the integration flow
            integration = APIIntegrationGateway(config)
            await integration.initialize()
            
            # Process test request
            result = await integration.process_external_request({
                "message_type": "test",
                "data": "test input",
                "session_id": "test_session"
            })
            
            assert result["success"] is True
            assert "data" in result
```

These integration patterns provide a solid foundation for building robust integrations with the Deep Tree Echo ecosystem. Choose the appropriate patterns based on your specific integration requirements and system constraints.
