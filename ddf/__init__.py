#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DDF - Enhanced Docker Compose Tools
====================================

A powerful tool for managing Docker Compose configurations with advanced features
like caching, server mode, backup management, and more.

:copyright: (c) 2025 by Hadi Cahyadi.
:license: MIT, see LICENSE for more details.
"""

from .ddf import (
    DDF,
    EnhancedDDF,
    Usage,
    DDFServer,
    CacheManager,
    CacheConfig,
    CacheBackend,
    BackupManager,
    EnhancedBackupManager,
    EditorManager,
    CACHE,
    CACHE_CONFIG,
    CONFIG,
    validate_service_name,
    safe_subprocess_run,
    cache_with_invalidation,
)

try:
    from .__version__ import version as __version__
except ImportError:
    __version__ = "0.1.0"

__author__ = "Hadi Cahyadi"
__email__ = "cumulus13@gmail.com"
__license__ = "MIT"
__url__ = "https://github.com/cumulus13/ddf"
__description__ = "Enhanced Docker Compose Tools with caching, server mode, and backup management"

__all__ = [
    # Main Classes
    "DDF",
    "EnhancedDDF",
    "Usage",
    
    # Server
    "DDFServer",
    
    # Cache
    "CacheManager",
    "CacheConfig",
    "CacheBackend",
    "CACHE",
    "CACHE_CONFIG",
    
    # Backup
    "BackupManager",
    "EnhancedBackupManager",
    
    # Editor
    "EditorManager",
    
    # Config
    "CONFIG",
    
    # Functions
    "validate_service_name",
    "safe_subprocess_run",
    "cache_with_invalidation",
    
    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
    "__description__",
]