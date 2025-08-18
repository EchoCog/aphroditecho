#!/usr/bin/env python3
"""
Echo Pilot - Evolution-Simulation-Metasystem (ESM) Pattern

This module implements the ESM pattern with both original interfaces and 
standardized Echo component interfaces for backward compatibility and 
integration with the Echo ecosystem.

Original concept: Each ESMWorker represents a pixie assigned to a specific pattern,
evolving its internal state using random improvement and constraints from other workers.
"""

import asyncio
import random
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import standardized Echo components for new interfaces
try:
    from echo_component_base import ProcessingEchoComponent, EchoConfig, EchoResponse
    ECHO_STANDARDIZED_AVAILABLE = True
except ImportError:
    ECHO_STANDARDIZED_AVAILABLE = False
    ProcessingEchoComponent = object
    EchoConfig = None
    EchoResponse = None


# Original ESMWorker class - unchanged for backward compatibility
class ESMWorker:
    """
    Each ESMWorker represents a pixie assigned to a specific pattern.
    The worker evolves its internal state in each cycle using both random improvement 
    and constraints gathered from the output of other workers (acting as emitter values).
    """
    def __init__(self, pattern_name, initial_value=0.0):
        self.pattern_name = pattern_name
        self.state = initial_value  # This represents the quality/precision of the pattern's implementation.
        self.iteration = 0

    async def evolve(self, constraints):
        """Simulate self-improvement evolution with constraints from other workers"""
        # Simulate self-improvement evolution:
        # - 'improvement' is a random factor representing the gain in this cycle.
        # - 'constraint_factor' represents influences from other patterns.
        improvement = random.uniform(-0.1, 0.5)
        constraint_factor = sum(constraints) / (len(constraints) or 1)
        self.state = self.state + improvement + (constraint_factor * 0.1)
        self.iteration += 1

        print(f"[{self.pattern_name}] Cycle {self.iteration}: state updated to {self.state:.2f} "
              f"(improvement: {improvement:.2f}, constraint factor: {constraint_factor:.2f})")
        await asyncio.sleep(0.1)  # Simulate processing delay

        # Emit the updated state to be used as a constraint for other workers.
        return self.state


# Original ConstraintEmitter class - unchanged for backward compatibility
class ConstraintEmitter:
    """
    The ConstraintEmitter works like a message bus to hold and propagate the emitter values 
    (i.e. state) of every worker. Constraints provided to each worker are the states from all other workers.
    """
    def __init__(self):
        self.emitter_values = {}

    def update(self, pattern_name, value):
        self.emitter_values[pattern_name] = value

    def get_constraints(self, excluding=None):
        # Return emitter values excluding the given pattern (if any)
        return [value for name, value in self.emitter_values.items() if name != excluding]


# Standardized Echo component wrapper
class EchoPilotStandardized(ProcessingEchoComponent):
    """
    Standardized Echo Pilot component
    
    Provides ESM (Evolution-Simulation-Metasystem) capabilities with standardized interfaces.
    Inherits from ProcessingEchoComponent for processing pipeline functionality.
    """
    
    def __init__(self, config: EchoConfig):
        if not ECHO_STANDARDIZED_AVAILABLE:
            raise ImportError("Echo standardized components not available")
        
        super().__init__(config)
        
        # ESM-specific configuration
        self.worker_patterns = []
        self.workers = []
        self.emitter = ConstraintEmitter()
        self.evolution_cycles = 0
        self.max_cycles = 5
        
        # Default patterns if none provided
        self.default_patterns = [
            "Differential Gear",   # Cross-departmental coordination system
            "Epicyclic Train",     # Adaptive resource allocation matrix
            "Zodiac Dial",         # Long-term strategic planning cycle
        ]
    
    def initialize(self) -> EchoResponse:
        """Initialize the ESM pilot system"""
        try:
            # Use patterns from config or defaults
            patterns = self.config.custom_params.get('patterns', self.default_patterns)
            self.worker_patterns = patterns
            
            # Initialize ESM workers with random initial states
            self.workers = [ESMWorker(name, initial_value=random.uniform(0, 1)) 
                          for name in self.worker_patterns]
            
            # Initialize the emitter's state values
            for worker in self.workers:
                self.emitter.update(worker.pattern_name, worker.state)
            
            self._initialized = True
            self.logger.info(f"ESM pilot initialized with {len(self.workers)} workers")
            
            return EchoResponse(
                success=True,
                message=f"ESM pilot system initialized with {len(self.workers)} workers",
                data={
                    'worker_count': len(self.workers),
                    'patterns': self.worker_patterns,
                    'initial_states': {w.pattern_name: w.state for w in self.workers}
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """
        Process ESM evolution requests
        
        Supported operations:
        - 'evolve_cycle': Run a single evolution cycle
        - 'evolve_multiple': Run multiple evolution cycles
        - 'get_states': Get current worker states
        - 'reset_workers': Reset all workers to initial state
        """
        try:
            if not self._initialized:
                return EchoResponse(
                    success=False,
                    message="Component not initialized - call initialize() first"
                )
            
            # Parse input data
            if isinstance(input_data, str):
                operation = input_data
                params = kwargs
            elif isinstance(input_data, dict):
                operation = input_data.get('operation', 'evolve_cycle')
                params = input_data.get('params', {})
                params.update(kwargs)
            else:
                operation = 'evolve_cycle'
                params = kwargs
            
            self.logger.info(f"Processing ESM operation: {operation}")
            
            # Route to appropriate operation
            if operation == 'evolve_cycle':
                return asyncio.run(self._evolve_single_cycle(**params))
            elif operation == 'evolve_multiple':
                cycles = params.get('cycles', self.max_cycles)
                return asyncio.run(self._evolve_multiple_cycles(cycles))
            elif operation == 'get_states':
                return self._get_worker_states()
            elif operation == 'reset_workers':
                return self._reset_workers(**params)
            else:
                return EchoResponse(
                    success=False,
                    message=f"Unknown operation: {operation}",
                    metadata={'valid_operations': [
                        'evolve_cycle', 'evolve_multiple', 'get_states', 'reset_workers'
                    ]}
                )
                
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """
        Echo operation for ESM pilot
        
        Returns current system state with echo characteristics
        """
        try:
            echoed_data = {
                'pilot_state': {
                    'evolution_cycles': self.evolution_cycles,
                    'worker_count': len(self.workers),
                    'initialized': self._initialized
                },
                'worker_states': {w.pattern_name: w.state for w in self.workers} if self.workers else {},
                'echo_value': echo_value,
                'timestamp': datetime.now().isoformat()
            }
            
            return EchoResponse(
                success=True,
                data=echoed_data,
                message=f"ESM pilot echo (value: {echo_value}, cycles: {self.evolution_cycles})",
                metadata={
                    'echo_value': echo_value,
                    'evolution_cycles': self.evolution_cycles
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "echo")
    
    async def _evolve_single_cycle(self) -> EchoResponse:
        """Run a single evolution cycle"""
        try:
            self.evolution_cycles += 1
            
            # Run one evolution cycle using original functions
            await run_cycle(self.workers, self.emitter)
            
            # Collect results
            final_states = {worker.pattern_name: worker.state for worker in self.workers}
            
            return EchoResponse(
                success=True,
                data={
                    'cycle_number': self.evolution_cycles,
                    'worker_states': final_states,
                    'emitter_values': dict(self.emitter.emitter_values)
                },
                message=f"Evolution cycle {self.evolution_cycles} completed",
                metadata={'cycle_number': self.evolution_cycles}
            )
            
        except Exception as e:
            return self.handle_error(e, f"evolve_cycle_{self.evolution_cycles}")
    
    async def _evolve_multiple_cycles(self, cycles: int) -> EchoResponse:
        """Run multiple evolution cycles"""
        try:
            start_cycle = self.evolution_cycles
            cycle_results = []
            
            for cycle in range(cycles):
                result = await self._evolve_single_cycle()
                if result.success:
                    cycle_results.append(result.data)
                else:
                    return result  # Return the error
                
                await asyncio.sleep(0.5)  # Delay between global cycles
            
            return EchoResponse(
                success=True,
                data={
                    'total_cycles_run': cycles,
                    'start_cycle': start_cycle + 1,
                    'end_cycle': self.evolution_cycles,
                    'cycle_results': cycle_results,
                    'final_states': {w.pattern_name: w.state for w in self.workers}
                },
                message=f"Completed {cycles} evolution cycles",
                metadata={
                    'cycles_run': cycles,
                    'total_evolution_cycles': self.evolution_cycles
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "evolve_multiple")
    
    def _get_worker_states(self) -> EchoResponse:
        """Get current states of all workers"""
        try:
            states = {
                worker.pattern_name: {
                    'state': worker.state,
                    'iteration': worker.iteration
                }
                for worker in self.workers
            }
            
            return EchoResponse(
                success=True,
                data={
                    'worker_states': states,
                    'evolution_cycles': self.evolution_cycles,
                    'emitter_values': dict(self.emitter.emitter_values)
                },
                message="Current worker states retrieved"
            )
            
        except Exception as e:
            return self.handle_error(e, "get_states")
    
    def _reset_workers(self, patterns: Optional[List[str]] = None) -> EchoResponse:
        """Reset workers to initial state"""
        try:
            if patterns:
                self.worker_patterns = patterns
            
            # Reinitialize workers
            self.workers = [ESMWorker(name, initial_value=random.uniform(0, 1)) 
                          for name in self.worker_patterns]
            self.emitter = ConstraintEmitter()
            
            # Initialize emitter
            for worker in self.workers:
                self.emitter.update(worker.pattern_name, worker.state)
            
            self.evolution_cycles = 0
            
            return EchoResponse(
                success=True,
                data={
                    'worker_count': len(self.workers),
                    'patterns': self.worker_patterns,
                    'initial_states': {w.pattern_name: w.state for w in self.workers}
                },
                message=f"Workers reset with {len(self.workers)} patterns"
            )
            
        except Exception as e:
            return self.handle_error(e, "reset_workers")


# Original functions - unchanged for backward compatibility
async def run_cycle(workers, emitter):
    """Run one global evolution cycle where every worker evolves concurrently."""
    tasks = []
    
    # Launch evolution for every worker, passing constraints from all other workers.
    for worker in workers:
        constraints = emitter.get_constraints(excluding=worker.pattern_name)
        tasks.append(asyncio.create_task(worker.evolve(constraints)))
    
    # Wait for all workers to finish their evolution cycle.
    results = await asyncio.gather(*tasks)
    
    # Update the emitter with the latest states from each worker.
    for worker, result in zip(workers, results):
        emitter.update(worker.pattern_name, result)


async def main():
    """Main function that sets up the system and runs multiple evolution cycles."""
    # Define a set of patterns (the core business functions or germs of design patterns)
    worker_patterns = [
        "Differential Gear",   # Cross-departmental coordination system
        "Epicyclic Train",     # Adaptive resource allocation matrix
        "Zodiac Dial",         # Long-term strategic planning cycle
    ]
    
    # Initialize ESM workers with random initial states.
    workers = [ESMWorker(name, initial_value=random.uniform(0, 1)) for name in worker_patterns]
    emitter = ConstraintEmitter()
    
    # Initialize the emitter's state values.
    for worker in workers:
        emitter.update(worker.pattern_name, worker.state)
    
    # Simulate 5 evolution cycles.
    for cycle in range(5):
        print(f"\n=== Global Cycle {cycle+1} ===")
        await run_cycle(workers, emitter)
        await asyncio.sleep(0.5)  # Delay between global cycles.
    
    print("\nFinal states:")
    for worker in workers:
        print(f"{worker.pattern_name}: {worker.state:.2f}")


# Factory function for creating standardized ESM pilot
def create_esm_pilot_system(patterns: Optional[List[str]] = None) -> EchoPilotStandardized:
    """Create a standardized ESM pilot system"""
    if not ECHO_STANDARDIZED_AVAILABLE:
        raise ImportError("Echo standardized components not available")
    
    config = EchoConfig(
        component_name="EchoPilot",
        version="1.0.0",
        custom_params={'patterns': patterns} if patterns else {}
    )
    
    pilot = EchoPilotStandardized(config)
    result = pilot.initialize()
    
    if not result.success:
        raise RuntimeError(f"Failed to initialize ESM pilot: {result.message}")
    
    return pilot


if __name__ == "__main__":
    asyncio.run(main())
