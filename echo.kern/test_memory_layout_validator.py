#!/usr/bin/env python3
"""
Test Suite for DTESN Memory Layout Validation Tools
==================================================

This test suite validates the memory layout validation functionality
implemented for the Echo.Kern DTESN system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_layout_validator import (
    DTESNMemoryValidator,
    MemoryRegion,
    MemoryRegionType,
    MembraneLevel,
    create_memory_validator,
    validate_custom_layout
)

def test_memory_validator_creation():
    """Test memory validator can be created and initialized"""
    print("Testing memory validator creation...")
    
    validator = create_memory_validator()
    assert validator is not None, "Should create validator instance"
    assert len(validator.regions) > 0, "Should have memory regions defined"
    assert len(validator.membrane_levels) > 0, "Should have membrane levels defined"
    
    print("✅ Memory validator creation test passed")

def test_memory_regions_definition():
    """Test that memory regions are properly defined"""
    print("Testing memory regions definition...")
    
    validator = create_memory_validator()
    
    # Check that all required regions exist
    region_types = {region.region_type for region in validator.regions}
    required_types = {
        MemoryRegionType.USER_SPACE,
        MemoryRegionType.KERNEL_DIRECT,
        MemoryRegionType.DTESN_MEMBRANES,
        MemoryRegionType.ESN_RESERVOIRS,
        MemoryRegionType.B_SERIES_CACHE
    }
    
    assert required_types.issubset(region_types), f"Missing required region types: {required_types - region_types}"
    
    # Check DTESN membranes region
    dtesn_regions = [r for r in validator.regions if r.region_type == MemoryRegionType.DTESN_MEMBRANES]
    assert len(dtesn_regions) == 1, "Should have exactly one DTESN membranes region"
    
    dtesn_region = dtesn_regions[0]
    assert dtesn_region.start_addr == 0xFFFF880000000000, "DTESN membranes should start at correct address"
    assert dtesn_region.end_addr == 0xFFFFC00000000000, "DTESN membranes should end at correct address"
    
    print("✅ Memory regions definition test passed")

def test_membrane_hierarchy():
    """Test membrane hierarchy follows OEIS A000081"""
    print("Testing membrane hierarchy...")
    
    validator = create_memory_validator()
    
    # Check that we have 5 membrane levels (0-4)
    assert len(validator.membrane_levels) == 5, "Should have 5 membrane levels"
    
    # Check level counts follow OEIS A000081
    expected_counts = [1, 1, 1, 2, 4]  # A000081 for levels 0-4
    actual_counts = [level.expected_count for level in validator.membrane_levels]
    assert actual_counts == expected_counts, f"Membrane counts {actual_counts} don't match OEIS A000081 {expected_counts}"
    
    # Check level addresses are in order
    for i in range(len(validator.membrane_levels) - 1):
        current_level = validator.membrane_levels[i]
        next_level = validator.membrane_levels[i + 1]
        assert current_level.base_addr < next_level.base_addr, f"Level {i} address should be less than level {i+1}"
    
    print("✅ Membrane hierarchy test passed")

def test_address_space_partitioning_validation():
    """Test address space partitioning validation"""
    print("Testing address space partitioning validation...")
    
    validator = create_memory_validator()
    is_valid, errors = validator.validate_address_space_partitioning()
    
    # The default layout should be valid
    assert is_valid, f"Default address space partitioning should be valid. Errors: {errors}"
    
    print("✅ Address space partitioning validation test passed")

def test_membrane_hierarchy_validation():
    """Test membrane hierarchy validation"""
    print("Testing membrane hierarchy validation...")
    
    validator = create_memory_validator()
    is_valid, errors = validator.validate_membrane_hierarchy()
    
    # The default hierarchy should be valid
    assert is_valid, f"Default membrane hierarchy should be valid. Errors: {errors}"
    
    print("✅ Membrane hierarchy validation test passed")

def test_alignment_constraints_validation():
    """Test alignment constraints validation"""
    print("Testing alignment constraints validation...")
    
    validator = create_memory_validator()
    is_valid, errors = validator.validate_alignment_constraints()
    
    # The default layout should meet alignment constraints
    assert is_valid, f"Default layout should meet alignment constraints. Errors: {errors}"
    
    print("✅ Alignment constraints validation test passed")

def test_size_constraints_validation():
    """Test size constraints validation"""
    print("Testing size constraints validation...")
    
    validator = create_memory_validator()
    is_valid, errors = validator.validate_size_constraints()
    
    # The default layout should meet size constraints
    assert is_valid, f"Default layout should meet size constraints. Errors: {errors}"
    
    print("✅ Size constraints validation test passed")

def test_address_ranges_validation():
    """Test address ranges validation"""
    print("Testing address ranges validation...")
    
    validator = create_memory_validator()
    is_valid, errors = validator.validate_address_ranges()
    
    # The default layout should have valid address ranges
    assert is_valid, f"Default layout should have valid address ranges. Errors: {errors}"
    
    print("✅ Address ranges validation test passed")

def test_full_layout_validation():
    """Test comprehensive layout validation"""
    print("Testing full layout validation...")
    
    validator = create_memory_validator()
    is_valid, errors = validator.validate_full_layout()
    
    # The default layout should be fully valid
    assert is_valid, f"Default layout should be fully valid. Errors: {errors}"
    
    print("✅ Full layout validation test passed")

def test_memory_layout_summary():
    """Test memory layout summary generation"""
    print("Testing memory layout summary...")
    
    validator = create_memory_validator()
    summary = validator.get_memory_layout_summary()
    
    # Check summary structure
    required_keys = ["total_address_space", "regions", "membrane_levels", "validation_status"]
    for key in required_keys:
        assert key in summary, f"Summary should contain '{key}'"
    
    # Check regions in summary
    assert len(summary["regions"]) == len(validator.regions), "Summary should include all regions"
    
    # Check membrane levels in summary
    assert len(summary["membrane_levels"]) == len(validator.membrane_levels), "Summary should include all membrane levels"
    
    # Check validation status
    assert summary["validation_status"] in ["valid", "invalid"], "Should have validation status"
    
    print("✅ Memory layout summary test passed")

def test_custom_layout_validation():
    """Test custom layout validation functionality"""
    print("Testing custom layout validation...")
    
    # Test valid custom layout (no overlaps)
    valid_regions = [
        ("Region A", 0x1000, 0x2000),
        ("Region B", 0x2000, 0x3000),
        ("Region C", 0x4000, 0x5000)
    ]
    is_valid, errors = validate_custom_layout(valid_regions)
    assert is_valid, f"Valid custom layout should pass validation. Errors: {errors}"
    
    # Test invalid custom layout (with overlap)
    invalid_regions = [
        ("Region A", 0x1000, 0x2500),  # Overlaps with Region B
        ("Region B", 0x2000, 0x3000),
        ("Region C", 0x4000, 0x5000)
    ]
    is_valid, errors = validate_custom_layout(invalid_regions)
    assert not is_valid, "Invalid custom layout should fail validation"
    assert len(errors) > 0, "Should have validation errors for overlapping regions"
    assert "Overlap" in errors[0], "Should detect overlap error"
    
    print("✅ Custom layout validation test passed")

def test_error_detection():
    """Test that validation properly detects errors"""
    print("Testing error detection...")
    
    # Create a validator with invalid membrane level
    validator = create_memory_validator()
    
    # Manually modify a membrane level to create an error
    validator.membrane_levels[2].expected_count = 999  # Invalid count for level 2
    
    # Validate membrane hierarchy - should fail
    is_valid, errors = validator.validate_membrane_hierarchy()
    assert not is_valid, "Should detect invalid membrane count"
    assert len(errors) > 0, "Should have validation errors"
    
    # Check error message contains relevant information
    error_found = any("count" in error and "999" in error for error in errors)
    assert error_found, f"Should detect count error in: {errors}"
    
    print("✅ Error detection test passed")

def test_performance_constraints():
    """Test performance-related validation"""
    print("Testing performance constraints...")
    
    validator = create_memory_validator()
    
    # Check that the validator has the correct performance constant
    assert validator.MAX_MEMORY_ACCESS_NS == 100, "Should have correct memory access time constraint"
    
    # Check that membrane levels have reasonable individual sizes
    for level in validator.membrane_levels:
        if level.expected_count > 0:
            assert level.individual_size > 0, f"Level {level.level} should have positive individual size"
            # Each membrane should be at least 16MB for reasonable performance
            assert level.individual_size >= 0x1000000, f"Level {level.level} individual size too small"
    
    print("✅ Performance constraints test passed")

def test_oeis_integration():
    """Test integration with OEIS A000081 validator"""
    print("Testing OEIS integration...")
    
    validator = create_memory_validator()
    
    # Test that membrane counts match OEIS A000081 when available
    try:
        from oeis_a000081_enumerator import create_enhanced_validator
        oeis_validator = create_enhanced_validator()
        
        for level in validator.membrane_levels:
            expected_oeis = oeis_validator.get_term(level.level) if level.level > 0 else 1
            assert level.expected_count == expected_oeis, \
                f"Level {level.level} count {level.expected_count} should match OEIS A000081 {expected_oeis}"
        
        print("✅ OEIS integration test passed (enhanced validator available)")
        
    except ImportError:
        # Fallback test with hardcoded values
        expected_counts = [1, 1, 1, 2, 4]
        actual_counts = [level.expected_count for level in validator.membrane_levels]
        assert actual_counts == expected_counts, "Should match hardcoded OEIS A000081 values"
        
        print("✅ OEIS integration test passed (using fallback values)")

def test_memory_constants():
    """Test that memory layout constants are correct"""
    print("Testing memory constants...")
    
    validator = create_memory_validator()
    
    # Test address constants match the architecture specification
    assert validator.DTESN_MEMBRANES_START == 0xFFFF880000000000, "DTESN membranes start address"
    assert validator.DTESN_MEMBRANES_END == 0xFFFFC00000000000, "DTESN membranes end address"
    assert validator.ESN_RESERVOIRS_START == 0xFFFFC00000000000, "ESN reservoirs start address"
    assert validator.ESN_RESERVOIRS_END == 0xFFFFE00000000000, "ESN reservoirs end address"
    assert validator.B_SERIES_CACHE_START == 0xFFFFE00000000000, "B-Series cache start address"
    assert validator.B_SERIES_CACHE_END == 0xFFFFFFFFFFFFFFFF, "B-Series cache end address"
    
    # Test membrane level addresses
    expected_addrs = {
        0: 0xFFFF880000000000,
        1: 0xFFFF881000000000,
        2: 0xFFFF882000000000,
        3: 0xFFFF884000000000,
        4: 0xFFFF890000000000,
    }
    
    for level, expected_addr in expected_addrs.items():
        assert validator.MEMBRANE_LEVEL_ADDRS[level] == expected_addr, \
            f"Membrane level {level} address should be 0x{expected_addr:016X}"
    
    print("✅ Memory constants test passed")

def run_all_tests():
    """Run all memory layout validation tests"""
    print("DTESN Memory Layout Validation Test Suite")
    print("=" * 50)
    
    tests = [
        test_memory_validator_creation,
        test_memory_regions_definition,
        test_membrane_hierarchy,
        test_address_space_partitioning_validation,
        test_membrane_hierarchy_validation,
        test_alignment_constraints_validation,
        test_size_constraints_validation,
        test_address_ranges_validation,
        test_full_layout_validation,
        test_memory_layout_summary,
        test_custom_layout_validation,
        test_error_detection,
        test_performance_constraints,
        test_oeis_integration,
        test_memory_constants
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Memory layout validation tools are working correctly.")
        return True
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)