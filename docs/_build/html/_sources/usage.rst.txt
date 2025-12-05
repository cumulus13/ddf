Usage Guide
===========

This comprehensive guide covers all DDF commands and features.

Command Line Interface
----------------------

Basic Syntax
~~~~~~~~~~~~

.. code-block:: bash

   ddf [SERVICE] [OPTIONS]

Where ``SERVICE`` is an optional service name pattern, and ``OPTIONS`` are command flags.

Global Options
~~~~~~~~~~~~~~

.. code-block:: text

   -c, --file FILE          Path to docker-compose YAML file
   -v, --version            Show version and exit
   -h, --help               Show help message
   --theme THEME            Syntax highlighting theme (default: fruity)
   --debug                  Enable debug mode
   --server-mode            Run in server mode (hidden)
   --health-check           Check server health status
   -dt, --detach            Open editor in new terminal window

Service Information
-------------------

List Services
~~~~~~~~~~~~~

.. code-block:: bash

   # List all services
   ddf -L
   
   # List services matching pattern
   ddf -L -F "web*"
   ddf -L -F "api" "worker"

Show Service Details
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Full configuration
   ddf myservice -d
   
   # With line numbers
   ddf myservice -d
   
   # Without line numbers
   ddf myservice -d -nl

Show Service Ports
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # List ports for service
   ddf myservice -P
   
   # Find services using specific port
   ddf -f 8080
   
   # Check if port is duplicated
   ddf -p 8080

Show Service Volumes
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show service volumes
   ddf myservice -vol
   
   # Show global volumes section
   ddf -V
   
   # Show volumes for pattern
   ddf -V -F "web*"

Show Service Devices
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show devices for service
   ddf myservice -D
   
   # Show all devices
   ddf -D

Show Service Hostname
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show hostname for service
   ddf myservice -hn
   
   # Show all hostnames
   ddf -hn

Port Management
---------------

Find Duplicate Ports
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Scan all services
   ddf
   
   # Scan specific service
   ddf myservice

Find Port Usage
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Find which services use a port
   ddf -f 8080
   
   # Compact output (default)
   ddf -f 8080
   
   # Detailed output
   ddf -f 8080 -a

Check Port Duplication
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check if port is duplicated
   ddf -p 8080
   
   # Output:
   # ✅ Port 8080 only found in service: web (8080:80)
   # or
   # ❌ Port 8080 is DUPLICATE in these services:
   #   - web: 8080:80
   #   - api: 8080:8000

Service Editing
---------------

Edit Service Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Edit service in default editor
   ddf myservice -E
   
   # Edit in detached terminal
   ddf myservice -E -dt
   
   # With custom config file
   ddf myservice -E -c /path/to/compose.yml

**Workflow:**

1. Automatic backup is created
2. Service config opens in editor
3. Changes are validated
4. docker-compose.yml is updated
5. Cache is invalidated

Edit Dockerfile
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Edit Dockerfile for service
   ddf myservice -e
   
   # Edit in detached terminal
   ddf myservice -e -dt
   
   # Edit specific Dockerfile
   ddf -e /path/to/Dockerfile

**Note:** Automatically resolves Dockerfile path from build context.

Edit Entrypoint Script
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Edit entrypoint script
   ddf myservice -ed
   
   # Edit in detached terminal
   ddf myservice -ed -dt

**Note:** Automatically finds and resolves entrypoint path from COPY instructions.

Edit Specific File
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Edit file referenced in COPY instruction
   ddf myservice -ef nginx.conf
   
   # Edit in detached terminal
   ddf myservice -ef startup.sh -dt

Set Dockerfile Path
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Set Dockerfile path for service
   ddf myservice -sd /path/to/Dockerfile
   
   # Then edit
   ddf myservice -sd /path/to/Dockerfile -e

Service Management
------------------

Create New Service
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create new service
   ddf newservice -n
   
   # Opens editor with empty service template

Duplicate Service
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Duplicate existing service
   ddf oldservice -dd newservice
   
   # Creates copy of oldservice as newservice

Rename Service
~~~~~~~~~~~~~~

.. code-block:: bash

   # Rename service
   ddf oldname -rn newname

Remove Service
~~~~~~~~~~~~~~

.. code-block:: bash

   # Remove service (with confirmation)
   ddf myservice -rm

**Note:** Creates backup before removal.

Copy Service to Clipboard
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Copy service YAML to clipboard
   ddf myservice -cs

Copy Dockerfile to Clipboard
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Copy Dockerfile content to clipboard
   ddf myservice -cd

Reading Files
-------------

Read Dockerfile
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Read Dockerfile with syntax highlighting
   ddf myservice -r
   
   # Without line numbers
   ddf myservice -r -nl
   
   # Read specific Dockerfile
   ddf -r /path/to/Dockerfile

Read Entrypoint
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Read entrypoint script
   ddf myservice -en
   
   # Without line numbers
   ddf myservice -en -nl

Read Specific File
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Read file from COPY instruction
   ddf myservice -rf nginx.conf

Advanced Features
-----------------

Pattern Matching
~~~~~~~~~~~~~~~~

Service names support wildcards and substring matching:

.. code-block:: bash

   # Wildcard matching
   ddf "web*" -d        # Matches web, web-api, web-frontend
   
   # Substring matching
   ddf api -d           # Matches api, web-api, api-gateway
   
   # Regex with filter
   ddf -L -F "^web-.*"  # Matches web-api, web-frontend

Detached Mode
~~~~~~~~~~~~~

Open editors in separate terminal windows:

.. code-block:: bash

   # Edit in new terminal
   ddf myservice -E -dt
   
   # Multiple edits simultaneously
   ddf service1 -E -dt
   ddf service2 -E -dt
   ddf service3 -E -dt

**Supported Platforms:**

* **Windows**: Opens in new cmd window
* **macOS**: Opens in Terminal.app
* **Linux**: Supports gnome-terminal, konsole, xterm, alacritty, kitty, terminator

Filtering
~~~~~~~~~

Use filters to narrow down service lists:

.. code-block:: bash

   # Multiple filters (OR logic)
   ddf -L -F "web" "api" "worker"
   
   # Regex filter
   ddf -L -F "^web-.*"
   
   # Wildcard filter
   ddf -L -F "web*"

Theme Customization
~~~~~~~~~~~~~~~~~~~

Change syntax highlighting theme:

.. code-block:: bash

   # Available themes: fruity, monokai, vim, emacs, etc.
   ddf myservice -d --theme monokai

Batch Operations
----------------

Process Multiple Services
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Find all services with pattern
   services=$(ddf -L -F "web*" | grep "^  -" | cut -d' ' -f4)
   
   # Edit each one
   for svc in $services; do
       ddf $svc -E
   done

Export All Services
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Export all services to separate files
   for svc in $(ddf -L | grep "^  -" | cut -d' ' -f4); do
       ddf $svc -cs > "${svc}.yml"
   done

Backup All Dockerfiles
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Copy all Dockerfiles
   for svc in $(ddf -L | grep "^  -" | cut -d' ' -f4); do
       ddf $svc -r > "Dockerfile.${svc}"
   done

Exit Codes
----------

DDF uses standard exit codes:

* ``0`` - Success
* ``1`` - General error
* ``2`` - Command line syntax error

Examples
--------

Typical Workflow
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Check for issues
   ddf
   
   # 2. Inspect problematic service
   ddf myservice -d
   
   # 3. Edit service configuration
   ddf myservice -E
   
   # 4. Edit Dockerfile if needed
   ddf myservice -e
   
   # 5. Verify changes
   ddf myservice -d

Port Conflict Resolution
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Find duplicate
   ddf
   # Output: ❌ web/8080 --> api/8080
   
   # 2. Check both services
   ddf web -P
   ddf api -P
   
   # 3. Edit one to change port
   ddf api -E
   
   # 4. Verify fix
   ddf

Service Migration
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Duplicate service
   ddf oldservice -dd newservice
   
   # 2. Edit new service
   ddf newservice -E
   
   # 3. Copy and modify Dockerfile
   ddf oldservice -cd  # Copy to clipboard
   # Create new Dockerfile
   ddf newservice -e   # Edit Dockerfile

For more advanced usage, see :doc:`server_mode` and :doc:`caching`.