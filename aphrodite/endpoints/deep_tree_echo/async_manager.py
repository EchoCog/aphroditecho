"""
Async resource management for Deep Tree Echo server-side processing.

Provides connection pooling, resource management, and concurrency control
for efficient async server-side request handling with 10x enhanced capacity.
"""

import asyncio
import logging
import time
import weakref
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoolConfig:
    """Configuration for async connection pooling."""
    
    max_connections: int = 100  # Optimized for 37 concurrent streams with overhead
    min_connections: int = 37   # Match target concurrent stream count
    connection_timeout: float = 15.0  # Reduced timeout for faster failover
    idle_timeout: float = 180.0  # Shorter idle timeout for better resource recycling
    max_retries: int = 3
    retry_delay: float = 0.05  # Faster retry for high throughput
    enable_keepalive: bool = True
    keepalive_interval: float = 30.0
    max_concurrent_creates: int = 37  # Match target concurrent stream count


@dataclass 
class ResourcePoolStats:
    """Statistics for resource pool monitoring."""
    
    active_connections: int = 0
    idle_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    pool_utilization: float = 0.0
    last_updated: float = field(default_factory=time.time)


class AsyncConnectionPool:
    """
    Async connection pool for efficient resource management.
    
    Manages connections for DTESN processing requests with proper
    lifecycle management and resource limiting.
    """
    
    def __init__(self, config: Optional[ConnectionPoolConfig] = None):
        """Initialize async connection pool with enhanced capacity."""
        self.config = config or ConnectionPoolConfig()
        self._active_connections: Set[str] = set()
        self._idle_connections: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_connections)
        self._connection_semaphore = asyncio.Semaphore(self.config.max_connections)
        self._create_semaphore = asyncio.Semaphore(self.config.max_concurrent_creates)
        self._stats = ResourcePoolStats()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._lock = asyncio.RLock()  # Use RLock for better concurrent performance
        self._connection_health: Dict[str, float] = {}  # Track connection health
        self._pending_creates = 0
        
    async def start(self):
        """Start the connection pool and cleanup task."""
        logger.info(f"Starting enhanced async connection pool with {self.config.max_connections} max connections")
        
        # Pre-populate with minimum connections in batches for efficiency
        create_tasks = []
        batch_size = min(10, self.config.min_connections)
        for i in range(0, self.config.min_connections, batch_size):
            batch_end = min(i + batch_size, self.config.min_connections)
            batch_tasks = [self._create_connection_safe() for _ in range(i, batch_end)]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, str):  # Successful connection ID
                    await self._idle_connections.put((result, time.time()))
                elif isinstance(result, Exception):
                    logger.warning(f"Failed to create initial connection: {result}")
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_idle_connections())
        if self.config.enable_keepalive:
            self._keepalive_task = asyncio.create_task(self._keepalive_connections())
        
    async def stop(self):
        """Stop the connection pool and cleanup resources."""
        logger.info("Stopping enhanced async connection pool")
        
        # Cancel background tasks
        for task in [self._cleanup_task, self._keepalive_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Clean up all connections concurrently for faster shutdown
        cleanup_tasks = []
        while not self._idle_connections.empty():
            try:
                connection_id, _ = self._idle_connections.get_nowait()
                cleanup_tasks.append(self._close_connection(connection_id))
            except asyncio.QueueEmpty:
                break
        
        # Wait for all connections to close
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[str, None]:
        """
        Get a connection from the pool with proper resource management.
        
        Returns:
            Connection context manager for safe resource handling
        """
        async with self._connection_semaphore:
            self._stats.total_requests += 1
            start_time = time.time()
            
            try:
                # Try to get idle connection first
                connection_id = await self._get_idle_connection()
                if connection_id is None:
                    # Create new connection if needed
                    connection_id = await self._create_connection()
                
                async with self._lock:
                    self._active_connections.add(connection_id)
                    self._stats.active_connections = len(self._active_connections)
                
                try:
                    yield connection_id
                finally:
                    # Return connection to idle pool
                    await self._return_connection(connection_id)
                    
                    # Update stats
                    response_time = time.time() - start_time
                    self._update_response_time(response_time)
                    
            except Exception as e:
                self._stats.failed_requests += 1
                logger.error(f"Connection pool error: {e}")
                raise
    
    async def _get_idle_connection(self) -> Optional[str]:
        """Get connection from idle pool."""
        try:
            connection_id, created_time = await asyncio.wait_for(
                self._idle_connections.get(),
                timeout=0.1  # Quick timeout for non-blocking behavior
            )
            
            # Check if connection is still valid
            if time.time() - created_time < self.config.idle_timeout:
                return connection_id
            else:
                # Connection too old, close it
                await self._close_connection(connection_id)
                return None
                
        except asyncio.TimeoutError:
            return None
    
    async def _create_connection_safe(self) -> str:
        """Create a new connection with proper semaphore control."""
        async with self._create_semaphore:
            self._pending_creates += 1
            try:
                return await self._create_connection()
            finally:
                self._pending_creates -= 1
    
    async def _create_connection(self) -> str:
        """Create a new connection."""
        connection_id = f"dtesn_conn_{int(time.time() * 1000000)}"
        
        # Track connection health for keepalive monitoring
        self._connection_health[connection_id] = time.time()
        
        logger.debug(f"Created new connection: {connection_id}")
        return connection_id
    
    async def _close_connection(self, connection_id: str):
        """Close a connection and clean up resources."""
        # Remove from health tracking
        if connection_id in self._connection_health:
            del self._connection_health[connection_id]
        
        logger.debug(f"Closing connection: {connection_id}")
        # In real implementation, would close actual connection resources
        
    async def _return_connection(self, connection_id: str):
        """Return connection to idle pool."""
        async with self._lock:
            if connection_id in self._active_connections:
                self._active_connections.remove(connection_id)
                self._stats.active_connections = len(self._active_connections)
        
        try:
            await asyncio.wait_for(
                self._idle_connections.put((connection_id, time.time())),
                timeout=0.1
            )
            async with self._lock:
                self._stats.idle_connections = self._idle_connections.qsize()
        except asyncio.TimeoutError:
            # Pool full, close connection
            await self._close_connection(connection_id)
    
    async def _cleanup_idle_connections(self):
        """Background task to clean up idle connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = time.time()
                connections_to_remove = []
                
                # Check all idle connections
                temp_queue = asyncio.Queue()
                while not self._idle_connections.empty():
                    try:
                        connection_id, created_time = self._idle_connections.get_nowait()
                        if current_time - created_time > self.config.idle_timeout:
                            connections_to_remove.append(connection_id)
                        else:
                            await temp_queue.put((connection_id, created_time))
                    except asyncio.QueueEmpty:
                        break
                
                # Restore valid connections
                while not temp_queue.empty():
                    try:
                        item = temp_queue.get_nowait()
                        await self._idle_connections.put(item)
                    except asyncio.QueueEmpty:
                        break
                
                # Close expired connections
                for connection_id in connections_to_remove:
                    await self._close_connection(connection_id)
                    logger.debug(f"Cleaned up idle connection: {connection_id}")
                
                async with self._lock:
                    self._stats.idle_connections = self._idle_connections.qsize()
                    self._stats.pool_utilization = (
                        len(self._active_connections) / self.config.max_connections
                    )
                    self._stats.last_updated = current_time
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection cleanup error: {e}")
    
    def _update_response_time(self, response_time: float):
        """Update average response time with exponential moving average."""
        alpha = 0.1  # Smoothing factor
        if self._stats.avg_response_time == 0:
            self._stats.avg_response_time = response_time
        else:
            self._stats.avg_response_time = (
                alpha * response_time + (1 - alpha) * self._stats.avg_response_time
            )
    
    async def _keepalive_connections(self):
        """Background task to maintain connection health via keepalive."""
        while True:
            try:
                await asyncio.sleep(self.config.keepalive_interval)
                
                current_time = time.time()
                healthy_connections = []
                stale_connections = []
                
                # Check health of all tracked connections
                for conn_id, last_health in self._connection_health.items():
                    if current_time - last_health > self.config.keepalive_interval * 2:
                        stale_connections.append(conn_id)
                    else:
                        healthy_connections.append(conn_id)
                
                # Update health timestamps for healthy connections
                for conn_id in healthy_connections:
                    self._connection_health[conn_id] = current_time
                
                # Remove stale connections
                for conn_id in stale_connections:
                    if conn_id in self._connection_health:
                        del self._connection_health[conn_id]
                        logger.debug(f"Removed stale connection from health tracking: {conn_id}")
                
                logger.debug(f"Keepalive check: {len(healthy_connections)} healthy, {len(stale_connections)} stale")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Keepalive error: {e}")
    
    def get_stats(self) -> ResourcePoolStats:
        """Get current pool statistics."""
        return self._stats


class ConcurrencyManager:
    """
    Manages concurrent request processing with throttling and resource control.
    
    Provides request rate limiting, concurrent request management, and
    adaptive throttling based on system load.
    """
    
    def __init__(
        self,
        max_concurrent_requests: int = 500,  # Enhanced for 10x capacity
        max_requests_per_second: float = 1000.0,  # 10x higher throughput
        burst_limit: int = 100,  # Larger burst capacity
        adaptive_scaling: bool = True,
        scale_factor: float = 1.2
    ):
        """Initialize enhanced concurrency manager."""
        self.max_concurrent_requests = max_concurrent_requests
        self.max_requests_per_second = max_requests_per_second
        self.burst_limit = burst_limit
        self.adaptive_scaling = adaptive_scaling
        self.scale_factor = scale_factor
        
        self._request_semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._rate_limiter = asyncio.Semaphore(burst_limit)
        self._request_times: List[float] = []
        self._lock = asyncio.RLock()  # Use RLock for better performance
        
        # Enhanced monitoring for adaptive scaling
        self._system_load = 0.0
        self._avg_response_time = 0.0
        self._success_rate = 1.0
        self._scale_history: List[float] = []
        
    @asynccontextmanager
    async def throttle_request(self) -> AsyncGenerator[None, None]:
        """
        Enhanced throttle request processing with adaptive scaling and load balancing.
        
        Returns:
            Context manager for throttled request processing with enhanced capacity
        """
        start_time = time.time()
        
        # Apply adaptive rate limiting based on system load
        await self._apply_adaptive_rate_limit()
        
        # Apply concurrency limiting with potential scaling
        semaphore = self._get_adaptive_semaphore()
        async with semaphore:
            try:
                yield
            finally:
                # Record performance metrics for adaptive scaling
                response_time = time.time() - start_time
                await self._record_performance_metrics(response_time, success=True)
                
                # Clean up rate limiting state
                await self._cleanup_rate_limit()
    
    async def _apply_adaptive_rate_limit(self):
        """Apply adaptive rate limiting based on system load."""
        if self.adaptive_scaling:
            # Adjust rate limit based on system performance
            load_factor = min(1.5, max(0.5, 1.0 - self._system_load))
            adaptive_rate = self.max_requests_per_second * load_factor
        else:
            adaptive_rate = self.max_requests_per_second
        
        await self._apply_rate_limit_with_rate(adaptive_rate)
    
    def _get_adaptive_semaphore(self) -> asyncio.Semaphore:
        """Get semaphore with adaptive capacity based on system load."""
        if not self.adaptive_scaling:
            return self._request_semaphore
        
        # Scale concurrency based on performance metrics
        if self._avg_response_time > 0:
            if self._avg_response_time < 0.1 and self._success_rate > 0.95:
                # System performing well, can handle more load
                scale = min(self.scale_factor, 1.5)
            elif self._avg_response_time > 1.0 or self._success_rate < 0.9:
                # System under stress, reduce load
                scale = max(1.0 / self.scale_factor, 0.7)
            else:
                scale = 1.0
            
            # Apply scaling with bounds checking
            scaled_capacity = int(self.max_concurrent_requests * scale)
            scaled_capacity = max(10, min(scaled_capacity, self.max_concurrent_requests * 2))
            
            # Create new semaphore if capacity changed significantly
            if abs(scaled_capacity - self._request_semaphore._initial_value) > 10:
                current_available = self._request_semaphore._value
                self._request_semaphore = asyncio.Semaphore(scaled_capacity)
                # Adjust available count proportionally
                new_available = int(current_available * scaled_capacity / self.max_concurrent_requests)
                for _ in range(scaled_capacity - new_available):
                    try:
                        self._request_semaphore.acquire_nowait()
                    except ValueError:
                        break
        
        return self._request_semaphore
    
    async def _record_performance_metrics(self, response_time: float, success: bool):
        """Record performance metrics for adaptive scaling."""
        async with self._lock:
            # Update average response time with exponential moving average
            alpha = 0.1
            if self._avg_response_time == 0:
                self._avg_response_time = response_time
            else:
                self._avg_response_time = (
                    alpha * response_time + (1 - alpha) * self._avg_response_time
                )
            
            # Update success rate
            self._success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * self._success_rate
            
            # Calculate system load based on concurrency utilization
            current_load = (
                (self.max_concurrent_requests - self._request_semaphore._value) 
                / self.max_concurrent_requests
            )
            self._system_load = alpha * current_load + (1 - alpha) * self._system_load
    
    async def _apply_rate_limit_with_rate(self, rate_limit: float):
        """Apply rate limiting with specified rate."""
        current_time = time.time()
        
        async with self._lock:
            # Clean old request times (older than 1 second)
            self._request_times = [
                t for t in self._request_times if current_time - t < 1.0
            ]
            
            # Check if we're over the rate limit
            if len(self._request_times) >= rate_limit:
                # Calculate delay needed
                oldest_time = min(self._request_times)
                delay = 1.0 - (current_time - oldest_time)
                if delay > 0:
                    await asyncio.sleep(delay)
            
            # Record this request time
            self._request_times.append(current_time)
    
    async def _apply_rate_limit(self):
        """Apply rate limiting based on requests per second."""
        current_time = time.time()
        
        async with self._lock:
            # Clean old request times (older than 1 second)
            self._request_times = [
                t for t in self._request_times if current_time - t < 1.0
            ]
            
            # Check if we're over the rate limit
            if len(self._request_times) >= self.max_requests_per_second:
                # Calculate delay needed
                oldest_time = min(self._request_times)
                delay = 1.0 - (current_time - oldest_time)
                if delay > 0:
                    await asyncio.sleep(delay)
            
            # Record this request time
            self._request_times.append(current_time)
    
    async def _cleanup_rate_limit(self):
        """Clean up rate limiting state after request completion."""
        current_time = time.time()
        
        # Remove old request timestamps beyond the rate limit window
        async with self._lock:
            # Clean up timestamps older than the rate limiting window
            self._request_times = [
                timestamp for timestamp in self._request_times
                if current_time - timestamp < 60.0
            ]
            
            # Log cleanup statistics for monitoring
            if len(self._request_times) > 0:
                logger.debug(
                    f"Rate limit cleanup: {len(self._request_times)} active timestamps remaining"
                )
    
    def get_current_load(self) -> Dict[str, Any]:
        """Get enhanced concurrency and rate limiting statistics with adaptive metrics."""
        current_time = time.time()
        
        # Count recent requests
        recent_requests = len([
            t for t in self._request_times if current_time - t < 1.0
        ])
        
        # Calculate effective capacity (may be scaled)
        effective_capacity = getattr(self._request_semaphore, '_initial_value', self.max_concurrent_requests)
        
        return {
            "concurrent_requests": effective_capacity - self._request_semaphore._value,
            "recent_requests_per_second": recent_requests,
            "rate_limit_utilization": recent_requests / self.max_requests_per_second,
            "concurrency_utilization": (
                (effective_capacity - self._request_semaphore._value) 
                / effective_capacity
            ),
            "available_slots": self._request_semaphore._value,
            "burst_capacity_remaining": self._rate_limiter._value,
            "adaptive_scaling_enabled": self.adaptive_scaling,
            "system_load": self._system_load,
            "avg_response_time": self._avg_response_time,
            "success_rate": self._success_rate,
            "effective_capacity": effective_capacity,
            "base_capacity": self.max_concurrent_requests
        }


class AsyncRequestQueue:
    """
    Enhanced async request queue with priority handling and load balancing.
    
    Provides non-blocking request queuing with priority levels, circuit breaker
    pattern, and adaptive load balancing based on system performance.
    """
    
    def __init__(
        self,
        max_queue_size: int = 10000,  # 10x larger queue for high throughput
        priority_levels: int = 5,  # More priority levels for better control
        circuit_breaker_threshold: int = 10,  # Higher threshold for enhanced capacity
        circuit_breaker_timeout: float = 30.0,  # Faster recovery
        adaptive_timeout: bool = True,
        batch_processing: bool = True,  # Enable batch processing
        batch_size: int = 10
    ):
        """Initialize enhanced async request queue with 10x capacity."""
        self.max_queue_size = max_queue_size
        self.priority_levels = priority_levels
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.adaptive_timeout = adaptive_timeout
        self.batch_processing = batch_processing
        self.batch_size = batch_size
        
        # Priority queues for different request types
        self._priority_queues = [
            asyncio.Queue(maxsize=max_queue_size // priority_levels)
            for _ in range(priority_levels)
        ]
        
        # Circuit breaker state
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = 0.0
        self._circuit_breaker_open = False
        
        # Performance tracking for adaptive timeouts
        self._response_times = []
        self._success_rate = 1.0
        self._lock = asyncio.RLock()  # Use RLock for better concurrent access
        
        # Batch processing support
        self._batch_queues = [[] for _ in range(priority_levels)]
        self._batch_timers = [None for _ in range(priority_levels)]
        self._batch_locks = [asyncio.Lock() for _ in range(priority_levels)]
        
        logger.info(f"AsyncRequestQueue initialized with {priority_levels} priority levels")
    
    async def enqueue_request(
        self,
        request_data: Any,
        priority: int = 1,
        timeout: Optional[float] = None
    ) -> str:
        """
        Enqueue request with priority and timeout handling.
        
        Args:
            request_data: Request data to process
            priority: Request priority (0=highest, 2=lowest)
            timeout: Optional custom timeout
            
        Returns:
            Request ID for tracking
        """
        # Check circuit breaker
        if self._circuit_breaker_open:
            current_time = time.time()
            if current_time - self._circuit_breaker_last_failure < self.circuit_breaker_timeout:
                raise RuntimeError("Circuit breaker is open - service temporarily unavailable")
            else:
                # Reset circuit breaker
                self._circuit_breaker_open = False
                self._circuit_breaker_failures = 0
                logger.info("Circuit breaker reset - service available")
        
        # Validate priority level
        priority = max(0, min(priority, self.priority_levels - 1))
        
        # Generate request ID
        request_id = f"req_{int(time.time() * 1000000)}_{priority}"
        
        # Calculate adaptive timeout if enabled
        if timeout is None and self.adaptive_timeout:
            timeout = self._calculate_adaptive_timeout()
        
        # Create request with metadata
        request_item = {
            "id": request_id,
            "data": request_data,
            "priority": priority,
            "timeout": timeout,
            "enqueued_at": time.time(),
            "retries": 0
        }
        
        try:
            # Add to appropriate priority queue (non-blocking)
            self._priority_queues[priority].put_nowait(request_item)
            logger.debug(f"Enqueued request {request_id} with priority {priority}")
            return request_id
            
        except asyncio.QueueFull:
            logger.warning(f"Queue full for priority {priority}, rejecting request {request_id}")
            raise RuntimeError(f"Request queue full for priority level {priority}")
    
    async def dequeue_request(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue next request based on priority.
        
        Returns:
            Next request to process or None if no requests available
        """
        # Try queues in priority order (0=highest priority)
        for priority in range(self.priority_levels):
            try:
                # Non-blocking get
                request_item = self._priority_queues[priority].get_nowait()
                logger.debug(f"Dequeued request {request_item['id']} with priority {priority}")
                return request_item
            except asyncio.QueueEmpty:
                continue
        
        return None
    
    async def record_request_result(
        self,
        request_id: str,
        success: bool,
        response_time: float,
        error: Optional[str] = None
    ):
        """
        Record request completion for performance tracking and circuit breaker.
        
        Args:
            request_id: Request ID
            success: Whether request succeeded
            response_time: Request processing time
            error: Error message if failed
        """
        async with self._lock:
            # Update response time tracking
            self._response_times.append(response_time)
            if len(self._response_times) > 100:
                self._response_times = self._response_times[-100:]  # Keep last 100
            
            # Update success rate
            if success:
                self._success_rate = 0.95 * self._success_rate + 0.05 * 1.0
                # Reset circuit breaker failures on success
                if self._circuit_breaker_failures > 0:
                    self._circuit_breaker_failures = max(0, self._circuit_breaker_failures - 1)
            else:
                self._success_rate = 0.95 * self._success_rate + 0.05 * 0.0
                self._circuit_breaker_failures += 1
                self._circuit_breaker_last_failure = time.time()
                
                # Check if circuit breaker should open
                if self._circuit_breaker_failures >= self.circuit_breaker_threshold:
                    self._circuit_breaker_open = True
                    logger.warning(
                        f"Circuit breaker opened due to {self._circuit_breaker_failures} failures"
                    )
                
                logger.warning(f"Request {request_id} failed: {error}")
    
    def _calculate_adaptive_timeout(self) -> float:
        """Calculate adaptive timeout based on historical response times."""
        if not self._response_times:
            return 30.0  # Default timeout
        
        # Calculate 95th percentile response time
        sorted_times = sorted(self._response_times)
        p95_index = int(0.95 * len(sorted_times))
        p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        
        # Add buffer based on success rate
        buffer_multiplier = 2.0 if self._success_rate < 0.9 else 1.5
        adaptive_timeout = p95_time * buffer_multiplier
        
        # Clamp between reasonable bounds
        return max(5.0, min(adaptive_timeout, 120.0))
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics."""
        total_queued = sum(q.qsize() for q in self._priority_queues)
        queue_sizes = [q.qsize() for q in self._priority_queues]
        
        avg_response_time = (
            sum(self._response_times) / len(self._response_times)
            if self._response_times else 0.0
        )
        
        return {
            "total_queued_requests": total_queued,
            "priority_queue_sizes": queue_sizes,
            "queue_utilization": total_queued / self.max_queue_size,
            "circuit_breaker_open": self._circuit_breaker_open,
            "circuit_breaker_failures": self._circuit_breaker_failures,
            "success_rate": self._success_rate,
            "avg_response_time": avg_response_time,
            "adaptive_timeout": self._calculate_adaptive_timeout(),
            "batch_processing_enabled": self.batch_processing,
            "batch_sizes": [len(batch) for batch in self._batch_queues] if self.batch_processing else []
        }
    
    async def enqueue_batch_request(
        self,
        request_data: Any,
        priority: int = 1,
        timeout: Optional[float] = None
    ) -> str:
        """
        Enqueue request for batch processing to improve throughput.
        
        Args:
            request_data: Request data to process
            priority: Request priority (0=highest)
            timeout: Optional custom timeout
            
        Returns:
            Request ID for tracking
        """
        if not self.batch_processing:
            return await self.enqueue_request(request_data, priority, timeout)
        
        # Validate priority level
        priority = max(0, min(priority, self.priority_levels - 1))
        
        # Generate request ID
        request_id = f"batch_req_{int(time.time() * 1000000)}_{priority}"
        
        # Calculate adaptive timeout if enabled
        if timeout is None and self.adaptive_timeout:
            timeout = self._calculate_adaptive_timeout()
        
        # Create request with metadata
        request_item = {
            "id": request_id,
            "data": request_data,
            "priority": priority,
            "timeout": timeout,
            "enqueued_at": time.time(),
            "batch": True
        }
        
        async with self._batch_locks[priority]:
            self._batch_queues[priority].append(request_item)
            
            # Check if batch is full or timer should be started
            if len(self._batch_queues[priority]) >= self.batch_size:
                await self._flush_batch(priority)
            elif self._batch_timers[priority] is None:
                # Start batch timer for partial batches
                self._batch_timers[priority] = asyncio.create_task(
                    self._batch_timeout(priority, 0.1)  # 100ms batch timeout
                )
        
        logger.debug(f"Enqueued batch request {request_id} with priority {priority}")
        return request_id
    
    async def _flush_batch(self, priority: int):
        """Flush batch queue for given priority level."""
        if not self._batch_queues[priority]:
            return
        
        # Create batch item
        batch_item = {
            "id": f"batch_{int(time.time() * 1000000)}_{priority}",
            "batch_data": self._batch_queues[priority].copy(),
            "priority": priority,
            "batch_size": len(self._batch_queues[priority]),
            "enqueued_at": time.time()
        }
        
        # Clear batch queue
        self._batch_queues[priority].clear()
        
        # Cancel timer if running
        if self._batch_timers[priority]:
            self._batch_timers[priority].cancel()
            self._batch_timers[priority] = None
        
        try:
            # Add batch to priority queue
            self._priority_queues[priority].put_nowait(batch_item)
            logger.debug(f"Flushed batch with {batch_item['batch_size']} requests for priority {priority}")
        except asyncio.QueueFull:
            logger.warning(f"Failed to flush batch for priority {priority}: queue full")
            # Re-add items to batch queue for retry
            self._batch_queues[priority].extend(batch_item["batch_data"])
    
    async def _batch_timeout(self, priority: int, timeout: float):
        """Handle batch timeout to flush partial batches."""
        try:
            await asyncio.sleep(timeout)
            async with self._batch_locks[priority]:
                if self._batch_queues[priority]:
                    await self._flush_batch(priority)
        except asyncio.CancelledError:
            pass
    
    async def dequeue_batch_request(self) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Dequeue next request or batch based on priority.
        
        Returns:
            Next request/batch to process or None if no requests available
        """
        # Try queues in priority order (0=highest priority)
        for priority in range(self.priority_levels):
            try:
                # Non-blocking get
                request_item = self._priority_queues[priority].get_nowait()
                
                # Check if it's a batch
                if "batch_data" in request_item:
                    logger.debug(f"Dequeued batch {request_item['id']} with {request_item['batch_size']} requests")
                    return request_item["batch_data"]
                else:
                    logger.debug(f"Dequeued request {request_item['id']} with priority {priority}")
                    return request_item
            except asyncio.QueueEmpty:
                continue
        
        return None