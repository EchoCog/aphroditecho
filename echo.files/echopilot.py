import asyncio
import random

# Each ESMWorker represents a pixie assigned to a specific pattern.
# The worker evolves its internal state in each cycle using both random improvement and constraints
# gathered from the output of other workers (acting as emitter values).
class ESMWorker:
    def __init__(self, pattern_name, initial_value=0.0):
        self.pattern_name = pattern_name
        self.state = initial_value  # This represents the quality/precision of the pattern's implementation.
        self.iteration = 0

    async def evolve(self, constraints):
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

# The ConstraintEmitter works like a message bus to hold and propagate the emitter values (i.e. state)
# of every worker. Constraints provided to each worker are the states from all other workers.
class ConstraintEmitter:
    def __init__(self):
        self.emitter_values = {}

    def update(self, pattern_name, value):
        self.emitter_values[pattern_name] = value

    def get_constraints(self, excluding=None):
        # Return emitter values excluding the given pattern (if any)
        return [value for name, value in self.emitter_values.items() if name != excluding]

# Run one global evolution cycle where every worker evolves concurrently.
async def run_cycle(workers, emitter):
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

# Main function that sets up the system and runs multiple evolution cycles.
async def main():
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

if __name__ == "__main__":
    asyncio.run(main())
