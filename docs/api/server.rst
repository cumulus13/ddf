Server API
==========

This section documents the server mode functionality.

DDFServer Class
---------------

Background server with tray icon support.

.. autoclass:: ddf.DDFServer
   :members:
   :undoc-members:
   :show-inheritance:
   
   .. automethod:: __init__
   
   Server Operations
   ~~~~~~~~~~~~~~~~~
   
   .. automethod:: run_server
   .. automethod:: handle_client
   .. automethod:: setup_tray
   .. automethod:: quit_app
   
   Health Check
   ~~~~~~~~~~~~
   
   .. automethod:: health_check
   .. automethod:: _check_port_available
   .. automethod:: _check_cache

Server Functions
----------------

Lock Management
~~~~~~~~~~~~~~~

.. autofunction:: ddf.acquire_lock

.. autofunction:: ddf.release_lock

.. autofunction:: ddf.is_server_running

Communication
~~~~~~~~~~~~~

.. autofunction:: ddf.send_to_server

.. autofunction:: ddf.execute_command_in_server

Notification
~~~~~~~~~~~~

.. autofunction:: ddf.notify_user

.. autofunction:: ddf.create_emoji_icon

Server Configuration
--------------------

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [server]
   # Enable server mode
   active = true
   
   # Server host
   host = 127.0.0.1
   
   # Server port
   port = 9876

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. data:: SERVER_HOST
   
   Server bind address (default: 127.0.0.1)

.. data:: SERVER_PORT
   
   Server port (default: 9876)

.. data:: SERVER_ACTIVE
   
   Server mode enabled (default: false)

.. data:: LOCK_FILE
   
   Path to server lock file

Usage Examples
--------------

Starting Server
~~~~~~~~~~~~~~~

Command Line:

.. code-block:: bash

   # Start server manually
   ddf --server-mode
   
   # Start in background (Linux/macOS)
   ddf --server-mode &
   
   # Start in background (Windows)
   start /B ddf --server-mode

Python API:

.. code-block:: python

   from ddf import DDFServer
   
   server = DDFServer()
   server.run_server()

With Tray Icon:

.. code-block:: python

   from ddf import DDFServer
   
   server = DDFServer()
   server.setup_tray()  # Starts server with system tray icon

Checking Server Status
~~~~~~~~~~~~~~~~~~~~~~

Command Line:

.. code-block:: bash

   # Check health
   ddf --health-check

Python API:

.. code-block:: python

   from ddf import is_server_running
   
   if is_server_running():
       print("Server is running")
   else:
       print("Server is not running")

Sending Commands
~~~~~~~~~~~~~~~~

Python API:

.. code-block:: python

   from ddf import send_to_server
   
   send_to_server({
       "args": ["myservice", "-E"],
       "cwd": "/path/to/project"
   })

Server Health Check
~~~~~~~~~~~~~~~~~~~

Python API:

.. code-block:: python

   from ddf import DDFServer
   
   server = DDFServer()
   health = server.health_check()
   
   print(f"Server running: {health['server_running']}")
   print(f"Lock file exists: {health['lock_file_exists']}")
   print(f"Port available: {health['port_available']}")
   print(f"Cache available: {health['cache_available']}")

Server Communication Protocol
-----------------------------

Request Format
~~~~~~~~~~~~~~

Requests are JSON objects sent via TCP socket:

.. code-block:: json

   {
       "args": ["myservice", "-E"],
       "cwd": "/path/to/project",
       "command": "health_check"
   }

**Fields:**

* ``args`` - Command line arguments (list)
* ``cwd`` - Working directory (string)
* ``command`` - Special command type (optional)

Response Format
~~~~~~~~~~~~~~~

Responses are JSON objects:

.. code-block:: json

   {
       "status": "accepted"
   }

For health check:

.. code-block:: json

   {
       "server_running": true,
       "lock_file_exists": true,
       "port_available": true,
       "cache_available": true
   }

Architecture
------------

Server Flow
~~~~~~~~~~~

1. Server starts and acquires lock file
2. Binds to configured host:port
3. Listens for incoming connections
4. Handles requests in separate threads
5. Executes commands asynchronously
6. Sends notifications for results

Tray Icon Integration
~~~~~~~~~~~~~~~~~~~~~

When running with ``setup_tray()``:

1. Creates system tray icon
2. Shows context menu with options:
   
   * 🟢 Start Server
   * 🔴 Stop Server
   * 🚪 Quit

3. Sends desktop notifications
4. Handles graceful shutdown

Auto-forwarding
~~~~~~~~~~~~~~~

When server mode is active:

1. Client checks if server is running
2. Editing commands are forwarded to server
3. Read-only commands execute locally
4. Server executes commands in background

**Forwarded Commands:**

* ``-E, --edit-service``
* ``-e, --edit-dockerfile``
* ``-ed, --edit-entrypoint``
* ``-ef, --edit-file``
* ``-n, --new``
* ``-rm, --remove-service``
* ``-rn, --rename-service``
* ``-dd, --duplicate-service``
* ``-cs, --copy-service``
* ``-cd, --copy-dockerfile``
* ``-sd, --set-dockerfile``

**Local Commands:**

* ``-L, --list-service-name``
* ``-d, --detail``
* ``-f, --find``
* ``-p, --port``
* All read operations

Systemd Integration
-------------------

Linux Service
~~~~~~~~~~~~~

Create ``/etc/systemd/system/ddf-server.service``:

.. code-block:: ini

   [Unit]
   Description=DDF Docker Compose Server
   After=network.target
   
   [Service]
   Type=simple
   User=your_username
   WorkingDirectory=/home/your_username/projects
   ExecStart=/usr/bin/python3 -m ddf --server-mode
   Restart=always
   RestartSec=5
   
   [Install]
   WantedBy=multi-user.target

Enable and start:

.. code-block:: bash

   sudo systemctl enable ddf-server
   sudo systemctl start ddf-server
   sudo systemctl status ddf-server

Windows Service
~~~~~~~~~~~~~~~

Using NSSM (Non-Sucking Service Manager):

.. code-block:: bash

   # Install NSSM
   choco install nssm
   
   # Create service
   nssm install DDFServer "C:\Python312\python.exe" "-m ddf --server-mode"
   nssm set DDFServer AppDirectory "C:\Projects"
   nssm start DDFServer

Docker Container
~~~~~~~~~~~~~~~~

Run server in Docker:

.. code-block:: dockerfile

   FROM python:3.12-slim
   
   RUN pip install ddf[all]
   
   WORKDIR /workspace
   
   CMD ["ddf", "--server-mode"]

.. code-block:: bash

   docker run -d \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v $(pwd):/workspace \
     -p 9876:9876 \
     --name ddf-server \
     ddf-server

Security Considerations
-----------------------

1. **Localhost Only**: Server should bind to 127.0.0.1 only
2. **No Authentication**: Currently no auth mechanism
3. **Lock File**: Prevents multiple instances
4. **Process Isolation**: Commands run in separate threads
5. **File Permissions**: Lock file uses user permissions

**Do NOT expose server to network without:**

* Authentication mechanism
* TLS encryption
* Firewall rules
* Network isolation

Troubleshooting
---------------

Server Won't Start
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check if port is in use
   netstat -tuln | grep 9876  # Linux
   netstat -an | findstr 9876 # Windows
   
   # Check lock file
   ls ~/.ddf_server.lock
   
   # Remove stale lock
   rm ~/.ddf_server.lock

Commands Not Forwarded
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check server mode is enabled
   grep "active" ddf.ini
   
   # Verify server is running
   ddf --health-check

Notifications Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install notification dependencies
   pip install ddf[server]
   
   # Check notification system
   python -c "import plyer; plyer.notification.notify('Test', 'Message')"

For more information, see :doc:`../server_mode`.