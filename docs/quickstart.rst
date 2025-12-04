Quick Start Guide
=================

This guide will help you get started with DDF quickly.

Basic Workflow
--------------

1. **List Services**

   .. code-block:: bash

      # List all services in docker-compose.yml
      ddf -L
      
      # Filter services by pattern
      ddf -L -F "web*"

2. **Check for Issues**

   .. code-block:: bash

      # Find duplicate ports
      ddf
      
      # Check specific port
      ddf -f 8080
      
      # Find port conflicts for a service
      ddf myservice

3. **View Service Details**

   .. code-block:: bash

      # Show full service configuration
      ddf myservice -d
      
      # Show service ports
      ddf myservice -P
      
      # Show service volumes
      ddf myservice -vol
      
      # Show service hostname
      ddf myservice -hn

4. **Edit Services**

   .. code-block:: bash

      # Edit service configuration
      ddf myservice -E
      
      # Edit in detached terminal
      ddf myservice -E -dt
      
      # Edit Dockerfile
      ddf myservice -e
      
      # Edit entrypoint script
      ddf myservice -ed

Common Tasks
------------

Finding Duplicate Ports
~~~~~~~~~~~~~~~~~~~~~~~

DDF automatically scans for duplicate port mappings:

.. code-block:: bash

   # Scan all services
   ddf
   
   # Output example:
   # 🔍 Scanning for duplicate ports...
   # 
   # ❌ web/ports/8080/tcp --> api/ports/8080/tcp

Editing Service Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit a service with automatic backup:

.. code-block:: bash

   ddf myservice -E

This will:

1. Create an automatic backup
2. Open the service configuration in your editor
3. Validate the YAML syntax
4. Update the docker-compose.yml if changes are made

Creating New Services
~~~~~~~~~~~~~~~~~~~~~

Create a new service interactively:

.. code-block:: bash

   ddf newservice -n

This opens an editor with an empty service template.

Duplicating Services
~~~~~~~~~~~~~~~~~~~~

Duplicate an existing service:

.. code-block:: bash

   ddf oldservice -dd newservice

This creates a copy of ``oldservice`` named ``newservice``.

Managing Dockerfiles
~~~~~~~~~~~~~~~~~~~~

View a Dockerfile:

.. code-block:: bash

   ddf myservice -r

Edit a Dockerfile:

.. code-block:: bash

   ddf myservice -e

Copy Dockerfile to clipboard:

.. code-block:: bash

   ddf myservice -cd

Working with Entrypoints
~~~~~~~~~~~~~~~~~~~~~~~~

View entrypoint script:

.. code-block:: bash

   ddf myservice -en

Edit entrypoint script:

.. code-block:: bash

   ddf myservice -ed

Port Management
~~~~~~~~~~~~~~~

Find which services use a specific port:

.. code-block:: bash

   ddf -f 8080

Check if a port is duplicated:

.. code-block:: bash

   ddf -p 8080

Configuration
-------------

Create a configuration file ``ddf.ini``:

.. code-block:: ini

   [docker-compose]
   file = /path/to/docker-compose.yml
   root_path = /path/to/project
   
   [editor]
   names = nvim, vim, nano
   
   [cache]
   backend = pickle
   enabled = true
   ttl = 3600
   
   [backup]
   directory = /path/to/backups

Editor Selection
----------------

DDF tries editors in order from the configuration. Common setups:

.. code-block:: ini

   # Linux/macOS
   [editor]
   names = nvim, vim, nano
   
   # Windows
   [editor]
   names = C:\msys64\usr\bin\nano.exe, nvim, notepad++
   
   # GUI editors
   [editor]
   names = subl, code, atom

Next Steps
----------

* Learn about :doc:`configuration` options
* Explore :doc:`server_mode` for background operation
* Understand :doc:`caching` for better performance
* Read about :doc:`backup` and recovery