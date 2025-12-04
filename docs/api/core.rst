Core API
========

This section documents the core DDF classes and functions.

DDF Class
---------

The main class providing Docker Compose file operations.

.. autoclass:: ddf.DDF
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: __init__
   
   Service Operations
   ~~~~~~~~~~~~~~~~~~
   
   .. automethod:: find_service
   .. automethod:: list_service_names
   .. automethod:: get_list_service_names
   .. automethod:: show_service_detail
   
   Port Management
   ~~~~~~~~~~~~~~~
   
   .. automethod:: find_duplicate_port
   .. automethod:: find_port
   .. automethod:: check_duplicate_port
   .. automethod:: list_service_ports
   
   Volume Management
   ~~~~~~~~~~~~~~~~~
   
   .. automethod:: list_service_volumes
   .. automethod:: list_volumes
   
   Device Management
   ~~~~~~~~~~~~~~~~~
   
   .. automethod:: list_service_devices
   
   Hostname Management
   ~~~~~~~~~~~~~~~~~~~
   
   .. automethod:: list_hostnames
   
   File Operations
   ~~~~~~~~~~~~~~~
   
   .. automethod:: open_file
   .. automethod:: get_content
   
   Dockerfile Operations
   ~~~~~~~~~~~~~~~~~~~~~
   
   .. automethod:: get_dockerfile
   .. automethod:: read_dockerfile
   .. automethod:: edit_dockerfile
   .. automethod:: copy_dockerfile
   .. automethod:: set_dockerfile
   
   Entrypoint Operations
   ~~~~~~~~~~~~~~~~~~~~~
   
   .. automethod:: read_entrypoint
   .. automethod:: edit_entrypoint
   
   Service Editing
   ~~~~~~~~~~~~~~~
   
   .. automethod:: edit_service
   .. automethod:: edit_file
   .. automethod:: read_file
   
   Service Management
   ~~~~~~~~~~~~~~~~~~
   
   .. automethod:: new_service
   .. automethod:: copy_service
   .. automethod:: rename_service
   .. automethod:: duplicate_server
   .. automethod:: remove_service
   .. automethod:: copy_dockerfile_config

EnhancedDDF Class
-----------------

Enhanced version with backup and monitoring support.

.. autoclass:: ddf.EnhancedDDF
   :members:
   :undoc-members:
   :show-inheritance:
   
   .. automethod:: edit_service_enhanced
   .. automethod:: edit_dockerfile_enhanced
   .. automethod:: edit_entrypoint_enhanced
   .. automethod:: remove_service_enhanced

Usage Class
-----------

Main CLI interface handler.

.. autoclass:: ddf.Usage
   :members:
   :undoc-members:
   :show-inheritance:
   
   .. automethod:: usage

Utility Functions
-----------------

Helper functions for common operations.

.. autofunction:: ddf.validate_service_name

.. autofunction:: ddf.safe_subprocess_run

.. autofunction:: ddf.safe_file_open

.. autofunction:: ddf.write_hash

.. autofunction:: ddf.get_hash_from_file

.. autofunction:: ddf.compare_hash

Decorators
----------

.. autofunction:: ddf.cache_with_invalidation

   Decorator for caching with smart invalidation.
   
   :param ttl: Time to live in seconds
   :param key_prefix: Prefix for cache key
   :param invalidate_on: List of patterns to invalidate
   :param validation: Function to check if backend changed
   :return: Decorated function

Data Classes
------------

CustomRichHelpFormatter
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ddf.CustomRichHelpFormatter
   :members:
   :undoc-members:
   :show-inheritance:

Constants
---------

.. data:: ddf.CONFIGFILE
   
   Path to the configuration file.

.. data:: ddf.CONFIG
   
   Global configuration object.

.. data:: ddf.CACHE
   
   Global cache manager instance.

.. data:: ddf.CACHE_CONFIG
   
   Global cache configuration.