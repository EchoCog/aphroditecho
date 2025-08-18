"""
Echo Pilot - Standardized Version

Migrated from original echopilot.py to use standardized Echo component base classes.
This demonstrates the Evolution-Simulation-Metasystem (ESM) pattern with
standardized Echo interfaces.

Original concept: Each ESMWorker represents a pixie assigned to a specific pattern,
evolving its internal state using random improvement and constraints from other workers.
"""

import asyncio
import random
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import standardized Echo components
from echo_component_base import ProcessingEchoComponent, EchoConfig, EchoResponse


class ESMWorker(ProcessingEchoComponent):
    """
    Evolution-Simulation-Metasystem Worker
    
    Standardized Echo component for pattern evolution with constraint-based improvement.
    Inherits from ProcessingEchoComponent for processing pipeline functionality.
    """
    
    def __init__(self, config: EchoConfig, pattern_name: str, initial_value: float = 0.0):
        super().__init__(config)
        self.pattern_name = pattern_name
        self.evolution_state = initial_value  # Keep evolution state separate
        self.iteration = 0
        self.evolution_history = []
        
        # Initialize component state dict for Echo framework
        self.state = {
            'pattern_name': pattern_name,
            'evolution_state': initial_value,
            'iteration': 0
        }
        
        # Add evolution processing step with proper constraint handling
        self.add_processing_step(self._create_improvement_step(), "random_improvement")
        self.add_processing_step(self._create_constraint_step(), "constraint_application")
        
    def initialize(self) -> EchoResponse:
        """Initialize the ESM worker"""
        try:
            self._initialized = True
            self.logger.info(f"ESM Worker '{self.pattern_name}' initialized with state: {self.evolution_state:.2f}")
            
            return EchoResponse(
                success=True,
                message=f"ESM Worker '{self.pattern_name}' initialized",
                metadata={'pattern_name': self.pattern_name, 'initial_state': self.evolution_state}
            )
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """
        Process evolution step with constraints
        
        Args:
            input_data: Constraints from other workers (list of float values)
            **kwargs: Additional processing parameters
        """
        try:
            validation = self.validate_input(input_data)
            if not validation.success:
                return validation
            
            # Input should be constraints (list of values from other workers)
            constraints = input_data if isinstance(input_data, list) else []
            
            # Store constraints for processing pipeline
            processing_data = {'current_state': self.evolution_state, 'constraints': constraints}
            
            # Execute processing pipeline (improvement + constraints)
            pipeline_result = self.execute_pipeline(processing_data)
            
            if not pipeline_result.success:
                return pipeline_result
            
            # Update internal state
            new_state = pipeline_result.data
            self.evolution_state = new_state
            self.iteration += 1
            
            # Update component state
            self.state.update({
                'evolution_state': self.evolution_state,
                'iteration': self.iteration,
                'last_constraints': constraints
            })
            
            # Record evolution history
            self.evolution_history.append({
                'iteration': self.iteration,
                'state': self.evolution_state,
                'constraints': constraints,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"[{self.pattern_name}] Cycle {self.iteration}: state updated to {self.evolution_state:.2f}")
            
            return EchoResponse(
                success=True,
                data=self.evolution_state,
                message=f"Evolution cycle {self.iteration} completed",
                metadata={
                    'pattern_name': self.pattern_name,
                    'iteration': self.iteration,
                    'state': self.evolution_state,
                    'constraints_applied': len(constraints)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """
        Echo operation for ESM Worker
        
        Returns augmented state information with echo characteristics
        """
        try:
            echoed_data = {
                'pattern_name': self.pattern_name,
                'current_state': self.evolution_state,
                'iteration': self.iteration,
                'echo_value': echo_value,
                'evolution_trace': self.evolution_history[-3:] if self.evolution_history else [],
                'timestamp': datetime.now().isoformat()
            }
            
            return EchoResponse(
                success=True,
                data=echoed_data,
                message=f"Echo from {self.pattern_name} (value: {echo_value})",
                metadata={'echo_value': echo_value, 'state': self.evolution_state}
            )
            
        except Exception as e:
            return self.handle_error(e, "echo")
    
    def _create_improvement_step(self):
        """Create improvement processing step with closure for constraints"""
        def apply_improvement(state_data):
            current_state = state_data['current_state']
            improvement = random.uniform(-0.1, 0.5)
            return {
                'current_state': current_state + improvement,
                'constraints': state_data['constraints'],
                'improvement': improvement
            }
        return apply_improvement
    
    def _create_constraint_step(self):
        """Create constraint processing step with closure"""
        def apply_constraints(state_data):
            current_state = state_data['current_state']
            constraints = state_data['constraints']
            constraint_factor = sum(constraints) / (len(constraints) or 1)
            final_state = current_state + (constraint_factor * 0.1)
            return final_state
        return apply_constraints
    
    async def evolve_async(self, constraints: List[float]) -> float:
        """
        Async evolution method for compatibility with original interface
        
        This wraps the standardized process() method in async interface
        """
        result = self.process(constraints)
        
        # Simulate processing delay as in original
        await asyncio.sleep(0.1)
        
        if result.success:
            return result.data
        else:
            self.logger.error(f"Evolution failed: {result.message}")
            return self.evolution_state


class ConstraintEmitter(ProcessingEchoComponent):
    """
    Constraint Emitter - Message bus for worker states
    
    Standardized Echo component for managing and propagating worker constraints.
    """
    
    def __init__(self, config: EchoConfig):
        super().__init__(config)
        self.emitter_values = {}
        
    def initialize(self) -> EchoResponse:
        """Initialize the constraint emitter"""
        try:
            self._initialized = True
            self.logger.info("Constraint Emitter initialized")
            
            return EchoResponse(
                success=True,
                message="Constraint Emitter initialized"
            )
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """
        Process constraint updates
        
        Args:
            input_data: Dict with 'pattern_name' and 'value' keys
        """
        try:
            validation = self.validate_input(input_data)
            if not validation.success:
                return validation
            
            if isinstance(input_data, dict) and 'pattern_name' in input_data and 'value' in input_data:
                pattern_name = input_data['pattern_name']
                value = input_data['value']
                
                self.emitter_values[pattern_name] = value
                
                return EchoResponse(
                    success=True,
                    data=self.emitter_values.copy(),
                    message=f"Updated constraint for {pattern_name}",
                    metadata={'pattern_name': pattern_name, 'value': value}
                )
            else:
                return EchoResponse(
                    success=False,
                    message="Input must be dict with 'pattern_name' and 'value' keys"
                )
                
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """Echo current constraint state"""
        try:
            echoed_data = {
                'emitter_values': self.emitter_values.copy(),
                'total_patterns': len(self.emitter_values),
                'echo_value': echo_value,
                'timestamp': datetime.now().isoformat()
            }
            
            return EchoResponse(
                success=True,
                data=echoed_data,
                message=f"Constraint emitter echo (value: {echo_value})",
                metadata={'echo_value': echo_value, 'patterns': len(self.emitter_values)}
            )
            
        except Exception as e:
            return self.handle_error(e, "echo")
    
    def update(self, pattern_name: str, value: float):
        """Update emitter value (legacy interface)"""
        result = self.process({'pattern_name': pattern_name, 'value': value})
        return result.success
    
    def get_constraints(self, excluding: Optional[str] = None) -> List[float]:
        """Get constraints excluding specified pattern (legacy interface)"""
        return [value for name, value in self.emitter_values.items() if name != excluding]


# Async orchestration functions (maintaining original interface)
async def run_cycle(workers: List[ESMWorker], emitter: ConstraintEmitter):
    """Run one global evolution cycle where every worker evolves concurrently"""
    tasks = []
    
    # Launch evolution for every worker, passing constraints from all other workers
    for worker in workers:
        constraints = emitter.get_constraints(excluding=worker.pattern_name)
        tasks.append(asyncio.create_task(worker.evolve_async(constraints)))
    
    # Wait for all workers to finish their evolution cycle
    results = await asyncio.gather(*tasks)
    
    # Update the emitter with the latest states from each worker
    for worker, result in zip(workers, results):
        emitter.update(worker.pattern_name, result)


async def main():
    """Main function demonstrating standardized Echo Pilot system"""
    print("🤖 Echo Pilot - Standardized ESM System")
    print("=" * 50)
    
    # Define pattern configurations
    worker_patterns = [
        "Differential Gear",   # Cross-departmental coordination system
        "Epicyclic Train",     # Adaptive resource allocation matrix
        "Zodiac Dial",         # Long-term strategic planning cycle
    ]
    
    # Create standardized configurations
    workers = []
    for pattern_name in worker_patterns:
        config = EchoConfig(
            component_name=f"ESM_{pattern_name.replace(' ', '_')}",
            version="1.0.0",
            echo_threshold=0.75,
            debug_mode=False
        )
        
        worker = ESMWorker(config, pattern_name, initial_value=random.uniform(0, 1))
        init_result = worker.initialize()
        
        if init_result.success:
            workers.append(worker)
        else:
            print(f"❌ Failed to initialize worker for {pattern_name}: {init_result.message}")
    
    # Create constraint emitter
    emitter_config = EchoConfig(
        component_name="ConstraintEmitter",
        version="1.0.0"
    )
    
    emitter = ConstraintEmitter(emitter_config)
    emitter_init = emitter.initialize()
    
    if not emitter_init.success:
        print(f"❌ Failed to initialize emitter: {emitter_init.message}")
        return
    
    # Initialize emitter with worker states
    for worker in workers:
        emitter.update(worker.pattern_name, worker.state)
    
    # Run evolution cycles
    print(f"\n🔄 Running evolution cycles...")
    for cycle in range(5):
        print(f"\n=== Global Cycle {cycle+1} ===")
        await run_cycle(workers, emitter)
        await asyncio.sleep(0.5)  # Delay between global cycles
    
    # Display final results
    print(f"\n📊 Final States:")
    for worker in workers:
        echo_result = worker.echo(None, echo_value=1.0)
        if echo_result.success:
            data = echo_result.data
            print(f"  {data['pattern_name']}: {data['current_state']:.2f} (iterations: {data['iteration']})")
    
    # Show emitter state
    emitter_echo = emitter.echo(None, echo_value=1.0)
    if emitter_echo.success:
        print(f"\n🔗 Constraint Emitter State:")
        for pattern, value in emitter_echo.data['emitter_values'].items():
            print(f"  {pattern}: {value:.2f}")


def create_esm_system(patterns: List[str]) -> tuple[List[ESMWorker], ConstraintEmitter]:
    """
    Factory function to create a standardized ESM system
    
    Args:
        patterns: List of pattern names
        
    Returns:
        Tuple of (workers, emitter)
    """
    workers = []
    
    for pattern_name in patterns:
        config = EchoConfig(
            component_name=f"ESM_{pattern_name.replace(' ', '_')}",
            version="1.0.0",
            echo_threshold=0.75
        )
        
        worker = ESMWorker(config, pattern_name, initial_value=random.uniform(0, 1))
        worker.initialize()
        workers.append(worker)
    
    emitter_config = EchoConfig(component_name="ConstraintEmitter", version="1.0.0")
    emitter = ConstraintEmitter(emitter_config)
    emitter.initialize()
    
    return workers, emitter


if __name__ == "__main__":
    asyncio.run(main())