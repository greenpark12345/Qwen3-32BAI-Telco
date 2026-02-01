#!/usr/bin/env python3
"""
5G Network Problem Diagnosis Solver
Main Entry Program
"""

import sys
import os

# Add current directory and src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))


def print_banner():
    """Print program banner"""
    banner = """
+================================================================+
|         5G Network Problem Diagnosis Solver v1.0               |
+================================================================+
|  Features:                                                     |
|  - Rule-based diagnosis for standard questions                 |
|  - AI-assisted analysis for non-standard questions             |
|  - Checkpoint resume support                                   |
+================================================================+
"""
    print(banner)


def check_files():
    """Check if necessary files exist"""
    from pathlib import Path
    
    # Required files
    required_files = ['config.txt']
    
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        print("Error: Missing required files:")
        for f in missing:
            print(f"  - {f}")
        return False
    
    # Check test data file
    try:
        from src.config_loader import load_config
        config = load_config()
        test_file = config.get('TEST_FILE', 'phase_2_test.csv')
        if not Path(test_file).exists():
            print(f"Error: Test data file not found: {test_file}")
            return False
    except Exception as e:
        print(f"Error: Configuration loading failed: {e}")
        return False
    
    return True


def main():
    """Main function"""
    print_banner()
    
    # Check files
    if not check_files():
        sys.exit(1)
    
    print("Starting solver...")
    print("-" * 60)
    
    try:
        from src.solver import main as solver_main
        solver_main()
    except KeyboardInterrupt:
        print("\n\nUser interrupted, progress saved")
    except Exception as e:
        print(f"\nProgram exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Program execution completed")


if __name__ == '__main__':
    main()
