Welcome to DDF's documentation!
=================================

**DDF (Docker Docker-compose File)** is an enhanced Docker Compose management tool that provides 
powerful features for working with docker-compose files, including intelligent caching, 
server mode operation, automatic backups, and advanced file editing capabilities.

.. image:: https://img.shields.io/pypi/v/ddf.svg
   :target: https://pypi.python.org/pypi/ddf
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/ddf.svg
   :target: https://pypi.python.org/pypi/ddf
   :alt: Python versions

.. image:: https://img.shields.io/github/license/cumulus13/ddf.svg
   :target: https://github.com/cumulus13/ddf/blob/main/LICENSE
   :alt: License

Key Features
------------

* **Intelligent Caching**: Multiple cache backends (Redis, Memcached, Pickle)
* **Server Mode**: Background server with system tray integration
* **Automatic Backups**: Create and restore backups before editing
* **Advanced Editing**: Support for multiple editors with change detection
* **Port Management**: Find duplicate ports and conflicts
* **Service Management**: Easy service creation, editing, duplication, and removal
* **File Monitoring**: Real-time file change detection
* **Detached Mode**: Open editors in separate terminal windows

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Basic installation
   pip install ddf
   
   # With all optional features
   pip install ddf[all]
   
   # With specific features
   pip install ddf[cache]    # Redis/Memcached support
   pip install ddf[server]   # Server mode with tray icon
   pip install ddf[monitoring]  # File monitoring

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

   # List all services
   ddf -L
   
   # Find duplicate ports
   ddf
   
   # Edit a service
   ddf myservice -E
   
   # Edit Dockerfile
   ddf myservice -e
   
   # Show service details
   ddf myservice -d
   
   # Find port usage
   ddf -f 8080

Server Mode
~~~~~~~~~~~

.. code-block:: bash

   # Start server
   ddf --server-mode &
   
   # Enable in config
   echo "[server]
   active = true" >> ddf.ini
   
   # All editing commands now run through server
   ddf myservice -E

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   configuration
   usage
   server_mode
   caching
   backup

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/cache
   api/server
   api/backup
   api/editor

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`