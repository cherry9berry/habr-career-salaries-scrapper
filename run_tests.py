"""
Script to run all tests with coverage reporting
"""
import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_all_tests():
    """Discover and run all tests"""
    # Create test loader
    loader = unittest.TestLoader()
    
    # Discover tests
    test_suite = loader.discover('tests', pattern='test_*.py')
    
    # Create test runner with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    result = runner.run(test_suite)
    
    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1


def run_unit_tests():
    """Run only unit tests"""
    loader = unittest.TestLoader()
    test_suite = loader.discover('tests/unit', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    return 0 if result.wasSuccessful() else 1


def run_integration_tests():
    """Run only integration tests"""
    loader = unittest.TestLoader()
    test_suite = loader.discover('tests/integration', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for salary scraper")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    args = parser.parse_args()
    
    if args.type == "unit":
        print("Running unit tests...")
        exit_code = run_unit_tests()
    elif args.type == "integration":
        print("Running integration tests...")
        exit_code = run_integration_tests()
    else:
        print("Running all tests...")
        exit_code = run_all_tests()
        
    print(f"\nTests {'PASSED' if exit_code == 0 else 'FAILED'}")
    sys.exit(exit_code) 