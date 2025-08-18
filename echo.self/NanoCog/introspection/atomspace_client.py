#!/usr/bin/env python3
"""
AtomSpace Client for NanoCog Introspection

This module provides a robust client for connecting to an AtomSpace via its REST API,
enabling introspective diagnostics of CogPrime-based systems. It includes methods for
querying various aspects of the system, pattern analysis, and cognitive state summarization.

Usage:
    client = AtomSpaceClient("http://localhost:8080/api/v1")
    if client.test_connection():
        summary = client.get_cognitive_state_summary()
        print(summary)
"""

import os
import time
import json
import re
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from collections import defaultdict, Counter

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nanocog.atomspace_client")

class AtomSpaceClient:
    """
    Client for connecting to and analyzing an AtomSpace via REST API.
    
    This client provides methods for querying the AtomSpace, analyzing patterns,
    and summarizing the cognitive state of a CogPrime-based system.
    """
    
    def __init__(self, 
                 endpoint: str, 
                 auth_token: Optional[str] = None,
                 timeout: int = 10,
                 max_retries: int = 3):
        """
                 Initializes an AtomSpaceClient for interacting with an AtomSpace REST API.
                 
                 Configures the client with the specified API endpoint, optional authentication token, request timeout, and HTTP retry strategy. Sets up a persistent session with appropriate headers for JSON communication and authorization if provided.
                 """
        self.endpoint = endpoint.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        
        # Set up session with retry capability
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set up headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    def test_connection(self) -> bool:
        """
        Checks connectivity to the AtomSpace REST API endpoint.
        
        Returns:
            True if the connection to the AtomSpace is successful; False otherwise.
        """
        try:
            response = self.session.get(
                f"{self.endpoint}/status",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info(f"Successfully connected to AtomSpace at {self.endpoint}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to AtomSpace at {self.endpoint}: {str(e)}")
            return False
    
    def _make_request(self, 
                      method: str, 
                      path: str, 
                      params: Optional[Dict[str, Any]] = None,
                      data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
                      Performs an HTTP request to the AtomSpace API and returns the parsed response.
                      
                      Args:
                          method: The HTTP method to use ("GET", "POST", "PUT", or "DELETE").
                          path: The API path relative to the AtomSpace endpoint.
                          params: Optional query parameters to include in the request.
                          data: Optional JSON body to include in the request.
                      
                      Returns:
                          The response data parsed as a dictionary. If the response is not valid JSON, returns a dictionary with the raw response text.
                      
                      Raises:
                          requests.exceptions.RequestException: If the HTTP request fails or an unsupported method is specified.
                      """
        url = f"{self.endpoint}/{path.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(
                    url, 
                    headers=self.headers, 
                    params=params, 
                    timeout=self.timeout
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    url, 
                    headers=self.headers, 
                    params=params, 
                    json=data, 
                    timeout=self.timeout
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    url, 
                    headers=self.headers, 
                    params=params, 
                    json=data, 
                    timeout=self.timeout
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    url, 
                    headers=self.headers, 
                    params=params, 
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Try to parse as JSON, but handle non-JSON responses
            try:
                return response.json()
            except ValueError:
                return {"text": response.text}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {url} failed: {str(e)}")
            raise
    
    # --- Basic AtomSpace Queries ---
    
    def get_atom_count(self) -> int:
        """
        Retrieves the total number of atoms present in the AtomSpace.
        
        Returns:
            The total atom count, or 0 if the request fails.
        """
        try:
            response = self._make_request("GET", "atoms/count")
            return response.get("count", 0)
        except requests.exceptions.RequestException:
            logger.warning("Failed to get atom count, returning 0")
            return 0
    
    def get_atom_types(self) -> List[str]:
        """
        Retrieves the list of all atom types available in the AtomSpace.
        
        Returns:
            A list of atom type names. Returns an empty list if the request fails.
        """
        try:
            response = self._make_request("GET", "types")
            return response.get("types", [])
        except requests.exceptions.RequestException:
            logger.warning("Failed to get atom types, returning empty list")
            return []
    
    def get_atoms_by_type(self, 
                          atom_type: str, 
                          limit: int = 100, 
                          offset: int = 0) -> List[Dict[str, Any]]:
        """
                          Retrieves a list of atoms of the specified type with pagination support.
                          
                          Args:
                              atom_type: The type of atoms to retrieve.
                              limit: Maximum number of atoms to return.
                              offset: Number of atoms to skip for pagination.
                          
                          Returns:
                              A list of atom dictionaries matching the specified type, or an empty list if the request fails.
                          """
        try:
            response = self._make_request(
                "GET", 
                f"atoms/type/{atom_type}", 
                params={"limit": limit, "offset": offset}
            )
            return response.get("atoms", [])
        except requests.exceptions.RequestException:
            logger.warning(f"Failed to get atoms of type {atom_type}, returning empty list")
            return []
    
    def get_atom_by_handle(self, handle: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves an atom from the AtomSpace by its unique handle.
        
        Args:
            handle: The unique identifier of the atom to retrieve.
        
        Returns:
            A dictionary representing the atom if found, or None if the atom does not exist or the request fails.
        """
        try:
            response = self._make_request("GET", f"atoms/{handle}")
            return response
        except requests.exceptions.RequestException:
            logger.warning(f"Failed to get atom with handle {handle}")
            return None
    
    def get_incoming_set(self, handle: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves atoms that have outgoing links to the specified atom.
        
        Args:
            handle: The unique identifier of the target atom.
            limit: The maximum number of incoming atoms to retrieve.
        
        Returns:
            A list of atoms that reference the specified atom as an outgoing connection. Returns an empty list if the request fails.
        """
        try:
            response = self._make_request(
                "GET", 
                f"atoms/{handle}/incoming", 
                params={"limit": limit}
            )
            return response.get("atoms", [])
        except requests.exceptions.RequestException:
            logger.warning(f"Failed to get incoming set for atom {handle}, returning empty list")
            return []
    
    def get_outgoing_set(self, handle: str) -> List[Dict[str, Any]]:
        """
        Retrieves the outgoing set of atoms for a specified atom handle.
        
        Args:
            handle: The unique identifier of the atom whose outgoing set is requested.
        
        Returns:
            A list of atoms that are directly connected as outgoing links from the specified atom. Returns an empty list if the request fails or no outgoing atoms are found.
        """
        try:
            response = self._make_request("GET", f"atoms/{handle}/outgoing")
            return response.get("atoms", [])
        except requests.exceptions.RequestException:
            logger.warning(f"Failed to get outgoing set for atom {handle}, returning empty list")
            return []
    
    # --- Attention and STI/LTI Queries ---
    
    def get_atoms_by_sti(self, 
                         min_sti: float = 0.5, 
                         max_sti: Optional[float] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
                         Retrieves atoms whose Short-Term Importance (STI) values fall within a specified range.
                         
                         Args:
                             min_sti: The minimum STI value to filter atoms.
                             max_sti: The maximum STI value to filter atoms (if provided).
                             limit: The maximum number of atoms to retrieve.
                         
                         Returns:
                             A list of atom dictionaries matching the STI criteria, or an empty list if the request fails.
                         """
        params = {"min_sti": min_sti, "limit": limit}
        if max_sti is not None:
            params["max_sti"] = max_sti
            
        try:
            response = self._make_request("GET", "atoms/sti", params=params)
            return response.get("atoms", [])
        except requests.exceptions.RequestException:
            logger.warning(f"Failed to get atoms by STI, returning empty list")
            return []
    
    def get_atoms_by_lti(self, 
                         min_lti: float = 0.5, 
                         max_lti: Optional[float] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
                         Retrieves atoms whose Long-Term Importance (LTI) values fall within a specified range.
                         
                         Args:
                             min_lti: The minimum LTI value to filter atoms.
                             max_lti: The maximum LTI value to filter atoms (optional).
                             limit: The maximum number of atoms to retrieve.
                         
                         Returns:
                             A list of atom dictionaries matching the LTI criteria. Returns an empty list if the request fails.
                         """
        params = {"min_lti": min_lti, "limit": limit}
        if max_lti is not None:
            params["max_lti"] = max_lti
            
        try:
            response = self._make_request("GET", "atoms/lti", params=params)
            return response.get("atoms", [])
        except requests.exceptions.RequestException:
            logger.warning(f"Failed to get atoms by LTI, returning empty list")
            return []
    
    def get_attention_statistics(self) -> Dict[str, Any]:
        """
        Retrieves attention allocation statistics from the AtomSpace.
        
        Returns:
            A dictionary containing attention statistics, or an empty dictionary if the request fails.
        """
        try:
            response = self._make_request("GET", "attention/statistics")
            return response
        except requests.exceptions.RequestException:
            logger.warning("Failed to get attention statistics, returning empty dict")
            return {}
    
    # --- Goal System Queries ---
    
    def get_active_goals(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieves a list of currently active goals in the AtomSpace system.
        
        Args:
            limit: The maximum number of active goals to retrieve.
        
        Returns:
            A list of dictionaries representing active goals. Returns an empty list if the request fails.
        """
        try:
            response = self._make_request("GET", "goals/active", params={"limit": limit})
            return response.get("goals", [])
        except requests.exceptions.RequestException:
            logger.warning("Failed to get active goals, returning empty list")
            return []
    
    def get_goal_hierarchy(self, goal_handle: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves the goal hierarchy from the AtomSpace, optionally rooted at a specified goal.
        
        Args:
            goal_handle: The handle of the root goal to start the hierarchy from, if provided.
        
        Returns:
            A dictionary representing the goal hierarchy, or an empty dictionary if retrieval fails.
        """
        try:
            params = {}
            if goal_handle:
                params["root"] = goal_handle
                
            response = self._make_request("GET", "goals/hierarchy", params=params)
            return response
        except requests.exceptions.RequestException:
            logger.warning("Failed to get goal hierarchy, returning empty dict")
            return {}
    
    # --- Pattern Mining and Analysis ---
    
    def get_frequent_patterns(self, 
                              min_support: float = 0.1, 
                              max_patterns: int = 20) -> List[Dict[str, Any]]:
        """
                              Retrieves frequent patterns from the AtomSpace that meet a minimum support threshold.
                              
                              Args:
                                  min_support: The minimum support value a pattern must have to be included.
                                  max_patterns: The maximum number of patterns to return.
                              
                              Returns:
                                  A list of dictionaries representing frequent patterns, or an empty list if the request fails.
                              """
        try:
            response = self._make_request(
                "GET", 
                "patterns/frequent", 
                params={"min_support": min_support, "max_patterns": max_patterns}
            )
            return response.get("patterns", [])
        except requests.exceptions.RequestException:
            logger.warning("Failed to get frequent patterns, returning empty list")
            return []
    
    def get_surprising_patterns(self, 
                                max_patterns: int = 20) -> List[Dict[str, Any]]:
        """
                                Retrieves surprising patterns from the AtomSpace, prioritizing those with low probability but high significance.
                                
                                Args:
                                    max_patterns: The maximum number of patterns to retrieve.
                                
                                Returns:
                                    A list of dictionaries representing surprising patterns. Returns an empty list if the request fails.
                                """
        try:
            response = self._make_request(
                "GET", 
                "patterns/surprising", 
                params={"max_patterns": max_patterns}
            )
            return response.get("patterns", [])
        except requests.exceptions.RequestException:
            logger.warning("Failed to get surprising patterns, returning empty list")
            return []
    
    def analyze_atom_distribution(self) -> Dict[str, Any]:
        """
        Analyzes the distribution of atoms by type in the AtomSpace.
        
        Returns:
            A dictionary containing the total atom count, counts and percentages for each atom type, and a list of atom types sorted by count in descending order.
        """
        try:
            # Get all atom types
            atom_types = self.get_atom_types()
            
            # Count atoms of each type
            type_counts = {}
            for atom_type in atom_types:
                try:
                    count_response = self._make_request(
                        "GET", 
                        f"atoms/type/{atom_type}/count"
                    )
                    type_counts[atom_type] = count_response.get("count", 0)
                except requests.exceptions.RequestException:
                    type_counts[atom_type] = 0
            
            # Calculate percentages
            total_atoms = sum(type_counts.values())
            type_percentages = {
                atom_type: (count / total_atoms * 100) if total_atoms > 0 else 0
                for atom_type, count in type_counts.items()
            }
            
            # Sort by count (descending)
            sorted_types = sorted(
                type_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            return {
                "total_atoms": total_atoms,
                "type_counts": type_counts,
                "type_percentages": type_percentages,
                "sorted_types": sorted_types
            }
        except Exception as e:
            logger.error(f"Failed to analyze atom distribution: {str(e)}")
            return {
                "total_atoms": 0,
                "type_counts": {},
                "type_percentages": {},
                "sorted_types": []
            }
    
    def analyze_attention_distribution(self) -> Dict[str, Any]:
        """
        Analyzes the distribution of attention (STI/LTI) across atoms in the AtomSpace.
        
        Returns:
            A dictionary containing overall attention statistics, counts of high STI atoms by type,
            and the distribution of atoms across predefined STI ranges.
        """
        try:
            # Get attention statistics
            stats = self.get_attention_statistics()
            
            # Get high STI atoms for more detailed analysis
            high_sti_atoms = self.get_atoms_by_sti(min_sti=0.5, limit=200)
            
            # Count high STI atoms by type
            high_sti_by_type = defaultdict(int)
            for atom in high_sti_atoms:
                atom_type = atom.get("type", "unknown")
                high_sti_by_type[atom_type] += 1
            
            # Calculate STI distribution
            sti_ranges = {
                "very_high": (0.8, 1.0),
                "high": (0.6, 0.8),
                "medium": (0.4, 0.6),
                "low": (0.2, 0.4),
                "very_low": (0.0, 0.2)
            }
            
            sti_distribution = {}
            for range_name, (min_val, max_val) in sti_ranges.items():
                try:
                    atoms = self.get_atoms_by_sti(min_sti=min_val, max_sti=max_val, limit=1)
                    count_response = self._make_request(
                        "GET", 
                        "atoms/sti/count", 
                        params={"min_sti": min_val, "max_sti": max_val}
                    )
                    sti_distribution[range_name] = count_response.get("count", 0)
                except requests.exceptions.RequestException:
                    sti_distribution[range_name] = 0
            
            return {
                "attention_stats": stats,
                "high_sti_count": len(high_sti_atoms),
                "high_sti_by_type": dict(high_sti_by_type),
                "sti_distribution": sti_distribution
            }
        except Exception as e:
            logger.error(f"Failed to analyze attention distribution: {str(e)}")
            return {
                "attention_stats": {},
                "high_sti_count": 0,
                "high_sti_by_type": {},
                "sti_distribution": {}
            }
    
    def analyze_cognitive_schematics(self, limit: int = 100) -> Dict[str, Any]:
        """
        Analyzes cognitive schematics in the AtomSpace and summarizes their outcomes.
        
        Retrieves up to the specified number of cognitive schematics (Context → Procedure → Goal), counts successful, failed, and unknown statuses, calculates the success rate, groups schematics by goal, and identifies the most common goals.
        
        Args:
            limit: Maximum number of schematics to analyze.
        
        Returns:
            A dictionary containing the total number of schematics, counts of each status, success rate, schematics grouped by goal, and the top goals by schematic count.
        """
        try:
            # Get cognitive schematics
            schematics = self._make_request(
                "GET", 
                "schematics", 
                params={"limit": limit}
            ).get("schematics", [])
            
            # Analyze success rates
            success_counts = {"successful": 0, "failed": 0, "unknown": 0}
            
            for schematic in schematics:
                status = schematic.get("status", "unknown").lower()
                if status == "successful":
                    success_counts["successful"] += 1
                elif status == "failed":
                    success_counts["failed"] += 1
                else:
                    success_counts["unknown"] += 1
            
            # Calculate success rate
            total_known = success_counts["successful"] + success_counts["failed"]
            success_rate = (success_counts["successful"] / total_known * 100) if total_known > 0 else 0
            
            # Group by goal
            schematics_by_goal = defaultdict(list)
            for schematic in schematics:
                goal = schematic.get("goal", {}).get("name", "unknown")
                schematics_by_goal[goal].append(schematic)
            
            # Find most common goals
            goal_counts = {goal: len(schems) for goal, schems in schematics_by_goal.items()}
            sorted_goals = sorted(goal_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "total_schematics": len(schematics),
                "success_counts": success_counts,
                "success_rate": success_rate,
                "schematics_by_goal": {k: len(v) for k, v in schematics_by_goal.items()},
                "top_goals": sorted_goals[:10]
            }
        except Exception as e:
            logger.error(f"Failed to analyze cognitive schematics: {str(e)}")
            return {
                "total_schematics": 0,
                "success_counts": {"successful": 0, "failed": 0, "unknown": 0},
                "success_rate": 0,
                "schematics_by_goal": {},
                "top_goals": []
            }
    
    # --- Comprehensive Analysis and Summaries ---
    
    def get_cognitive_state_summary(self) -> Dict[str, Any]:
        """
        Aggregates and returns a comprehensive summary of the system's cognitive state.
        
        The summary includes timestamp, atom count, active goals, attention and atom distributions, cognitive schematics, and high-level metrics such as goal count, high STI atom count, schematic success rate, and atom type diversity. On error, returns a summary with error details and empty fields.
        
        Returns:
            A dictionary containing cognitive state information and metrics.
        """
        try:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "atom_count": self.get_atom_count(),
                "active_goals": self.get_active_goals(limit=10),
                "attention_distribution": self.analyze_attention_distribution(),
                "atom_distribution": self.analyze_atom_distribution(),
                "cognitive_schematics": self.analyze_cognitive_schematics(limit=50)
            }
            
            # Add high-level metrics
            summary["metrics"] = {
                "goal_count": len(summary["active_goals"]),
                "high_sti_count": summary["attention_distribution"]["high_sti_count"],
                "schematic_success_rate": summary["cognitive_schematics"]["success_rate"],
                "atom_type_diversity": len(summary["atom_distribution"]["type_counts"])
            }
            
            return summary
        except Exception as e:
            logger.error(f"Failed to get cognitive state summary: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "atom_count": 0,
                "active_goals": [],
                "attention_distribution": {},
                "atom_distribution": {},
                "cognitive_schematics": {},
                "metrics": {}
            }
    
    def detect_cognitive_bottlenecks(self) -> List[Dict[str, Any]]:
        """
        Analyzes the cognitive state to identify potential bottlenecks such as attention concentration, goal proliferation, low schematic success rates, and atom type imbalances.
        
        Returns:
            A list of detected bottlenecks, each with type, description, severity, and recommendations. If an error occurs during analysis, returns a single entry describing the error.
        """
        bottlenecks = []
        
        try:
            # Get cognitive state summary
            summary = self.get_cognitive_state_summary()
            
            # Check for attention allocation issues
            attention_dist = summary.get("attention_distribution", {})
            sti_dist = attention_dist.get("sti_distribution", {})
            
            if sti_dist.get("very_high", 0) > 100:
                bottlenecks.append({
                    "type": "attention_concentration",
                    "description": "Too many atoms with very high STI values",
                    "severity": "medium",
                    "count": sti_dist.get("very_high", 0),
                    "recommendation": "Consider increasing ECAN decay rate or adjusting STI spread factors"
                })
            
            # Check for goal proliferation
            goal_count = len(summary.get("active_goals", []))
            if goal_count > 7:
                bottlenecks.append({
                    "type": "goal_proliferation",
                    "description": "Excessive number of active goals",
                    "severity": "high" if goal_count > 15 else "medium",
                    "count": goal_count,
                    "recommendation": "Increase goal selection threshold or implement stricter goal pruning"
                })
            
            # Check for cognitive schematic issues
            schematics = summary.get("cognitive_schematics", {})
            success_rate = schematics.get("success_rate", 0)
            
            if success_rate < 40:
                bottlenecks.append({
                    "type": "low_schematic_success",
                    "description": "Low success rate for cognitive schematics",
                    "severity": "high" if success_rate < 20 else "medium",
                    "rate": success_rate,
                    "recommendation": "Review procedure learning parameters or context definitions"
                })
            
            # Check for atom type imbalance
            atom_dist = summary.get("atom_distribution", {})
            type_percentages = atom_dist.get("type_percentages", {})
            
            # Look for dominant atom types (>50% of one type)
            for atom_type, percentage in type_percentages.items():
                if percentage > 50:
                    bottlenecks.append({
                        "type": "atom_type_imbalance",
                        "description": f"Excessive dominance of {atom_type} atoms",
                        "severity": "medium",
                        "percentage": percentage,
                        "recommendation": "Diversify knowledge representation or adjust creation parameters"
                    })
            
            return bottlenecks
        except Exception as e:
            logger.error(f"Failed to detect cognitive bottlenecks: {str(e)}")
            return [{
                "type": "analysis_error",
                "description": f"Error during bottleneck detection: {str(e)}",
                "severity": "unknown"
            }]
    
    def generate_introspection_report(self, 
                                     include_bottlenecks: bool = True,
                                     include_recommendations: bool = True) -> Dict[str, Any]:
        """
                                     Generates a comprehensive introspection report of the AtomSpace cognitive state.
                                     
                                     The report includes a summary of cognitive metrics, optionally detected bottlenecks and recommendations, and a human-readable summary. Returns a dictionary containing all report components. If an error occurs, returns a dictionary with error details and a summary message.
                                     
                                     Args:
                                         include_bottlenecks: If True, includes detected cognitive bottlenecks in the report.
                                         include_recommendations: If True and bottlenecks are included, adds recommendations for each bottleneck.
                                     
                                     Returns:
                                         A dictionary containing the introspection report, including cognitive state summary, bottlenecks, recommendations, and a human-readable summary. On error, returns a dictionary with error information.
                                     """
        try:
            # Get basic cognitive state
            summary = self.get_cognitive_state_summary()
            
            # Add bottlenecks if requested
            if include_bottlenecks:
                summary["bottlenecks"] = self.detect_cognitive_bottlenecks()
            
            # Add recommendations if requested
            if include_recommendations and include_bottlenecks:
                recommendations = []
                for bottleneck in summary.get("bottlenecks", []):
                    if "recommendation" in bottleneck:
                        recommendations.append({
                            "for_issue": bottleneck["type"],
                            "severity": bottleneck["severity"],
                            "action": bottleneck["recommendation"]
                        })
                
                summary["recommendations"] = recommendations
            
            # Add a human-readable summary
            readable_summary = self._generate_readable_summary(summary)
            summary["readable_summary"] = readable_summary
            
            return summary
        except Exception as e:
            logger.error(f"Failed to generate introspection report: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "readable_summary": "Failed to generate introspection report due to an error."
            }
    
    def _generate_readable_summary(self, summary: Dict[str, Any]) -> str:
        """
        Creates a formatted, human-readable summary string from the provided introspection summary dictionary.
        
        Args:
            summary: The introspection summary data containing atom counts, goals, distributions, schematics, bottlenecks, and recommendations.
        
        Returns:
            A multi-line string summarizing the cognitive state, including atom counts, active goals, attention and atom type distributions, cognitive schematics, detected bottlenecks, and recommendations.
        """
        lines = []
        
        # Basic information
        lines.append(f"AtomSpace Introspection Report ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        lines.append("=" * 50)
        
        # Atom count
        lines.append(f"Total atoms: {summary.get('atom_count', 'unknown')}")
        
        # Active goals
        active_goals = summary.get("active_goals", [])
        lines.append(f"\nActive goals: {len(active_goals)}")
        for i, goal in enumerate(active_goals[:5]):  # Show top 5
            goal_name = goal.get("name", "Unnamed")
            goal_sti = goal.get("sti", 0.0)
            lines.append(f"  {i+1}. {goal_name} (STI: {goal_sti:.2f})")
        
        if len(active_goals) > 5:
            lines.append(f"  ... and {len(active_goals) - 5} more goals")
        
        # Attention distribution
        attention_dist = summary.get("attention_distribution", {})
        sti_dist = attention_dist.get("sti_distribution", {})
        
        if sti_dist:
            lines.append("\nSTI Distribution:")
            for range_name, count in sti_dist.items():
                lines.append(f"  {range_name}: {count} atoms")
        
        # Atom type distribution
        atom_dist = summary.get("atom_distribution", {})
        sorted_types = atom_dist.get("sorted_types", [])
        
        if sorted_types:
            lines.append("\nTop atom types:")
            for atom_type, count in sorted_types[:5]:  # Show top 5
                percentage = atom_dist.get("type_percentages", {}).get(atom_type, 0)
                lines.append(f"  {atom_type}: {count} atoms ({percentage:.1f}%)")
        
        # Cognitive schematics
        schematics = summary.get("cognitive_schematics", {})
        success_rate = schematics.get("success_rate", 0)
        
        lines.append(f"\nCognitive schematics: {schematics.get('total_schematics', 0)} total")
        lines.append(f"  Success rate: {success_rate:.1f}%")
        
        # Top goals with schematics
        top_goals = schematics.get("top_goals", [])
        if top_goals:
            lines.append("  Top goals with schematics:")
            for goal, count in top_goals[:3]:  # Show top 3
                lines.append(f"    {goal}: {count} schematics")
        
        # Bottlenecks
        bottlenecks = summary.get("bottlenecks", [])
        if bottlenecks:
            lines.append("\nDetected bottlenecks:")
            for bottleneck in bottlenecks:
                severity = bottleneck.get("severity", "unknown").upper()
                description = bottleneck.get("description", "Unknown issue")
                lines.append(f"  [{severity}] {description}")
        
        # Recommendations
        recommendations = summary.get("recommendations", [])
        if recommendations:
            lines.append("\nRecommendations:")
            for i, rec in enumerate(recommendations):
                lines.append(f"  {i+1}. {rec.get('action', 'No action specified')}")
        
        return "\n".join(lines)
    
    # --- Mock methods for testing without a real AtomSpace ---
    
    def mock_get_cognitive_state(self) -> Dict[str, Any]:
        """
        Generates randomized mock cognitive state data for testing and development purposes.
        
        Returns:
            A dictionary containing simulated values for atom count, active goals, attention and atom distributions, cognitive schematics, detected bottlenecks, recommendations, and summary metrics.
        """
        import random
        
        # Mock atom count
        atom_count = random.randint(1000, 10000)
        
        # Mock active goals
        active_goals = []
        for i in range(random.randint(3, 8)):
            active_goals.append({
                "handle": f"0x{random.randint(1000, 9999):x}",
                "name": f"Goal{i+1}",
                "type": "ConceptNode",
                "sti": random.uniform(0.5, 0.95),
                "lti": random.uniform(0.1, 0.5),
                "tv": [random.uniform(0.7, 0.99), random.uniform(0.6, 0.9)]
            })
        
        # Mock attention distribution
        attention_distribution = {
            "attention_stats": {
                "avg_sti": random.uniform(0.1, 0.3),
                "max_sti": random.uniform(0.8, 0.99),
                "min_sti": random.uniform(0.01, 0.1),
                "std_dev_sti": random.uniform(0.1, 0.3),
                "avg_lti": random.uniform(0.1, 0.3),
                "max_lti": random.uniform(0.7, 0.9),
                "min_lti": random.uniform(0.01, 0.1)
            },
            "high_sti_count": random.randint(50, 200),
            "high_sti_by_type": {
                "ConceptNode": random.randint(20, 100),
                "PredicateNode": random.randint(10, 50),
                "ListLink": random.randint(5, 30),
                "EvaluationLink": random.randint(10, 40),
                "HebbianLink": random.randint(0, 20)
            },
            "sti_distribution": {
                "very_high": random.randint(10, 50),
                "high": random.randint(50, 150),
                "medium": random.randint(200, 500),
                "low": random.randint(500, 1000),
                "very_low": random.randint(1000, 5000)
            }
        }
        
        # Mock atom distribution
        atom_types = [
            "ConceptNode", "PredicateNode", "ListLink", "EvaluationLink", 
            "HebbianLink", "InheritanceLink", "SchemaNode", "VariableNode",
            "GroundedSchemaNode", "GroundedPredicateNode", "AndLink", "OrLink"
        ]
        
        type_counts = {}
        for atom_type in atom_types:
            type_counts[atom_type] = random.randint(50, 1000)
        
        total_atoms = sum(type_counts.values())
        type_percentages = {
            atom_type: (count / total_atoms * 100)
            for atom_type, count in type_counts.items()
        }
        
        sorted_types = sorted(
            type_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        atom_distribution = {
            "total_atoms": total_atoms,
            "type_counts": type_counts,
            "type_percentages": type_percentages,
            "sorted_types": sorted_types
        }
        
        # Mock cognitive schematics
        schematics = {
            "total_schematics": random.randint(50, 200),
            "success_counts": {
                "successful": random.randint(30, 150),
                "failed": random.randint(10, 50),
                "unknown": random.randint(0, 20)
            },
            "schematics_by_goal": {
                f"Goal{i}": random.randint(5, 30)
                for i in range(1, random.randint(5, 10))
            }
        }
        
        # Calculate success rate
        total_known = schematics["success_counts"]["successful"] + schematics["success_counts"]["failed"]
        success_rate = (schematics["success_counts"]["successful"] / total_known * 100) if total_known > 0 else 0
        schematics["success_rate"] = success_rate
        
        # Sort goals by schematic count
        sorted_goals = sorted(
            schematics["schematics_by_goal"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        schematics["top_goals"] = sorted_goals
        
        # Generate bottlenecks based on the mock data
        bottlenecks = []
        
        # Check for attention concentration
        if attention_distribution["sti_distribution"]["very_high"] > 40:
            bottlenecks.append({
                "type": "attention_concentration",
                "description": "Too many atoms with very high STI values",
                "severity": "medium",
                "count": attention_distribution["sti_distribution"]["very_high"],
                "recommendation": "Consider increasing ECAN decay rate or adjusting STI spread factors"
            })
        
        # Check for goal proliferation
        if len(active_goals) > 7:
            bottlenecks.append({
                "type": "goal_proliferation",
                "description": "Excessive number of active goals",
                "severity": "high" if len(active_goals) > 15 else "medium",
                "count": len(active_goals),
                "recommendation": "Increase goal selection threshold or implement stricter goal pruning"
            })
        
        # Check for cognitive schematic issues
        if success_rate < 40:
            bottlenecks.append({
                "type": "low_schematic_success",
                "description": "Low success rate for cognitive schematics",
                "severity": "high" if success_rate < 20 else "medium",
                "rate": success_rate,
                "recommendation": "Review procedure learning parameters or context definitions"
            })
        
        # Check for atom type imbalance
        for atom_type, percentage in type_percentages.items():
            if percentage > 50:
                bottlenecks.append({
                    "type": "atom_type_imbalance",
                    "description": f"Excessive dominance of {atom_type} atoms",
                    "severity": "medium",
                    "percentage": percentage,
                    "recommendation": "Diversify knowledge representation or adjust creation parameters"
                })
        
        # Generate recommendations
        recommendations = []
        for bottleneck in bottlenecks:
            if "recommendation" in bottleneck:
                recommendations.append({
                    "for_issue": bottleneck["type"],
                    "severity": bottleneck["severity"],
                    "action": bottleneck["recommendation"]
                })
        
        # Assemble the complete mock data
        return {
            "timestamp": datetime.now().isoformat(),
            "atom_count": atom_count,
            "active_goals": active_goals,
            "attention_distribution": attention_distribution,
            "atom_distribution": atom_distribution,
            "cognitive_schematics": schematics,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": {
                "goal_count": len(active_goals),
                "high_sti_count": attention_distribution["high_sti_count"],
                "schematic_success_rate": success_rate,
                "atom_type_diversity": len(atom_distribution["type_counts"])
            }
        }

    # --- Enhanced Evaluation Metrics ---
    
    def evaluate_symbolic_accuracy(self, generated_text: str) -> Dict[str, Any]:
        """
        Evaluate the symbolic accuracy of generated Atomese/Scheme code.
        
        Args:
            generated_text: Generated text containing Atomese/Scheme code
            
        Returns:
            Dictionary containing accuracy metrics
        """
        import re
        
        # Extract Atomese patterns from generated text
        atomese_patterns = re.findall(r'\([A-Za-z][A-Za-z0-9]*Link[^)]*\)', generated_text, re.MULTILINE | re.DOTALL)
        scheme_definitions = re.findall(r'\(define[^)]*\)', generated_text, re.MULTILINE | re.DOTALL)
        
        total_constructs = len(atomese_patterns) + len(scheme_definitions)
        
        if total_constructs == 0:
            return {
                "total_constructs": 0,
                "syntax_correct": 0,
                "syntax_accuracy": 0.0,
                "semantic_coherent": 0,
                "semantic_accuracy": 0.0,
                "patterns_found": []
            }
        
        # Basic syntax validation (simplified)
        syntax_correct = 0
        semantic_coherent = 0
        
        valid_atom_types = {
            'ConceptNode', 'PredicateNode', 'SchemaNode', 'VariableNode', 'NumberNode',
            'ListLink', 'InheritanceLink', 'EvaluationLink', 'ImplicationLink', 
            'AndLink', 'OrLink', 'SequentialLink', 'ExecutionLink', 'BindLink',
            'SatisfactionLink', 'GoalNode', 'StateLink', 'AtTimeLink'
        }
        
        for pattern in atomese_patterns:
            # Check for balanced parentheses
            if pattern.count('(') == pattern.count(')'):
                syntax_correct += 1
                
                # Check for valid atom types
                for atom_type in valid_atom_types:
                    if atom_type in pattern:
                        semantic_coherent += 1
                        break
        
        for definition in scheme_definitions:
            if definition.count('(') == definition.count(')'):
                syntax_correct += 1
                semantic_coherent += 1  # Assume definitions are semantically coherent if syntactically correct
        
        return {
            "total_constructs": total_constructs,
            "syntax_correct": syntax_correct,
            "syntax_accuracy": syntax_correct / total_constructs if total_constructs > 0 else 0.0,
            "semantic_coherent": semantic_coherent,
            "semantic_accuracy": semantic_coherent / total_constructs if total_constructs > 0 else 0.0,
            "patterns_found": atomese_patterns[:5]  # Sample of found patterns
        }
    
    def evaluate_diagnostic_alignment(self, model_predictions: Dict[str, Any], 
                                    actual_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate alignment between model diagnostic predictions and actual AtomSpace state.
        
        Args:
            model_predictions: Model's diagnostic predictions
            actual_state: Actual AtomSpace cognitive state
            
        Returns:
            Dictionary containing alignment metrics
        """
        alignment_score = 0.0
        total_comparisons = 0
        detailed_results = {}
        
        # Compare bottleneck predictions
        if 'predicted_bottlenecks' in model_predictions and 'bottlenecks' in actual_state:
            predicted_types = {b.get('type', '') for b in model_predictions['predicted_bottlenecks']}
            actual_types = {b.get('type', '') for b in actual_state['bottlenecks']}
            
            correct_predictions = len(predicted_types.intersection(actual_types))
            total_predictions = max(len(predicted_types), len(actual_types))
            
            if total_predictions > 0:
                bottleneck_accuracy = correct_predictions / total_predictions
                alignment_score += bottleneck_accuracy
                total_comparisons += 1
                
                detailed_results['bottleneck_detection'] = {
                    'accuracy': bottleneck_accuracy,
                    'predicted': list(predicted_types),
                    'actual': list(actual_types),
                    'correct': list(predicted_types.intersection(actual_types))
                }
        
        # Compare attention pattern recognition
        if 'attention_analysis' in model_predictions and 'attention_distribution' in actual_state:
            pred_attention = model_predictions['attention_analysis']
            actual_attention = actual_state['attention_distribution']
            
            # Compare high STI count predictions
            if 'high_sti_prediction' in pred_attention and 'high_sti_count' in actual_attention:
                pred_high_sti = pred_attention['high_sti_prediction']
                actual_high_sti = actual_attention['high_sti_count']
                
                # Calculate relative accuracy (within 20% tolerance)
                if actual_high_sti > 0:
                    relative_error = abs(pred_high_sti - actual_high_sti) / actual_high_sti
                    attention_accuracy = max(0, 1 - relative_error / 0.2)  # 20% tolerance
                    alignment_score += attention_accuracy
                    total_comparisons += 1
                    
                    detailed_results['attention_pattern_recognition'] = {
                        'accuracy': attention_accuracy,
                        'predicted_high_sti': pred_high_sti,
                        'actual_high_sti': actual_high_sti,
                        'relative_error': relative_error
                    }
        
        # Overall alignment score
        overall_accuracy = alignment_score / total_comparisons if total_comparisons > 0 else 0.0
        
        return {
            "overall_accuracy": overall_accuracy,
            "total_comparisons": total_comparisons,
            "detailed_results": detailed_results,
            "alignment_score": alignment_score
        }
    
    def detect_emergent_patterns(self, generated_samples: List[str], 
                               training_corpus: List[str]) -> Dict[str, Any]:
        """
        Detect emergent patterns in generated samples that are novel compared to training corpus.
        
        Args:
            generated_samples: List of generated text samples
            training_corpus: List of training corpus samples for comparison
            
        Returns:
            Dictionary containing emergent pattern analysis
        """
        import re
        from collections import Counter
        
        # Extract cognitive patterns from generated samples
        generated_patterns = []
        for sample in generated_samples:
            # Extract cognitive schematics (ImplicationLink patterns)
            implications = re.findall(r'\(ImplicationLink[^)]*\)', sample, re.MULTILINE | re.DOTALL)
            generated_patterns.extend(implications)
            
            # Extract attention patterns
            attention_patterns = re.findall(r'\(set-[st]ti![^)]*\)', sample)
            generated_patterns.extend(attention_patterns)
            
            # Extract goal patterns
            goal_patterns = re.findall(r'\(GoalNode[^)]*\)', sample)
            generated_patterns.extend(goal_patterns)
        
        # Extract patterns from training corpus for comparison
        corpus_patterns = []
        for sample in training_corpus[:100]:  # Sample to avoid performance issues
            implications = re.findall(r'\(ImplicationLink[^)]*\)', sample, re.MULTILINE | re.DOTALL)
            corpus_patterns.extend(implications)
            
            attention_patterns = re.findall(r'\(set-[st]ti![^)]*\)', sample)
            corpus_patterns.extend(attention_patterns)
            
            goal_patterns = re.findall(r'\(GoalNode[^)]*\)', sample)
            corpus_patterns.extend(goal_patterns)
        
        # Normalize patterns for comparison (remove specific values, keep structure)
        def normalize_pattern(pattern):
            # Replace specific values with placeholders
            normalized = re.sub(r'"[^"]*"', '"PLACEHOLDER"', pattern)
            normalized = re.sub(r'\d+\.?\d*', 'NUM', normalized)
            return normalized
        
        generated_normalized = [normalize_pattern(p) for p in generated_patterns]
        corpus_normalized = [normalize_pattern(p) for p in corpus_patterns]
        
        # Find novel patterns (appear in generated but not in corpus)
        generated_counter = Counter(generated_normalized)
        corpus_counter = Counter(corpus_normalized)
        
        novel_patterns = []
        for pattern, count in generated_counter.items():
            if pattern not in corpus_counter:
                novel_patterns.append((pattern, count))
        
        # Calculate novelty metrics
        total_generated = len(generated_patterns)
        novel_count = sum(count for _, count in novel_patterns)
        novelty_rate = novel_count / total_generated if total_generated > 0 else 0.0
        
        # Identify most frequent novel patterns
        novel_patterns.sort(key=lambda x: x[1], reverse=True)
        top_novel = novel_patterns[:10]
        
        return {
            "total_generated_patterns": total_generated,
            "novel_pattern_count": novel_count,
            "novelty_rate": novelty_rate,
            "pattern_diversity": len(set(generated_normalized)),
            "top_novel_patterns": [{"pattern": p, "frequency": f} for p, f in top_novel],
            "emergent_creativity_score": min(1.0, novelty_rate * 2)  # Scale to 0-1
        }
    
    def analyze_cross_domain_integration(self, generated_text: str) -> Dict[str, Any]:
        """
        Analyze the model's ability to integrate concepts from different cognitive domains.
        
        Args:
            generated_text: Generated text to analyze
            
        Returns:
            Dictionary containing cross-domain integration metrics
        """
        # Define cognitive domain keywords
        cognitive_domains = {
            'attention': ['sti', 'lti', 'attention', 'focus', 'ecan', 'stimulate'],
            'reasoning': ['pln', 'inference', 'implication', 'deduction', 'logic', 'conclusion'],
            'learning': ['moses', 'evolve', 'fitness', 'genetic', 'program', 'adapt'],
            'memory': ['storage', 'retrieve', 'recall', 'consolidate', 'episodic', 'semantic'],
            'goals': ['goal', 'objective', 'target', 'achieve', 'satisfy', 'pursuit'],
            'patterns': ['pattern', 'frequent', 'mining', 'association', 'cluster', 'correlation']
        }
        
        # Count domain keywords in generated text
        domain_counts = {}
        text_lower = generated_text.lower()
        
        for domain, keywords in cognitive_domains.items():
            count = sum(text_lower.count(keyword) for keyword in keywords)
            domain_counts[domain] = count
        
        # Calculate integration metrics
        active_domains = sum(1 for count in domain_counts.values() if count > 0)
        total_domain_mentions = sum(domain_counts.values())
        
        # Look for explicit integration patterns (mentions of multiple domains together)
        integration_patterns = []
        
        # Check for sentences that mention multiple domains
        sentences = re.split(r'[.!?]', generated_text)
        multi_domain_sentences = 0
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            domains_in_sentence = []
            
            for domain, keywords in cognitive_domains.items():
                if any(keyword in sentence_lower for keyword in keywords):
                    domains_in_sentence.append(domain)
            
            if len(domains_in_sentence) >= 2:
                multi_domain_sentences += 1
                integration_patterns.append({
                    "sentence": sentence.strip()[:100] + "..." if len(sentence) > 100 else sentence.strip(),
                    "domains": domains_in_sentence
                })
        
        # Calculate integration score
        integration_score = 0.0
        if len(sentences) > 0:
            integration_score = multi_domain_sentences / len(sentences)
        
        return {
            "active_domains": active_domains,
            "total_domains": len(cognitive_domains),
            "domain_coverage": active_domains / len(cognitive_domains),
            "domain_counts": domain_counts,
            "multi_domain_sentences": multi_domain_sentences,
            "integration_score": integration_score,
            "integration_examples": integration_patterns[:5],
            "cross_domain_synergy_rating": min(1.0, integration_score * 3)  # Scale to 0-1
        }

# --- Command-line interface for testing ---

def main():
    """
    Runs the command-line interface for AtomSpace introspection and reporting.
    
    Parses command-line arguments to connect to an AtomSpace REST API or generate mock data, produces an introspection report, prints a human-readable summary, and optionally saves the report as JSON.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="AtomSpace Client for NanoCog Introspection")
    parser.add_argument("--endpoint", type=str, help="AtomSpace REST API endpoint")
    parser.add_argument("--auth-token", type=str, help="Authentication token (if required)")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of connecting to an AtomSpace")
    parser.add_argument("--output", type=str, help="Output file for the report (JSON format)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger("nanocog.atomspace_client").setLevel(logging.DEBUG)
    
    if args.mock:
        print("Using mock data (no AtomSpace connection)")
        client = AtomSpaceClient("http://localhost:8080/api/v1")  # Dummy endpoint
        report = client.mock_get_cognitive_state()
    else:
        if not args.endpoint:
            print("Error: AtomSpace endpoint is required when not using mock data")
            parser.print_help()
            return
        
        print(f"Connecting to AtomSpace at {args.endpoint}...")
        client = AtomSpaceClient(args.endpoint, auth_token=args.auth_token)
        
        if not client.test_connection():
            print("Failed to connect to AtomSpace. Use --mock to generate mock data instead.")
            return
        
        print("Generating introspection report...")
        report = client.generate_introspection_report()
    
    # Print readable summary
    if "readable_summary" in report:
        print("\n" + report["readable_summary"])
    
    # Save to file if requested
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to {args.output}")
        except Exception as e:
            print(f"Error saving report to {args.output}: {str(e)}")
    
    print("\nDone.")

if __name__ == "__main__":
    main()
