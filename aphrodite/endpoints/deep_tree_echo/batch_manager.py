"""
Dynamic batch management for DTESN operations.

Implements intelligent batch sizing based on server load, request patterns,
and performance metrics to optimize throughput while maintaining responsiveness.
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BatchingMetrics:
    """Metrics for batch processing performance monitoring."""
    
    # Throughput metrics
    requests_processed: int = 0
    total_processing_time_ms: float = 0.0
    avg_batch_size: float = 0.0
    avg_processing_time_ms: float = 0.0
    
    # Load metrics
    server_load_samples: List[float] = field(default_factory=list)
    avg_server_load: float = 0.0
    
    # Efficiency metrics
    batch_utilization: float = 0.0  # Actual batch size / target batch size
    throughput_improvement: float = 0.0  # Compared to baseline
    
    # Timing metrics
    batch_wait_times: List[float] = field(default_factory=list)
    avg_batch_wait_time: float = 0.0
    
    last_updated: float = field(default_factory=time.time)


@dataclass
class BatchConfiguration:
    """Configuration for dynamic batch processing."""
    
    # Base batch sizing - optimized for 37 concurrent streams
    min_batch_size: int = 1
    max_batch_size: int = 37
    target_batch_size: int = 12
    
    # Load-aware adjustments
    low_load_threshold: float = 0.3
    high_load_threshold: float = 0.8
    load_adjustment_factor: float = 0.2
    
    # Timing constraints
    max_batch_wait_ms: float = 50.0  # Maximum time to wait for batch filling
    min_batch_wait_ms: float = 5.0   # Minimum time to wait
    
    # Adaptive parameters
    enable_adaptive_sizing: bool = True
    performance_window_size: int = 100  # Number of batches to track
    adaptation_rate: float = 0.1  # How quickly to adapt to changes
    
    # Circuit breaker
    enable_circuit_breaker: bool = True
    failure_threshold: int = 5
    circuit_breaker_timeout: float = 30.0


class DynamicBatchManager:
    """
    Manages dynamic batching for DTESN operations with load-aware sizing.
    
    Implements intelligent batch aggregation that adapts to server load,
    request patterns, and performance metrics to maximize throughput
    while maintaining responsiveness.
    """
    
    def __init__(
        self,
        config: Optional[BatchConfiguration] = None,
        load_tracker: Optional[Callable[[], float]] = None
    ):
        """Initialize dynamic batch manager."""
        self.config = config or BatchConfiguration()
        self.load_tracker = load_tracker
        
        # Batch state
        self._pending_requests: List[Dict[str, Any]] = []
        self._batch_lock = asyncio.Lock()
        self._batch_event = asyncio.Event()
        self._processing = False
        
        # Performance tracking
        self._metrics = BatchingMetrics()
        self._performance_history = deque(maxlen=self.config.performance_window_size)
        self._baseline_throughput: Optional[float] = None
        
        # Adaptive sizing state
        self._current_batch_size = self.config.target_batch_size
        self._load_samples = deque(maxlen=50)  # Keep recent load samples
        
        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_breaker_open = False
        self._circuit_breaker_opened_at = 0.0
        
        # Background tasks
        self._batch_processor_task: Optional[asyncio.Task] = None
        self._metrics_updater_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"DynamicBatchManager initialized with target batch size: "
            f"{self.config.target_batch_size}"
        )
    
    async def start(self):
        """Start the batch manager and background tasks."""
        logger.info("Starting dynamic batch manager")
        
        self._batch_processor_task = asyncio.create_task(
            self._batch_processor_loop()
        )
        self._metrics_updater_task = asyncio.create_task(
            self._metrics_updater_loop()
        )
    
    async def stop(self):
        """Stop the batch manager and clean up resources."""
        logger.info("Stopping dynamic batch manager")
        
        if self._batch_processor_task:
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass
        
        if self._metrics_updater_task:
            self._metrics_updater_task.cancel()
            try:
                await self._metrics_updater_task
            except asyncio.CancelledError:
                pass
        
        # Process any remaining requests
        if self._pending_requests:
            logger.warning(f"Processing {len(self._pending_requests)} remaining requests")
            await self._process_pending_batch()
    
    async def submit_request(
        self,
        request_data: Dict[str, Any],
        priority: int = 1,
        timeout: Optional[float] = None
    ) -> str:
        """
        Submit a request for batch processing.
        
        Args:
            request_data: Request data to process
            priority: Request priority (0=highest, 2=lowest)
            timeout: Optional timeout for request
            
        Returns:
            Request ID for tracking
        """
        # Check circuit breaker
        if self._circuit_breaker_open:
            current_time = time.time()
            if current_time - self._circuit_breaker_opened_at < self.config.circuit_breaker_timeout:
                raise RuntimeError("Batch processing circuit breaker is open")
            else:
                # Reset circuit breaker
                self._circuit_breaker_open = False
                self._consecutive_failures = 0
                logger.info("Batch processing circuit breaker reset")
        
        request_id = f"batch_req_{int(time.time() * 1000000)}_{priority}"
        
        request_item = {
            "id": request_id,
            "data": request_data,
            "priority": priority,
            "timeout": timeout,
            "submitted_at": time.time(),
            "future": asyncio.Future()
        }
        
        async with self._batch_lock:
            self._pending_requests.append(request_item)
            # Sort by priority (0 = highest priority)
            self._pending_requests.sort(key=lambda x: x["priority"])
        
        # Signal batch processor
        self._batch_event.set()
        
        logger.debug(f"Submitted request {request_id} for batch processing (priority {priority})")
        
        # Wait for result
        return await request_item["future"]
    
    def _calculate_dynamic_batch_size(self) -> int:
        """Calculate optimal batch size based on current conditions."""
        if not self.config.enable_adaptive_sizing:
            return self.config.target_batch_size
        
        # Get current server load
        current_load = self._get_current_load()
        
        # Base size from configuration
        base_size = self.config.target_batch_size
        
        # Adjust based on server load
        if current_load < self.config.low_load_threshold:
            # Low load - increase batch size for better throughput
            load_factor = 1.0 + self.config.load_adjustment_factor
        elif current_load > self.config.high_load_threshold:
            # High load - decrease batch size for responsiveness
            load_factor = 1.0 - self.config.load_adjustment_factor
        else:
            # Normal load - use base size
            load_factor = 1.0
        
        # Adjust based on recent performance
        performance_factor = self._calculate_performance_factor()
        
        # Calculate adjusted size
        adjusted_size = int(base_size * load_factor * performance_factor)
        
        # Clamp to configured bounds
        final_size = max(
            self.config.min_batch_size,
            min(adjusted_size, self.config.max_batch_size)
        )
        
        # Smooth the adjustment
        if hasattr(self, '_current_batch_size'):
            alpha = self.config.adaptation_rate
            final_size = int(
                alpha * final_size + (1 - alpha) * self._current_batch_size
            )
        
        self._current_batch_size = final_size
        
        logger.debug(
            f"Dynamic batch size calculated: {final_size} "
            f"(load: {current_load:.3f}, load_factor: {load_factor:.3f}, "
            f"perf_factor: {performance_factor:.3f})"
        )
        
        return final_size
    
    def _get_current_load(self) -> float:
        """Get current server load metric."""
        if self.load_tracker:
            try:
                load = self.load_tracker()
                self._load_samples.append(load)
                return load
            except Exception as e:
                logger.warning(f"Failed to get server load: {e}")
        
        # Use recent average if available
        if self._load_samples:
            return sum(self._load_samples) / len(self._load_samples)
        
        # Default to moderate load
        return 0.5
    
    def _calculate_performance_factor(self) -> float:
        """Calculate performance adjustment factor based on recent history."""
        if len(self._performance_history) < 5:
            return 1.0  # Not enough data
        
        # Calculate recent throughput trend
        recent_perf = list(self._performance_history)[-10:]  # Last 10 batches
        older_perf = list(self._performance_history)[-20:-10]  # Previous 10 batches
        
        if not older_perf:
            return 1.0
        
        recent_avg = np.mean([p["throughput"] for p in recent_perf])
        older_avg = np.mean([p["throughput"] for p in older_perf])
        
        if older_avg == 0:
            return 1.0
        
        # If recent throughput is better, allow larger batches
        # If worse, prefer smaller batches
        throughput_ratio = recent_avg / older_avg
        
        if throughput_ratio > 1.1:
            return 1.1  # Increase batch size
        elif throughput_ratio < 0.9:
            return 0.9  # Decrease batch size
        else:
            return 1.0  # Keep current size
    
    def _calculate_batch_wait_time(self, pending_count: int, target_size: int) -> float:
        """Calculate how long to wait for more requests to fill batch."""
        if pending_count >= target_size:
            return 0.0  # Batch is full, process immediately
        
        # Calculate fill ratio
        fill_ratio = pending_count / target_size
        
        # Use exponential decay for wait time based on fill ratio
        base_wait = self.config.max_batch_wait_ms
        adjusted_wait = base_wait * (1.0 - fill_ratio) ** 2
        
        # Apply minimum wait time
        final_wait = max(adjusted_wait, self.config.min_batch_wait_ms)
        
        # Convert to seconds
        return final_wait / 1000.0
    
    async def _batch_processor_loop(self):
        """Main batch processing loop."""
        logger.info("Batch processor loop started")
        
        while True:
            try:
                # Wait for requests or timeout
                try:
                    await asyncio.wait_for(self._batch_event.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Check for pending requests even without new submissions
                    pass
                
                self._batch_event.clear()
                
                # Check if we have pending requests
                async with self._batch_lock:
                    pending_count = len(self._pending_requests)
                
                if pending_count == 0:
                    continue
                
                # Calculate optimal batch size and wait time
                target_batch_size = self._calculate_dynamic_batch_size()
                wait_time = self._calculate_batch_wait_time(pending_count, target_batch_size)
                
                # Wait for more requests if beneficial
                if wait_time > 0 and pending_count < target_batch_size:
                    await asyncio.sleep(wait_time)
                
                # Process the batch
                await self._process_pending_batch()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch processor loop error: {e}", exc_info=True)
                self._consecutive_failures += 1
                
                if (self.config.enable_circuit_breaker and 
                    self._consecutive_failures >= self.config.failure_threshold):
                    self._circuit_breaker_open = True
                    self._circuit_breaker_opened_at = time.time()
                    logger.error(
                        f"Batch processing circuit breaker opened after "
                        f"{self._consecutive_failures} consecutive failures"
                    )
                
                await asyncio.sleep(1.0)  # Back off on error
    
    async def _process_pending_batch(self):
        """Process the current batch of pending requests."""
        async with self._batch_lock:
            if not self._pending_requests:
                return
            
            # Take requests for this batch
            batch_requests = self._pending_requests[:]
            self._pending_requests.clear()
        
        batch_size = len(batch_requests)
        batch_start_time = time.time()
        
        logger.info(f"Processing batch of {batch_size} requests")
        
        try:
            # Extract input data for batch processing
            input_data = [req["data"]["input_data"] for req in batch_requests]
            
            # Get processing parameters from first request (assume similar configs)
            first_req = batch_requests[0]["data"]
            membrane_depth = first_req.get("membrane_depth")
            esn_size = first_req.get("esn_size")
            
            # Process batch using existing DTESN processor
            # This would be injected or configured
            if hasattr(self, '_dtesn_processor'):
                results = await self._dtesn_processor.process_batch(
                    inputs=input_data,
                    membrane_depth=membrane_depth,
                    esn_size=esn_size,
                    max_concurrent=min(batch_size, 8)  # Reasonable concurrency limit
                )
            else:
                # Fallback for testing/demo
                results = [
                    {
                        "input_data": inp,
                        "processed_output": {"result": f"processed_{inp[:10]}"},
                        "processing_time_ms": 10.0,
                        "batch_processed": True
                    }
                    for inp in input_data
                ]
            
            # Resolve futures with results
            for req, result in zip(batch_requests, results):
                if not req["future"].done():
                    req["future"].set_result(result)
            
            # Update metrics
            batch_time = (time.time() - batch_start_time) * 1000
            throughput = batch_size / (batch_time / 1000.0)  # requests per second
            
            self._update_performance_metrics(batch_size, batch_time, throughput)
            self._consecutive_failures = 0  # Reset on success
            
            logger.info(
                f"Batch processing completed: {batch_size} requests in {batch_time:.2f}ms "
                f"(throughput: {throughput:.1f} req/s)"
            )
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}", exc_info=True)
            
            # Fail all requests in batch
            for req in batch_requests:
                if not req["future"].done():
                    req["future"].set_exception(e)
            
            self._consecutive_failures += 1
            raise
    
    def _update_performance_metrics(self, batch_size: int, processing_time_ms: float, throughput: float):
        """Update performance metrics with batch results."""
        # Update basic metrics
        self._metrics.requests_processed += batch_size
        self._metrics.total_processing_time_ms += processing_time_ms
        
        # Update averages
        total_batches = len(self._performance_history) + 1
        self._metrics.avg_batch_size = (
            (self._metrics.avg_batch_size * (total_batches - 1) + batch_size) / total_batches
        )
        self._metrics.avg_processing_time_ms = (
            (self._metrics.avg_processing_time_ms * (total_batches - 1) + processing_time_ms) 
            / total_batches
        )
        
        # Update load metrics
        current_load = self._get_current_load()
        self._metrics.server_load_samples.append(current_load)
        if len(self._metrics.server_load_samples) > 100:
            self._metrics.server_load_samples = self._metrics.server_load_samples[-100:]
        
        self._metrics.avg_server_load = np.mean(self._metrics.server_load_samples)
        
        # Calculate throughput improvement
        if self._baseline_throughput is None:
            self._baseline_throughput = throughput
            self._metrics.throughput_improvement = 0.0
        else:
            self._metrics.throughput_improvement = (
                (throughput - self._baseline_throughput) / self._baseline_throughput * 100
            )
        
        # Update performance history
        perf_record = {
            "timestamp": time.time(),
            "batch_size": batch_size,
            "processing_time_ms": processing_time_ms,
            "throughput": throughput,
            "server_load": current_load
        }
        self._performance_history.append(perf_record)
        
        self._metrics.last_updated = time.time()
    
    async def _metrics_updater_loop(self):
        """Background task to update metrics and perform maintenance."""
        while True:
            try:
                await asyncio.sleep(10.0)  # Update every 10 seconds
                
                # Clean up old performance data
                current_time = time.time()
                cutoff_time = current_time - 3600  # Keep 1 hour of history
                
                # Clean performance history
                while (self._performance_history and 
                       self._performance_history[0]["timestamp"] < cutoff_time):
                    self._performance_history.popleft()
                
                # Log current metrics
                logger.debug(
                    f"Batch metrics - Processed: {self._metrics.requests_processed}, "
                    f"Avg batch size: {self._metrics.avg_batch_size:.1f}, "
                    f"Throughput improvement: {self._metrics.throughput_improvement:.1f}%"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics updater error: {e}")
    
    def get_metrics(self) -> BatchingMetrics:
        """Get current batching metrics."""
        return self._metrics
    
    def get_current_batch_size(self) -> int:
        """Get current dynamic batch size."""
        return self._current_batch_size
    
    async def get_pending_count(self) -> int:
        """Get number of pending requests."""
        async with self._batch_lock:
            return len(self._pending_requests)
    
    def set_dtesn_processor(self, processor):
        """Set the DTESN processor for batch processing."""
        self._dtesn_processor = processor
        logger.info("DTESN processor configured for batch manager")