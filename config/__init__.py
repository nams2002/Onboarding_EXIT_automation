"""
Centralized Configuration Management System for HR Automation

This module provides a unified configuration system that eliminates duplication
and ensures consistency across all files and templates.
"""

try:
    from .base import BaseConfig
    from .manager import ConfigManager
    from .environments import get_config
    from .validators import validate_config

    # Initialize the configuration manager
    config_manager = ConfigManager()

    # Get the current configuration based on environment
    config = get_config()

    # Validate configuration on import (only warn, don't fail)
    try:
        validation_errors = validate_config(config)
        if validation_errors:
            import warnings
            warnings.warn(f"Configuration validation errors: {validation_errors}")
    except Exception as e:
        import warnings
        warnings.warn(f"Configuration validation failed: {e}")

    __all__ = [
        'config',
        'config_manager',
        'BaseConfig',
        'get_config',
        'validate_config'
    ]

except ImportError as e:
    # Fallback for when dependencies are not available
    import warnings
    warnings.warn(f"Configuration system not fully available: {e}")
    
    # Create minimal config for backward compatibility
    class MinimalConfig:
        def __init__(self):
            import os
            self.COMPANY_NAME = "Rapid Innovation Pvt. Ltd."
            self.COMPANY_ADDRESS = "Hotel North 39, Junas Wada, near River Bridge, Mandrem, Goa 403524"
            self.DEFAULT_SENDER_EMAIL = "hrms@rapidinnovation.dev"
    
    config = MinimalConfig()
    config_manager = None
    BaseConfig = None
    get_config = None
    validate_config = None
    
    __all__ = ['config']
