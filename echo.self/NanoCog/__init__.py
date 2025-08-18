"""
NanoCog: CogPrime-Aware AI Assistant

A lightweight, GPT-based assistant fine-tuned on CogPrime architecture
and OpenCog implementation details. NanoCog provides:

1. Conversational help with CogPrime theory and OpenCog internals
2. Introspective diagnostics for live CogPrime/OpenCog agents
3. Code generation and refactoring for Atomese/Scheme/MeTTa

The package includes:
- Data preparation tools for training on CogPrime corpus
- FastAPI server for hosting the assistant
- CLI interface for interactive chat and diagnostics
- AtomSpace client for introspective analysis

For more information, see the README.md file.
"""

__version__ = "0.1.0"

# Import key components for easier access
try:
    from .server import ModelConfig as ServerModelConfig
    from .server import app as server_app
    from .nctalk import ModelConfig as CLIModelConfig
    from .nctalk import NanoCogCLI
    from .introspection.atomspace_client import AtomSpaceClient
except ImportError:
    # Handle the case where the modules aren't available yet
    # This allows the package to be imported even if some dependencies are missing
    pass

# Convenience functions
def create_server(model_path, device="cuda", port=8080, host="0.0.0.0"):
    """
    Create and configure a NanoCog server.
    
    Args:
        model_path: Path to the trained model checkpoint
        device: Device to run the model on (cuda, cpu, mps)
        port: Port to run the server on
        host: Host to bind the server to
        
    Returns:
        Configured FastAPI app
    """
    import sys
    import os
    from .server import app, ModelConfig
    
    # Create and load model
    model_config = ModelConfig(model_path, device)
    app.state.model_config = model_config
    
    return app, {"host": host, "port": port}

def start_cli(model_path, device="cuda"):
    """
    Start the NanoCog CLI interface.
    
    Args:
        model_path: Path to the trained model checkpoint
        device: Device to run the model on (cuda, cpu, mps)
    """
    from .nctalk import ModelConfig, NanoCogCLI
    
    # Create and load model
    model_config = ModelConfig(model_path, device)
    model_config.load_model()
    
    # Create and run CLI
    cli = NanoCogCLI(model_config)
    cli.run()
