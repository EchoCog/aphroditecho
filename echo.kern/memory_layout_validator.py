#!/usr/bin/env python3
"""
DTESN Memory Layout Validation Tools
===================================

This module provides validation tools for Deep Tree Echo State Network (DTESN)
memory layout according to the specifications defined in DTESN-ARCHITECTURE.md.

The DTESN memory layout follows OEIS A000081 rooted tree enumeration for
optimal neuromorphic computing performance with the following address space:

- DTESN Membranes: 0xFFFF880000000000 - 0xFFFFC00000000000
- ESN Reservoirs:  0xFFFFC00000000000 - 0xFFFFE00000000000  
- B-Series Cache:  0xFFFFE00000000000 - 0xFFFFFFFFFFFFFFFF

Usage:
    from memory_layout_validator import DTESNMemoryValidator
    
    validator = DTESNMemoryValidator()
    is_valid, errors = validator.validate_full_layout()
"""

import sys
import os
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum

# Import OEIS A000081 enumerator for mathematical validation
try:
    from oeis_a000081_enumerator import create_enhanced_validator
    _oeis_validator = create_enhanced_validator()
    _HAS_OEIS_VALIDATOR = True
except ImportError:
    _oeis_validator = None
    _HAS_OEIS_VALIDATOR = False


class MemoryRegionType(Enum):
    """Memory region types in DTESN architecture"""
    DTESN_MEMBRANES = "dtesn_membranes"
    ESN_RESERVOIRS = "esn_reservoirs"
    B_SERIES_CACHE = "b_series_cache"
    USER_SPACE = "user_space"
    KERNEL_DIRECT = "kernel_direct"


@dataclass
class MemoryRegion:
    """Represents a memory region in the DTESN address space"""
    name: str
    start_addr: int
    end_addr: int
    region_type: MemoryRegionType
    size_bytes: int = 0
    
    def __post_init__(self):
        if self.size_bytes == 0:
            self.size_bytes = self.end_addr - self.start_addr


@dataclass
class MembraneLevel:
    """Represents a membrane level in the DTESN hierarchy"""
    level: int
    expected_count: int
    base_addr: int
    level_size: int
    individual_size: int = 0
    
    def __post_init__(self):
        if self.individual_size == 0 and self.expected_count > 0:
            self.individual_size = self.level_size // self.expected_count


class DTESNMemoryValidator:
    """
    Validates DTESN memory layout according to architectural specifications
    """
    
    # DTESN Memory Layout Constants (from DTESN-ARCHITECTURE.md)
    DTESN_MEMBRANES_START = 0xFFFF880000000000
    DTESN_MEMBRANES_END   = 0xFFFFC00000000000
    ESN_RESERVOIRS_START  = 0xFFFFC00000000000
    ESN_RESERVOIRS_END    = 0xFFFFE00000000000
    B_SERIES_CACHE_START  = 0xFFFFE00000000000
    B_SERIES_CACHE_END    = 0xFFFFFFFFFFFFFFFF
    
    # User space and kernel constants
    USER_SPACE_START     = 0x0000000000000000
    USER_SPACE_END       = 0x00007FFFFFFFFFFF
    KERNEL_DIRECT_START  = 0xFFFF800000000000
    KERNEL_DIRECT_END    = 0xFFFF880000000000
    
    # Membrane level base addresses (from architecture spec)
    MEMBRANE_LEVEL_ADDRS = {
        0: 0xFFFF880000000000,  # Level 0: 1 membrane
        1: 0xFFFF881000000000,  # Level 1: 1 membrane  
        2: 0xFFFF882000000000,  # Level 2: 2 membranes
        3: 0xFFFF884000000000,  # Level 3: 4 membranes
        4: 0xFFFF890000000000,  # Level 4: 9 membranes
    }
    
    # Performance requirements (from architecture spec)
    MAX_MEMORY_ACCESS_NS = 100  # ≤100ns for DTESN data structure access
    
    def __init__(self):
        """Initialize the DTESN memory layout validator"""
        self.regions = self._define_memory_regions()
        self.membrane_levels = self._define_membrane_levels()
    
    def _define_memory_regions(self) -> List[MemoryRegion]:
        """Define the standard DTESN memory regions"""
        return [
            MemoryRegion(
                "User Space",
                self.USER_SPACE_START,
                self.USER_SPACE_END,
                MemoryRegionType.USER_SPACE
            ),
            MemoryRegion(
                "Kernel Direct Mapping", 
                self.KERNEL_DIRECT_START,
                self.KERNEL_DIRECT_END,
                MemoryRegionType.KERNEL_DIRECT
            ),
            MemoryRegion(
                "DTESN Membranes",
                self.DTESN_MEMBRANES_START,
                self.DTESN_MEMBRANES_END, 
                MemoryRegionType.DTESN_MEMBRANES
            ),
            MemoryRegion(
                "ESN Reservoirs",
                self.ESN_RESERVOIRS_START,
                self.ESN_RESERVOIRS_END,
                MemoryRegionType.ESN_RESERVOIRS
            ),
            MemoryRegion(
                "B-Series Cache",
                self.B_SERIES_CACHE_START,
                self.B_SERIES_CACHE_END,
                MemoryRegionType.B_SERIES_CACHE
            ),
        ]
    
    def _define_membrane_levels(self) -> List[MembraneLevel]:
        """Define membrane levels according to OEIS A000081"""
        levels = []
        
        if _HAS_OEIS_VALIDATOR:
            # Use actual OEIS A000081 values
            for level in range(5):  # Levels 0-4 defined in architecture
                expected_count = _oeis_validator.get_term(level) if level > 0 else 1
                base_addr = self.MEMBRANE_LEVEL_ADDRS.get(level, 0)
                
                # Calculate level size (each level gets 16GB = 0x400000000)
                level_size = 0x400000000
                
                levels.append(MembraneLevel(
                    level=level,
                    expected_count=expected_count,
                    base_addr=base_addr,
                    level_size=level_size
                ))
        else:
            # Fallback to hardcoded OEIS A000081 values
            oeis_values = [1, 1, 1, 2, 4]  # A000081 terms for levels 0-4
            for level, expected_count in enumerate(oeis_values):
                base_addr = self.MEMBRANE_LEVEL_ADDRS.get(level, 0)
                level_size = 0x400000000
                
                levels.append(MembraneLevel(
                    level=level,
                    expected_count=expected_count,
                    base_addr=base_addr,
                    level_size=level_size
                ))
        
        return levels
    
    def validate_address_space_partitioning(self) -> Tuple[bool, List[str]]:
        """
        Validate that memory regions don't overlap and cover the full space
        """
        errors = []
        
        # Sort regions by start address
        sorted_regions = sorted(self.regions, key=lambda r: r.start_addr)
        
        # Check for gaps and overlaps
        for i in range(len(sorted_regions) - 1):
            current = sorted_regions[i]
            next_region = sorted_regions[i + 1]
            
            # Check for overlap
            if current.end_addr > next_region.start_addr:
                errors.append(
                    f"Memory overlap: {current.name} (ends 0x{current.end_addr:016X}) "
                    f"overlaps with {next_region.name} (starts 0x{next_region.start_addr:016X})"
                )
            
            # Check for gaps (except between user space and kernel space)
            elif (current.end_addr < next_region.start_addr and 
                  not (current.region_type == MemoryRegionType.USER_SPACE and 
                       next_region.region_type == MemoryRegionType.KERNEL_DIRECT)):
                gap_size = next_region.start_addr - current.end_addr
                errors.append(
                    f"Memory gap: 0x{gap_size:016X} bytes between {current.name} "
                    f"and {next_region.name}"
                )
        
        return len(errors) == 0, errors
    
    def validate_membrane_hierarchy(self) -> Tuple[bool, List[str]]:
        """
        Validate membrane hierarchy follows OEIS A000081 enumeration
        """
        errors = []
        
        # Check each membrane level
        for membrane_level in self.membrane_levels:
            level = membrane_level.level
            expected_count = membrane_level.expected_count
            base_addr = membrane_level.base_addr
            
            # Validate base address is within DTESN membranes region
            if not (self.DTESN_MEMBRANES_START <= base_addr < self.DTESN_MEMBRANES_END):
                errors.append(
                    f"Membrane level {level} base address 0x{base_addr:016X} "
                    f"is outside DTESN membranes region"
                )
            
            # Validate expected count matches OEIS A000081
            if _HAS_OEIS_VALIDATOR:
                oeis_expected = _oeis_validator.get_term(level) if level > 0 else 1
                if expected_count != oeis_expected:
                    errors.append(
                        f"Membrane level {level} count {expected_count} doesn't match "
                        f"OEIS A000081 expected value {oeis_expected}"
                    )
            
            # Validate individual membrane size is reasonable
            if membrane_level.individual_size == 0:
                errors.append(
                    f"Membrane level {level} has zero individual membrane size"
                )
            elif membrane_level.individual_size < 0x1000000:  # Minimum 16MB per membrane
                errors.append(
                    f"Membrane level {level} individual size "
                    f"0x{membrane_level.individual_size:X} is too small (< 16MB)"
                )
        
        return len(errors) == 0, errors
    
    def validate_alignment_constraints(self) -> Tuple[bool, List[str]]:
        """
        Validate memory alignment constraints for optimal performance
        """
        errors = []
        
        # Only check alignment for DTESN-specific regions and start addresses
        # User space and B-series cache end addresses are naturally not page-aligned
        page_size = 0x1000
        
        for region in self.regions:
            # Always check start address alignment
            if region.start_addr % page_size != 0:
                errors.append(
                    f"Region {region.name} start address 0x{region.start_addr:016X} "
                    f"is not page-aligned (4KB)"
                )
            
            # Only check end address alignment for DTESN-specific regions
            if (region.region_type in [MemoryRegionType.DTESN_MEMBRANES, 
                                       MemoryRegionType.ESN_RESERVOIRS] and
                region.end_addr % page_size != 0):
                errors.append(
                    f"Region {region.name} end address 0x{region.end_addr:016X} "
                    f"is not page-aligned (4KB)"
                )
        
        # Membrane levels should be aligned to larger boundaries for performance
        membrane_alignment = 0x1000000  # 16MB alignment
        
        for membrane_level in self.membrane_levels:
            if membrane_level.base_addr % membrane_alignment != 0:
                errors.append(
                    f"Membrane level {membrane_level.level} base address "
                    f"0x{membrane_level.base_addr:016X} is not aligned to 16MB boundary"
                )
        
        return len(errors) == 0, errors
    
    def validate_size_constraints(self) -> Tuple[bool, List[str]]:
        """
        Validate size constraints for each memory region
        """
        errors = []
        
        # Check minimum sizes for each region type
        min_sizes = {
            MemoryRegionType.DTESN_MEMBRANES: 0x38000000000,  # ~3.5TB minimum
            MemoryRegionType.ESN_RESERVOIRS: 0x20000000000,   # ~2TB minimum  
            MemoryRegionType.B_SERIES_CACHE: 0x20000000000,   # ~2TB minimum
        }
        
        for region in self.regions:
            if region.region_type in min_sizes:
                min_size = min_sizes[region.region_type]
                if region.size_bytes < min_size:
                    errors.append(
                        f"Region {region.name} size 0x{region.size_bytes:X} "
                        f"is below minimum 0x{min_size:X}"
                    )
        
        return len(errors) == 0, errors
    
    def validate_address_ranges(self) -> Tuple[bool, List[str]]:
        """
        Validate that addresses are within valid 64-bit ranges
        """
        errors = []
        
        max_64bit_addr = 0xFFFFFFFFFFFFFFFF
        
        for region in self.regions:
            if region.start_addr > max_64bit_addr:
                errors.append(
                    f"Region {region.name} start address 0x{region.start_addr:016X} "
                    f"exceeds 64-bit address space"
                )
            
            if region.end_addr > max_64bit_addr:
                errors.append(
                    f"Region {region.name} end address 0x{region.end_addr:016X} "
                    f"exceeds 64-bit address space"
                )
            
            if region.start_addr >= region.end_addr:
                errors.append(
                    f"Region {region.name} has invalid address range: "
                    f"start 0x{region.start_addr:016X} >= end 0x{region.end_addr:016X}"
                )
        
        return len(errors) == 0, errors
    
    def validate_full_layout(self) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive validation of the DTESN memory layout
        """
        all_errors = []
        
        # Run all validation checks
        validation_checks = [
            ("Address Space Partitioning", self.validate_address_space_partitioning),
            ("Membrane Hierarchy", self.validate_membrane_hierarchy),
            ("Alignment Constraints", self.validate_alignment_constraints),
            ("Size Constraints", self.validate_size_constraints),
            ("Address Ranges", self.validate_address_ranges),
        ]
        
        for check_name, check_func in validation_checks:
            is_valid, errors = check_func()
            if not is_valid:
                all_errors.extend([f"[{check_name}] {error}" for error in errors])
        
        return len(all_errors) == 0, all_errors
    
    def get_memory_layout_summary(self) -> Dict:
        """
        Generate a summary of the DTESN memory layout
        """
        summary = {
            "total_address_space": "64-bit (0x0000000000000000 - 0xFFFFFFFFFFFFFFFF)",
            "regions": [],
            "membrane_levels": [],
            "validation_status": "unknown"
        }
        
        # Add region information
        for region in self.regions:
            summary["regions"].append({
                "name": region.name,
                "start": f"0x{region.start_addr:016X}",
                "end": f"0x{region.end_addr:016X}", 
                "size_gb": region.size_bytes / (1024**3),
                "type": region.region_type.value
            })
        
        # Add membrane level information
        for level in self.membrane_levels:
            summary["membrane_levels"].append({
                "level": level.level,
                "count": level.expected_count,
                "base_addr": f"0x{level.base_addr:016X}",
                "level_size_gb": level.level_size / (1024**3),
                "individual_size_mb": level.individual_size / (1024**2) if level.individual_size else 0
            })
        
        # Add validation status
        is_valid, errors = self.validate_full_layout()
        summary["validation_status"] = "valid" if is_valid else "invalid"
        if not is_valid:
            summary["validation_errors"] = errors
        
        return summary


def create_memory_validator() -> DTESNMemoryValidator:
    """
    Factory function to create a DTESN memory layout validator
    """
    return DTESNMemoryValidator()


def validate_custom_layout(regions: List[Tuple[str, int, int]]) -> Tuple[bool, List[str]]:
    """
    Validate a custom memory layout configuration
    
    Args:
        regions: List of (name, start_addr, end_addr) tuples
        
    Returns:
        Tuple of (is_valid, error_list)
    """
    errors = []
    
    # Convert to MemoryRegion objects
    memory_regions = []
    for name, start, end in regions:
        memory_regions.append(MemoryRegion(
            name, start, end, MemoryRegionType.USER_SPACE  # Default type
        ))
    
    # Check for overlaps
    sorted_regions = sorted(memory_regions, key=lambda r: r.start_addr)
    for i in range(len(sorted_regions) - 1):
        current = sorted_regions[i]
        next_region = sorted_regions[i + 1]
        
        if current.end_addr > next_region.start_addr:
            errors.append(
                f"Overlap: {current.name} and {next_region.name}"
            )
    
    return len(errors) == 0, errors


if __name__ == "__main__":
    """
    Command-line interface for memory layout validation
    """
    import json
    
    print("DTESN Memory Layout Validation Tool")
    print("=" * 40)
    
    validator = create_memory_validator()
    
    # Generate and display summary
    summary = validator.get_memory_layout_summary()
    print(f"\nValidation Status: {summary['validation_status'].upper()}")
    
    # Show regions
    print(f"\nMemory Regions ({len(summary['regions'])}):")
    for region in summary["regions"]:
        print(f"  {region['name']:20} {region['start']} - {region['end']} "
              f"({region['size_gb']:.1f} GB)")
    
    # Show membrane levels
    print(f"\nMembrane Levels ({len(summary['membrane_levels'])}):")
    for level in summary["membrane_levels"]:
        print(f"  Level {level['level']}: {level['count']:2d} membranes at "
              f"{level['base_addr']} ({level['individual_size_mb']:.1f} MB each)")
    
    # Show validation errors if any
    if "validation_errors" in summary:
        print(f"\nValidation Errors ({len(summary['validation_errors'])}):")
        for error in summary["validation_errors"]:
            print(f"  ❌ {error}")
    else:
        print(f"\n✅ All validation checks passed!")
    
    # Export summary as JSON if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        with open("dtesn_memory_layout.json", "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nMemory layout summary exported to dtesn_memory_layout.json")