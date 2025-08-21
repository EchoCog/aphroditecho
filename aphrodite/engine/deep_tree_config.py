
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class DeepTreeEchoConfig:
    """Configuration for Deep Tree Echo cognitive enhancements."""
    
    # Meta-learning settings
    enable_meta_learning: bool = True
    meta_learning_rate: float = 0.001
    experience_memory_size: int = 1000
    meta_update_frequency: int = 10
    
    # Evolution engine settings
    enable_evolution: bool = True
    population_size: int = 50
    mutation_rate: float = 0.1
    selection_pressure: float = 0.8
    
    # AAR orchestration settings
    enable_aar: bool = True
    max_concurrent_agents: int = 100
    agent_allocation_strategy: str = "performance_based"
    
    # DTESN kernel settings
    enable_dtesn: bool = True
    membrane_hierarchy_depth: int = 4
    reservoir_size: int = 1000
    spectral_radius: float = 0.95
    
    # Performance constraints
    max_processing_latency_ms: float = 1.0
    min_convergence_rate: float = 0.8
    memory_limit_mb: int = 4096
    
    # 4E Embodied AI settings
    enable_embodied_ai: bool = True
    virtual_body_enabled: bool = True
    sensory_integration: bool = True
    motor_control: bool = True
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "DeepTreeEchoConfig":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})
        
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if self.meta_learning_rate <= 0 or self.meta_learning_rate >= 1:
            return False
        if self.experience_memory_size <= 0:
            return False
        if self.population_size <= 0:
            return False
        if self.max_processing_latency_ms <= 0:
            return False
        return True
