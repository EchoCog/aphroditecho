"""
Echo Component Base Classes

This module provides the foundational base classes for all Echo system components,
establishing consistent interfaces and common functionality across the ecosystem.

Created as part of the Deep Tree Echo consolidation effort to standardize APIs
and improve system integration.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EchoResponse:
    """Standard response object for Echo operations"""
    success: bool
    data: Any = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EchoConfig:
    """Configuration object for Echo components"""
    component_name: str
    version: str = "1.0.0"
    echo_threshold: float = 0.75
    max_depth: int = 10
    debug_mode: bool = False
    custom_params: Dict[str, Any] = field(default_factory=dict)


class EchoComponent(ABC):
    """
    Abstract base class for all Echo system components.
    
    Provides standardized interface and common functionality for:
    - Initialization and configuration
    - Processing and echo operations
    - Logging and error handling
    - State management
    """
    
    def __init__(self, config: EchoConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.state = {}
        self._initialized = False
        
        self.logger.info(f"Initializing {self.config.component_name} v{self.config.version}")
        
    def _setup_logging(self) -> logging.Logger:
        """Setup component-specific logging"""
        logger = logging.getLogger(f"echo.{self.config.component_name}")
        
        if self.config.debug_mode:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            
        # Avoid duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.config.component_name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    @abstractmethod
    def initialize(self) -> EchoResponse:
        """
        Initialize the component.
        Must be implemented by concrete classes.
        """
        pass
    
    @abstractmethod
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """
        Main processing method for the component.
        Must be implemented by concrete classes.
        """
        pass
    
    @abstractmethod
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """
        Perform echo operation specific to the component.
        Must be implemented by concrete classes.
        """
        pass
    
    def get_status(self) -> EchoResponse:
        """Get current component status"""
        status_data = {
            'component_name': self.config.component_name,
            'version': self.config.version,
            'initialized': self._initialized,
            'state_keys': list(self.state.keys()),
            'config': {
                'echo_threshold': self.config.echo_threshold,
                'max_depth': self.config.max_depth,
                'debug_mode': self.config.debug_mode
            }
        }
        
        return EchoResponse(
            success=True,
            data=status_data,
            message=f"{self.config.component_name} status retrieved"
        )
    
    def reset(self) -> EchoResponse:
        """Reset component to initial state"""
        try:
            self.state.clear()
            self._initialized = False
            self.logger.info(f"{self.config.component_name} reset completed")
            
            return EchoResponse(
                success=True,
                message=f"{self.config.component_name} reset successfully"
            )
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            return EchoResponse(
                success=False,
                message=f"Reset failed: {str(e)}"
            )
    
    def validate_input(self, input_data: Any) -> EchoResponse:
        """Validate input data before processing"""
        if input_data is None:
            return EchoResponse(
                success=False,
                message="Input data cannot be None"
            )
            
        return EchoResponse(
            success=True,
            message="Input validation passed"
        )
    
    def handle_error(self, error: Exception, context: str = "") -> EchoResponse:
        """Standardized error handling"""
        error_msg = f"Error in {context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg, exc_info=True)
        
        return EchoResponse(
            success=False,
            message=error_msg,
            metadata={'error_type': type(error).__name__}
        )


class MemoryEchoComponent(EchoComponent):
    """
    Specialized base class for Echo components that handle memory operations.
    
    Extends EchoComponent with memory-specific functionality.
    """
    
    def __init__(self, config: EchoConfig):
        super().__init__(config)
        self.memory_store = {}
        self.memory_stats = {
            'operations': 0,
            'last_access': None,
            'size': 0
        }
    
    def initialize(self) -> EchoResponse:
        """Initialize memory component"""
        try:
            self._initialized = True
            self.logger.info(f"Memory component {self.config.component_name} initialized")
            return EchoResponse(success=True, message="Memory component initialized")
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """Process data with memory operations"""
        try:
            validation = self.validate_input(input_data)
            if not validation.success:
                return validation
            
            # Default processing: store input data and return it
            key = kwargs.get('memory_key', f"process_{datetime.now().timestamp()}")
            store_result = self.store_memory(key, input_data)
            
            if not store_result.success:
                return store_result
            
            return EchoResponse(
                success=True,
                data=input_data,
                message=f"Data processed and stored in memory: {key}",
                metadata={'memory_key': key}
            )
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """Perform echo operation with memory consideration"""
        try:
            # Default echo: store data with echo value and return augmented data
            key = f"echo_{datetime.now().timestamp()}"
            augmented_data = {
                'original_data': data,
                'echo_value': echo_value,
                'timestamp': datetime.now().isoformat()
            }
            
            store_result = self.store_memory(key, augmented_data)
            if not store_result.success:
                return store_result
            
            return EchoResponse(
                success=True,
                data=augmented_data,
                message=f"Echo operation completed (value: {echo_value})",
                metadata={'memory_key': key, 'echo_value': echo_value}
            )
        except Exception as e:
            return self.handle_error(e, "echo")
    
    def store_memory(self, key: str, data: Any) -> EchoResponse:
        """Store data in memory with tracking"""
        try:
            self.memory_store[key] = data
            self.memory_stats['operations'] += 1
            self.memory_stats['last_access'] = datetime.now()
            self.memory_stats['size'] = len(self.memory_store)
            
            self.logger.debug(f"Stored memory: {key}")
            
            return EchoResponse(
                success=True,
                message=f"Memory stored: {key}",
                metadata={'memory_size': self.memory_stats['size']}
            )
        except Exception as e:
            return self.handle_error(e, "store_memory")
    
    def retrieve_memory(self, key: str) -> EchoResponse:
        """Retrieve data from memory"""
        try:
            if key not in self.memory_store:
                return EchoResponse(
                    success=False,
                    message=f"Memory key not found: {key}"
                )
            
            data = self.memory_store[key]
            self.memory_stats['operations'] += 1
            self.memory_stats['last_access'] = datetime.now()
            
            self.logger.debug(f"Retrieved memory: {key}")
            
            return EchoResponse(
                success=True,
                data=data,
                message=f"Memory retrieved: {key}"
            )
        except Exception as e:
            return self.handle_error(e, "retrieve_memory")
    
    def clear_memory(self) -> EchoResponse:
        """Clear all memory storage"""
        try:
            cleared_count = len(self.memory_store)
            self.memory_store.clear()
            self.memory_stats['size'] = 0
            
            return EchoResponse(
                success=True,
                message=f"Cleared {cleared_count} memory items",
                metadata={'cleared_count': cleared_count}
            )
        except Exception as e:
            return self.handle_error(e, "clear_memory")


class ProcessingEchoComponent(EchoComponent):
    """
    Specialized base class for Echo components that handle data processing.
    
    Extends EchoComponent with processing pipeline functionality.
    """
    
    def __init__(self, config: EchoConfig):
        super().__init__(config)
        self.processing_pipeline = []
        self.processing_stats = {
            'total_processed': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_processing_time': None
        }
    
    def initialize(self) -> EchoResponse:
        """Initialize processing component"""
        try:
            self._initialized = True
            self.logger.info(f"Processing component {self.config.component_name} initialized")
            return EchoResponse(success=True, message="Processing component initialized")
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """Process data through the pipeline"""
        try:
            validation = self.validate_input(input_data)
            if not validation.success:
                return validation
            
            # If no pipeline is defined, return data as-is
            if not self.processing_pipeline:
                return EchoResponse(
                    success=True,
                    data=input_data,
                    message="No processing pipeline defined, returning input data"
                )
            
            # Execute pipeline
            return self.execute_pipeline(input_data)
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """Perform echo operation with processing consideration"""
        try:
            # Default echo: process data and add echo metadata
            process_result = self.process(data)
            
            if not process_result.success:
                return process_result
            
            echoed_data = {
                'processed_data': process_result.data,
                'echo_value': echo_value,
                'processing_metadata': process_result.metadata,
                'timestamp': datetime.now().isoformat()
            }
            
            return EchoResponse(
                success=True,
                data=echoed_data,
                message=f"Echo processing completed (value: {echo_value})",
                metadata={'echo_value': echo_value, 'pipeline_steps': len(self.processing_pipeline)}
            )
        except Exception as e:
            return self.handle_error(e, "echo")
    
    def add_processing_step(self, step_func, step_name: str = None):
        """Add a processing step to the pipeline"""
        step_info = {
            'function': step_func,
            'name': step_name or step_func.__name__,
            'added_at': datetime.now()
        }
        self.processing_pipeline.append(step_info)
        self.logger.info(f"Added processing step: {step_info['name']}")
    
    def execute_pipeline(self, input_data: Any) -> EchoResponse:
        """Execute the full processing pipeline"""
        try:
            current_data = input_data
            start_time = datetime.now()
            
            for step in self.processing_pipeline:
                try:
                    current_data = step['function'](current_data)
                    self.logger.debug(f"Completed step: {step['name']}")
                except Exception as e:
                    self.processing_stats['failed_operations'] += 1
                    return self.handle_error(e, f"processing step: {step['name']}")
            
            # Update stats
            self.processing_stats['total_processed'] += 1
            self.processing_stats['successful_operations'] += 1
            self.processing_stats['last_processing_time'] = datetime.now()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EchoResponse(
                success=True,
                data=current_data,
                message=f"Pipeline executed successfully ({len(self.processing_pipeline)} steps)",
                metadata={
                    'processing_time': processing_time,
                    'steps_executed': len(self.processing_pipeline)
                }
            )
            
        except Exception as e:
            self.processing_stats['failed_operations'] += 1
            return self.handle_error(e, "execute_pipeline")


# Factory function for creating Echo components
def create_echo_component(component_type: str, config: EchoConfig) -> EchoComponent:
    """
    Factory function to create Echo components.
    
    Args:
        component_type: Type of component ('memory', 'processing', 'basic')
        config: Configuration for the component
        
    Returns:
        Appropriate EchoComponent instance
    """
    if component_type == 'memory':
        return MemoryEchoComponent(config)
    elif component_type == 'processing':
        return ProcessingEchoComponent(config)
    else:
        # For basic components, we need a concrete implementation
        class BasicEchoComponent(EchoComponent):
            def initialize(self) -> EchoResponse:
                self._initialized = True
                return EchoResponse(success=True, message="Basic component initialized")
                
            def process(self, input_data: Any, **kwargs) -> EchoResponse:
                return EchoResponse(success=True, data=input_data, message="Basic processing completed")
                
            def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
                return EchoResponse(success=True, data=data, message=f"Echo operation (value: {echo_value})")
        
        return BasicEchoComponent(config)


# Utility functions for working with Echo components
def validate_echo_component(component: Any) -> bool:
    """Validate that an object is a proper Echo component"""
    return isinstance(component, EchoComponent)


def get_echo_component_info(component: EchoComponent) -> Dict[str, Any]:
    """Get comprehensive information about an Echo component"""
    if not validate_echo_component(component):
        raise ValueError("Object is not a valid Echo component")
    
    info = {
        'component_name': component.config.component_name,
        'version': component.config.version,
        'type': type(component).__name__,
        'initialized': component._initialized,
        'has_memory': isinstance(component, MemoryEchoComponent),
        'has_processing': isinstance(component, ProcessingEchoComponent),
        'state_size': len(component.state),
        'config': {
            'echo_threshold': component.config.echo_threshold,
            'max_depth': component.config.max_depth,
            'debug_mode': component.config.debug_mode
        }
    }
    
    # Add memory-specific info
    if isinstance(component, MemoryEchoComponent):
        info['memory_stats'] = component.memory_stats.copy()
    
    # Add processing-specific info
    if isinstance(component, ProcessingEchoComponent):
        info['processing_stats'] = component.processing_stats.copy()
        info['pipeline_steps'] = len(component.processing_pipeline)
    
    return info