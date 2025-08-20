#!/usr/bin/env python3
"""
Launch Deep Tree Echo - Standardized Launcher

Enhanced launcher for Deep Tree Echo system with both original launcher functionality
and standardized Echo component interfaces for integration with the Echo ecosystem.

Original functionality: Command-line launcher for Deep Tree Echo system
New functionality: Standardized Echo component for programmatic integration
"""

import sys
import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

# Import unified launcher for original functionality
try:
    from unified_launcher import UnifiedLauncher, create_config_from_args, create_argument_parser
    UNIFIED_LAUNCHER_AVAILABLE = True
except ImportError:
    UNIFIED_LAUNCHER_AVAILABLE = False
    UnifiedLauncher = None
    create_config_from_args = None
    create_argument_parser = None

# Import standardized Echo components for new interfaces
try:
    from echo_component_base import EchoComponent, EchoConfig, EchoResponse
    ECHO_STANDARDIZED_AVAILABLE = True
except ImportError:
    ECHO_STANDARDIZED_AVAILABLE = False
    EchoComponent = object
    EchoConfig = None
    EchoResponse = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deep-tree-echo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeepTreeEchoLauncherStandardized(EchoComponent):
    """
    Standardized Deep Tree Echo launcher component
    
    Provides launcher capabilities with standardized Echo interfaces.
    Inherits from EchoComponent for basic Echo functionality.
    """
    
    def __init__(self, config: EchoConfig):
        if not ECHO_STANDARDIZED_AVAILABLE:
            raise ImportError("Echo standardized components not available")
        
        super().__init__(config)
        
        # Launcher-specific state
        self.unified_launcher = None
        self.launch_history = []
        self.current_launch_config = None
        self.launch_count = 0
    
    def initialize(self) -> EchoResponse:
        """Initialize the Deep Tree Echo launcher"""
        try:
            if not UNIFIED_LAUNCHER_AVAILABLE:
                return EchoResponse(
                    success=False,
                    message="UnifiedLauncher not available - required for launcher functionality",
                    metadata={'error': 'missing_dependency'}
                )
            
            self.unified_launcher = UnifiedLauncher()
            self._initialized = True
            
            self.logger.info("Deep Tree Echo launcher initialized successfully")
            
            return EchoResponse(
                success=True,
                message="Deep Tree Echo launcher initialized",
                data={
                    'unified_launcher_available': True,
                    'launch_count': self.launch_count,
                    'log_file': 'deep-tree-echo.log'
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "initialize")
    
    def process(self, input_data: Any, **kwargs) -> EchoResponse:
        """
        Process launcher operations
        
        Supported operations:
        - 'launch': Launch Deep Tree Echo with specified configuration
        - 'create_config': Create configuration from arguments
        - 'get_history': Get launch history
        - 'get_status': Get launcher status
        """
        try:
            if not self._initialized:
                return EchoResponse(
                    success=False,
                    message="Launcher not initialized - call initialize() first"
                )
            
            # Parse input data
            if isinstance(input_data, str):
                operation = input_data
                params = kwargs
            elif isinstance(input_data, dict):
                operation = input_data.get('operation', 'launch')
                params = input_data.get('params', {})
                params.update(kwargs)
            else:
                operation = 'launch'
                params = kwargs
            
            self.logger.info(f"Processing launcher operation: {operation}")
            
            # Route to appropriate operation
            if operation == 'launch':
                return asyncio.run(self._launch_system(**params))
            elif operation == 'create_config':
                return self._create_config(**params)
            elif operation == 'get_history':
                return self._get_launch_history()
            elif operation == 'get_status':
                return self._get_launcher_status()
            else:
                return EchoResponse(
                    success=False,
                    message=f"Unknown operation: {operation}",
                    metadata={'valid_operations': [
                        'launch', 'create_config', 'get_history', 'get_status'
                    ]}
                )
                
        except Exception as e:
            return self.handle_error(e, "process")
    
    def echo(self, data: Any, echo_value: float = 0.0) -> EchoResponse:
        """
        Echo operation for launcher
        
        Returns launcher state with echo characteristics
        """
        try:
            echoed_data = {
                'launcher_state': {
                    'launch_count': self.launch_count,
                    'initialized': self._initialized,
                    'unified_launcher_available': self.unified_launcher is not None
                },
                'recent_launches': self.launch_history[-3:] if self.launch_history else [],
                'echo_value': echo_value,
                'timestamp': datetime.now().isoformat()
            }
            
            return EchoResponse(
                success=True,
                data=echoed_data,
                message=f"Deep Tree Echo launcher echo (value: {echo_value}, launches: {self.launch_count})",
                metadata={
                    'echo_value': echo_value,
                    'launch_count': self.launch_count
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "echo")
    
    async def _launch_system(self, config_name: str = "deep-tree-echo", args_dict: Optional[Dict] = None) -> EchoResponse:
        """Launch the Deep Tree Echo system"""
        try:
            self.launch_count += 1
            launch_start = datetime.now()
            
            # Create config from arguments or use provided config
            if args_dict:
                # Create mock args object from dictionary
                class MockArgs:
                    def __init__(self, args_dict):
                        for key, value in args_dict.items():
                            setattr(self, key, value)
                
                args = MockArgs(args_dict)
                config = create_config_from_args(config_name, args)
            else:
                # Use default configuration
                parser = create_argument_parser(config_name)
                args = parser.parse_args([])  # Parse empty args for defaults
                config = create_config_from_args(config_name, args)
            
            self.current_launch_config = config
            
            # Launch the system
            self.logger.info(f"Launching Deep Tree Echo system (launch #{self.launch_count})")
            result = await self.unified_launcher.launch_async(config)
            
            launch_end = datetime.now()
            launch_duration = (launch_end - launch_start).total_seconds()
            
            # Record launch history
            launch_record = {
                'launch_number': self.launch_count,
                'config_name': config_name,
                'start_time': launch_start.isoformat(),
                'end_time': launch_end.isoformat(),
                'duration_seconds': launch_duration,
                'result': result,
                'success': result == 0 if isinstance(result, int) else bool(result)
            }
            
            self.launch_history.append(launch_record)
            
            return EchoResponse(
                success=launch_record['success'],
                data={
                    'launch_record': launch_record,
                    'config_used': str(config),
                    'total_launches': self.launch_count
                },
                message=f"Launch #{self.launch_count} completed {'successfully' if launch_record['success'] else 'with errors'}",
                metadata={
                    'launch_number': self.launch_count,
                    'duration_seconds': launch_duration
                }
            )
            
        except Exception as e:
            return self.handle_error(e, f"launch_{self.launch_count}")
    
    def _create_config(self, config_name: str = "deep-tree-echo", args_dict: Optional[Dict] = None) -> EchoResponse:
        """Create configuration from arguments"""
        try:
            if args_dict:
                class MockArgs:
                    def __init__(self, args_dict):
                        for key, value in args_dict.items():
                            setattr(self, key, value)
                
                args = MockArgs(args_dict)
            else:
                parser = create_argument_parser(config_name)
                args = parser.parse_args([])
            
            config = create_config_from_args(config_name, args)
            
            return EchoResponse(
                success=True,
                data={
                    'config': str(config),
                    'config_name': config_name,
                    'args_provided': args_dict is not None
                },
                message="Configuration created successfully"
            )
            
        except Exception as e:
            return self.handle_error(e, "create_config")
    
    def _get_launch_history(self) -> EchoResponse:
        """Get launch history"""
        try:
            return EchoResponse(
                success=True,
                data={
                    'launch_history': self.launch_history,
                    'total_launches': self.launch_count,
                    'successful_launches': sum(1 for launch in self.launch_history if launch['success']),
                    'failed_launches': sum(1 for launch in self.launch_history if not launch['success'])
                },
                message=f"Launch history retrieved: {self.launch_count} total launches"
            )
            
        except Exception as e:
            return self.handle_error(e, "get_history")
    
    def _get_launcher_status(self) -> EchoResponse:
        """Get detailed launcher status"""
        try:
            status = {
                'initialized': self._initialized,
                'unified_launcher_available': self.unified_launcher is not None,
                'launch_count': self.launch_count,
                'current_config': str(self.current_launch_config) if self.current_launch_config else None,
                'log_file': 'deep-tree-echo.log',
                'component_info': {
                    'name': self.config.component_name,
                    'version': self.config.version,
                    'debug_mode': self.config.debug_mode
                }
            }
            
            return EchoResponse(
                success=True,
                data=status,
                message="Launcher status retrieved"
            )
            
        except Exception as e:
            return self.handle_error(e, "get_status")


# Original functions - maintained for backward compatibility
async def main():
    """Main entry point for Deep Tree Echo - original functionality"""
    if not UNIFIED_LAUNCHER_AVAILABLE:
        logger.error("UnifiedLauncher not available - cannot launch Deep Tree Echo")
        return 1
    
    # Parse arguments using unified launcher's parser
    parser = create_argument_parser("deep-tree-echo")
    args = parser.parse_args()
    
    # Create config from arguments
    config = create_config_from_args("deep-tree-echo", args)
    
    # Use unified launcher
    launcher = UnifiedLauncher()
    return await launcher.launch_async(config)


# Factory function for creating standardized launcher
def create_deep_tree_echo_launcher() -> DeepTreeEchoLauncherStandardized:
    """Create a standardized Deep Tree Echo launcher"""
    if not ECHO_STANDARDIZED_AVAILABLE:
        raise ImportError("Echo standardized components not available")
    
    config = EchoConfig(
        component_name="DeepTreeEchoLauncher",
        version="1.0.0",
        debug_mode=False
    )
    
    launcher = DeepTreeEchoLauncherStandardized(config)
    result = launcher.initialize()
    
    if not result.success:
        raise RuntimeError(f"Failed to initialize Deep Tree Echo launcher: {result.message}")
    
    return launcher


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nShutdown initiated by keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

