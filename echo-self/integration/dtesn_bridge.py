"""
DTESN Bridge for Echo-Self AI Evolution Engine.

Integrates the evolution engine with the Deep Tree Echo System Network (DTESN)
components from echo.kern for membrane computing and reservoir dynamics.
"""

import logging
from typing import Dict, Any, List

# Handle both absolute and relative imports
try:
    from core.interfaces import Individual
except ImportError:
    from ..core.interfaces import Individual

logger = logging.getLogger(__name__)


class DTESNBridge:
    """Bridge between Echo-Self Evolution Engine and DTESN components."""
    
    def __init__(self):
        self.dtesn_kernel = None
        self.membrane_system = None
        self.reservoir = None
        self.b_series_calculator = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize DTESN components."""
        try:
            # Import DTESN components
            self._import_dtesn_components()
            
            # Initialize components
            self._initialize_components()
            
            self._initialized = True
            logger.info("DTESN Bridge initialized successfully")
            return True
            
        except ImportError as e:
            logger.warning(f"DTESN components not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize DTESN Bridge: {e}")
            return False
    
    def _import_dtesn_components(self):
        """Import DTESN components from echo.kern."""
        try:
            # Import P-System membranes
            from ...echo.kern.psystem_membranes import PSystemMembranes
            self.PSystemMembranes = PSystemMembranes
            
            # Import ESN reservoir
            from ...echo.kern.esn_reservoir import ESNReservoir
            self.ESNReservoir = ESNReservoir
            
            # Import B-Series calculator
            from ...echo.kern.bseries_differential_calculator import BSeriesCalculator
            self.BSeriesCalculator = BSeriesCalculator
            
            # Import DTESN compiler if available
            try:
                from ...echo.kern.dtesn_compiler import DTESNCompiler
                self.DTESNCompiler = DTESNCompiler
            except ImportError:
                logger.warning("DTESN Compiler not available")
                self.DTESNCompiler = None
            
        except ImportError as e:
            logger.warning(f"Some DTESN components not available: {e}")
            # Try alternative import paths
            self._try_alternative_imports()
    
    def _try_alternative_imports(self):
        """Try alternative import paths for DTESN components."""
        try:
            import sys
            import os
            
            # Add echo.kern to path
            echo_kern_path = os.path.join(os.path.dirname(__file__), '..', '..', 'echo.kern')
            if echo_kern_path not in sys.path:
                sys.path.insert(0, echo_kern_path)
            
            # Retry imports
            import psystem_membranes
            import esn_reservoir
            import bseries_differential_calculator
            
            self.PSystemMembranes = psystem_membranes.PSystemMembranes
            self.ESNReservoir = esn_reservoir.ESNReservoir
            self.BSeriesCalculator = bseries_differential_calculator.BSeriesCalculator
            
        except ImportError as e:
            logger.error(f"Could not import DTESN components: {e}")
            raise
    
    def _initialize_components(self):
        """Initialize DTESN components."""
        if not hasattr(self, 'PSystemMembranes'):
            raise ImportError("DTESN components not properly imported")
        
        # Initialize P-System membranes
        self.membrane_system = self.PSystemMembranes()
        
        # Initialize ESN reservoir
        reservoir_config = {
            'input_size': 64,
            'reservoir_size': 512,
            'output_size': 32,
            'spectral_radius': 0.9,
            'leak_rate': 0.1,
            'connectivity': 0.1
        }
        self.reservoir = self.ESNReservoir(**reservoir_config)
        
        # Initialize B-Series calculator
        self.b_series_calculator = self.BSeriesCalculator()
        
        logger.info("DTESN components initialized")
    
    def is_initialized(self) -> bool:
        """Check if the bridge is initialized."""
        return self._initialized
    
    def process_individual_through_dtesn(self, individual: Individual) -> Dict[str, Any]:
        """Process an individual through DTESN components."""
        if not self._initialized:
            logger.warning("DTESN Bridge not initialized, returning empty results")
            return {}
        
        try:
            results = {}
            
            # Process through membrane system
            if self.membrane_system:
                membrane_state = self._process_through_membranes(individual)
                results['membrane_state'] = membrane_state
            
            # Process through reservoir
            if self.reservoir:
                reservoir_state = self._process_through_reservoir(individual)
                results['reservoir_state'] = reservoir_state
            
            # Calculate B-Series dynamics
            if self.b_series_calculator:
                dynamics = self._calculate_dynamics(individual)
                results['dynamics'] = dynamics
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing individual through DTESN: {e}")
            return {}
    
    def _process_through_membranes(self, individual: Individual) -> Dict[str, Any]:
        """Process individual through P-System membranes."""
        try:
            # Convert individual genome to membrane input format
            genome_data = self._genome_to_membrane_format(individual.genome)
            
            # Process through membranes
            membrane_output = self.membrane_system.process(genome_data)
            
            return {
                'input_data': genome_data,
                'output_data': membrane_output,
                'membrane_count': len(membrane_output) if isinstance(membrane_output, (list, dict)) else 1
            }
            
        except Exception as e:
            logger.error(f"Error in membrane processing: {e}")
            return {}
    
    def _process_through_reservoir(self, individual: Individual) -> Dict[str, Any]:
        """Process individual through ESN reservoir."""
        try:
            # Convert individual to reservoir input
            reservoir_input = self._genome_to_reservoir_format(individual.genome)
            
            # Process through reservoir
            reservoir_output = self.reservoir.process(reservoir_input)
            
            return {
                'input_data': reservoir_input,
                'output_data': reservoir_output,
                'reservoir_size': self.reservoir.reservoir_size if hasattr(self.reservoir, 'reservoir_size') else 0
            }
            
        except Exception as e:
            logger.error(f"Error in reservoir processing: {e}")
            return {}
    
    def _calculate_dynamics(self, individual: Individual) -> Dict[str, Any]:
        """Calculate B-Series dynamics for individual."""
        try:
            # Extract network structure for dynamics calculation
            layers = individual.genome.get('layers', [])
            
            if not layers:
                return {}
            
            # Calculate tree structures based on network topology
            tree_data = self._network_to_tree_structure(layers)
            
            # Calculate B-Series coefficients
            b_series_result = self.b_series_calculator.calculate(tree_data)
            
            return {
                'tree_structure': tree_data,
                'b_series_coefficients': b_series_result,
                'complexity_measure': len(tree_data)
            }
            
        except Exception as e:
            logger.error(f"Error in dynamics calculation: {e}")
            return {}
    
    def _genome_to_membrane_format(self, genome: Dict[str, Any]) -> List[Any]:
        """Convert genome to P-System membrane input format."""
        # Simple conversion - in practice this would be more sophisticated
        membrane_input = []
        
        # Add layers as membrane objects
        for layer in genome.get('layers', []):
            membrane_obj = {
                'type': layer.get('type', 'dense'),
                'size': layer.get('size', 64),
                'activation': genome.get('activation_functions', {}).get(str(len(membrane_input)), 'relu')
            }
            membrane_input.append(membrane_obj)
        
        return membrane_input
    
    def _genome_to_reservoir_format(self, genome: Dict[str, Any]) -> List[float]:
        """Convert genome to ESN reservoir input format."""
        # Convert network structure to numerical input
        reservoir_input = []
        
        # Encode layers
        for layer in genome.get('layers', []):
            reservoir_input.extend([
                float(layer.get('size', 64)) / 512.0,  # Normalized size
                float(hash(layer.get('type', 'dense')) % 100) / 100.0,  # Type encoding
            ])
        
        # Encode connections
        for conn in genome.get('connections', []):
            reservoir_input.extend([
                float(conn.get('from', 0)) / 10.0,
                float(conn.get('to', 0)) / 10.0,
                conn.get('weight', 0.0)
            ])
        
        # Pad or truncate to standard size
        target_size = 64
        if len(reservoir_input) > target_size:
            reservoir_input = reservoir_input[:target_size]
        else:
            reservoir_input.extend([0.0] * (target_size - len(reservoir_input)))
        
        return reservoir_input
    
    def _network_to_tree_structure(self, layers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert network layers to tree structure for B-Series calculation."""
        tree_structure = []
        
        for i, layer in enumerate(layers):
            tree_node = {
                'id': i,
                'type': layer.get('type', 'dense'),
                'size': layer.get('size', 64),
                'children': [],
                'parent': i - 1 if i > 0 else None
            }
            tree_structure.append(tree_node)
        
        return tree_structure
    
    def update_individual_with_dtesn_feedback(
        self, 
        individual: Individual, 
        dtesn_results: Dict[str, Any]
    ) -> Individual:
        """Update individual based on DTESN processing feedback."""
        if not dtesn_results:
            return individual
        
        try:
            # Update individual metadata with DTESN results
            if not hasattr(individual, 'dtesn_data'):
                individual.dtesn_data = {}
            
            individual.dtesn_data.update(dtesn_results)
            
            # Optionally modify fitness based on DTESN results
            if 'membrane_state' in dtesn_results:
                membrane_complexity = dtesn_results['membrane_state'].get('membrane_count', 1)
                # Reward moderate complexity
                complexity_bonus = 1.0 - abs(membrane_complexity - 5) / 10.0
                individual.fitness *= max(0.5, complexity_bonus)
            
            return individual
            
        except Exception as e:
            logger.error(f"Error updating individual with DTESN feedback: {e}")
            return individual
    
    def get_dtesn_statistics(self) -> Dict[str, Any]:
        """Get statistics about DTESN integration."""
        if not self._initialized:
            return {'status': 'not_initialized'}
        
        stats = {
            'status': 'initialized',
            'components': {
                'membrane_system': self.membrane_system is not None,
                'reservoir': self.reservoir is not None,
                'b_series_calculator': self.b_series_calculator is not None
            }
        }
        
        # Add component-specific stats if available
        if self.reservoir and hasattr(self.reservoir, 'get_stats'):
            stats['reservoir_stats'] = self.reservoir.get_stats()
        
        return stats