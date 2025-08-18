"""
NanoCog Introspection Module

This module provides tools for introspective diagnostics of CogPrime-based systems.
It includes clients for connecting to AtomSpace instances, analyzing cognitive states,
detecting bottlenecks, and generating recommendations based on CogPrime principles.

The main component is the AtomSpaceClient, which connects to an AtomSpace REST API
and provides methods for querying and analyzing the cognitive state of the system.

Example usage:
    from nanocog.introspection import AtomSpaceClient
    
    # Connect to an AtomSpace
    client = AtomSpaceClient("http://localhost:8080/api/v1")
    
    # Get a comprehensive cognitive state summary
    summary = client.get_cognitive_state_summary()
    
    # Detect cognitive bottlenecks
    bottlenecks = client.detect_cognitive_bottlenecks()
    
    # Generate a full introspection report
    report = client.generate_introspection_report()
"""

__version__ = "0.1.0"

# Export key components
from .atomspace_client import AtomSpaceClient

# Convenience functions
def create_mock_data():
    """
    Generate mock cognitive state data for testing or demonstration.
    
    Returns:
        Dictionary with mock cognitive state data
    """
    client = AtomSpaceClient("http://localhost:8080/api/v1")  # Dummy endpoint
    return client.mock_get_cognitive_state()

def analyze_atomspace(endpoint, include_bottlenecks=True, include_recommendations=True):
    """
    Analyze an AtomSpace and generate a comprehensive report.
    
    Args:
        endpoint: The URL of the AtomSpace REST API
        include_bottlenecks: Whether to include bottleneck detection
        include_recommendations: Whether to include recommendations
        
    Returns:
        Dictionary with the complete report, or None if connection fails
    """
    client = AtomSpaceClient(endpoint)
    if not client.test_connection():
        return None
    
    return client.generate_introspection_report(
        include_bottlenecks=include_bottlenecks,
        include_recommendations=include_recommendations
    )
