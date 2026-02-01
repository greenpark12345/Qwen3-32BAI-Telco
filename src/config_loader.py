#!/usr/bin/env python3
"""
Configuration File Loader
Reads configuration parameters from config.txt
"""

import os
from pathlib import Path


def load_config(config_path=None):
    """
    Load configuration file
    
    Args:
        config_path: Path to config file, defaults to config.txt in current directory
        
    Returns:
        dict: Configuration dictionary
    """
    if config_path is None:
        # Search order: current directory -> script directory -> parent directory
        possible_paths = [
            Path('config.txt'),
            Path(__file__).parent / 'config.txt',
            Path(__file__).parent.parent / 'config.txt',
        ]
        for p in possible_paths:
            if p.exists():
                config_path = p
                break
    
    if config_path is None or not Path(config_path).exists():
        raise FileNotFoundError(
            "Configuration file config.txt not found!\n"
            "Please ensure config.txt exists in the current or program directory."
        )
    
    config = {
        # Default values
        'OPENROUTER_API_KEY': '',
        'MODEL': 'qwen/qwen3-32b',
        'API_URL': 'https://openrouter.ai/api/v1/chat/completions',
        'MAX_WORKERS': 8,
        'OUTPUT_DIR': 'output',
        'TEST_FILE': 'phase_2_test.csv',
        # Optional case library files
        'TRAIN_FILE': '',
        'CASE_FILE': '',
    }
    
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse key = value format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Type conversion
                if key == 'MAX_WORKERS':
                    value = int(value)
                
                config[key] = value
    
    # Validate required configuration
    if not config['OPENROUTER_API_KEY']:
        raise ValueError("Missing OPENROUTER_API_KEY in configuration file!")
    
    return config


def get_config():
    """Get global configuration singleton"""
    if not hasattr(get_config, '_config'):
        get_config._config = load_config()
    return get_config._config


if __name__ == '__main__':
    # Test configuration loading
    try:
        config = load_config()
        print("Configuration loaded successfully!")
        print(f"  MODEL: {config['MODEL']}")
        print(f"  MAX_WORKERS: {config['MAX_WORKERS']}")
        print(f"  TEST_FILE: {config['TEST_FILE']}")
        print(f"  API_KEY: {config['OPENROUTER_API_KEY'][:20]}...")
    except Exception as e:
        print(f"Configuration loading failed: {e}")
