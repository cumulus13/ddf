Server Mode
===========

Server mode allows DDF to run as a background service, providing faster response times
and system tray integration for convenient access.

Overview
--------

When server mode is enabled:

1. DDF runs as a background process
2. Editing commands are automatically forwarded to the server
3. Read-only commands execute immediately in the foreground
4. A system tray icon provides quick access (optional)
5. Desktop notifications inform you of operation results

Benefits
--------

* **Faster Startup**: Server is already running, no initialization delay
* **Background Processing**: Editing doesn't block your terminal
* **Multi-tasking**: Open multiple files simultaneously in detached mode
* **Persistent State**: Cache remains warm between operations
* **System Integration**: Tray icon and notifications

Architecture
------------

Client-Server Model
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ┌─────────────┐          ┌─────────────┐
   │   Client    │          │   Server    │
   │   (CLI)     │ ────────>│ (Background)│
   └─────────────┘          └─────────────┘
         │                         │
         │ Editing Command         │ Executes
         │ (Forwarded)             │ Asynchronously
         │                         │
         │ Read Command            │
         │ (Local Execution)       │
         └─────────────────────────┘

Command Routing
~~~~~~~~~~~~~~~

**Forwarded to Server:**

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

**Executed Locally:**

* ``-L, --list-service-name``
* ``-d, --detail``
* ``-f, --find``
* ``-p, --port``
* ``-r, --dockerfile`` (read only)
* ``-en, --entrypoint`` (read only)
* All display/query commands

Starting Server
---------------

Manual Start
~~~~~~~~~~~~

.. code-block:: bash

   # Foreground (for testing)
   ddf --server-mode
   
   # Background (Linux/macOS)
   ddf --server-mode &
   
   # Background (Windows)
   start /B ddf --server-mode

With Tray Icon
~~~~~~~~~~~~~~

.. code-block:: bash

   # Install server dependencies first
   pip install git+https://github.com/cumulus13/ddf[server]
   
   # Start with tray icon
   ddf --server-mode
   
   # Tray menu provides:
   # - 🟢 Start Server
   # - 🔴 Stop Server
   # - 🚪 Quit

Enable Auto-forwarding
~~~~~~~~~~~~~~~~~~~~~~~

Edit ``ddf.ini``:

.. code-block:: ini

   [server]
   active = true
   host = 127.0.0.1
   port = 9876

Now editing commands will automatically use the server if it's running.

Systemd Service (Linux)
------------------------

Create Service File
~~~~~~~~~~~~~~~~~~~

Create ``/etc/systemd/system/ddf-server.service``:

.. code-block:: ini

   [Unit]
   Description=DDF Docker Compose Server
   After=network.target
   
   [Service]
   Type=simple
   User=%i
   Group=%i
   WorkingDirectory=/home/%i/projects
   Environment="PATH=/home/%i/.local/bin:/usr/bin:/bin"
   ExecStart=/usr/bin/python3 -m ddf --server-mode
   Restart=always
   RestartSec=5
   StandardOutput=journal
   StandardError=journal
   
   [Install]
   WantedBy=multi-user.target

Enable and Start
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Reload systemd
   sudo systemctl daemon-reload
   
   # Enable on boot
   sudo systemctl enable ddf-server@$USER
   
   # Start now
   sudo systemctl start ddf-server@$USER
   
   # Check status
   sudo systemctl status ddf-server@$USER
   
   # View logs
   journalctl -u ddf-server@$USER -f

User Service (Linux)
~~~~~~~~~~~~~~~~~~~~~

For user-level service without sudo:

Create ``~/.config/systemd/user/ddf-server.service``:

.. code-block:: ini

   [Unit]
   Description=DDF Docker Compose Server
   After=network.target
   
   [Service]
   Type=simple
   WorkingDirectory=%h/projects
   ExecStart=%h/.local/bin/ddf --server-mode
   Restart=always
   RestartSec=5
   
   [Install]
   WantedBy=default.target

.. code-block:: bash

   # Enable linger (keep running after logout)
   loginctl enable-linger $USER
   
   # Reload
   systemctl --user daemon-reload
   
   # Enable and start
   systemctl --user enable --now ddf-server
   
   # Check status
   systemctl --user status ddf-server

Windows Service
---------------

Using NSSM
~~~~~~~~~~

`NSSM (Non-Sucking Service Manager) <https://nssm.cc/>`_ is recommended:

.. code-block:: powershell

   # Install NSSM
   choco install nssm
   
   # Or download from https://nssm.cc/download
   
   # Install service
   nssm install DDFServer
   
   # Configure
   nssm set DDFServer Application "C:\Python312\python.exe"
   nssm set DDFServer AppParameters "-m ddf --server-mode"
   nssm set DDFServer AppDirectory "C:\Projects"
   nssm set DDFServer DisplayName "DDF Docker Compose Server"
   nssm set DDFServer Description "Enhanced Docker Compose management server"
   nssm set DDFServer Start SERVICE_AUTO_START
   
   # Start service
   nssm start DDFServer
   
   # Check status
   nssm status DDFServer

Using Task Scheduler
~~~~~~~~~~~~~~~~~~~~~

Create a scheduled task that runs at startup:

.. code-block:: powershell

   # Create task
   $action = New-ScheduledTaskAction -Execute "C:\Python312\python.exe" -Argument "-m ddf --server-mode" -WorkingDirectory "C:\Projects"
   $trigger = New-ScheduledTaskTrigger -AtStartup
   $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
   $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0
   
   Register-ScheduledTask -TaskName "DDF Server" -Action $action -Trigger $trigger -Principal $principal -Settings $settings

macOS LaunchAgent
-----------------

Create Launch Agent
~~~~~~~~~~~~~~~~~~~

Create ``~/Library/LaunchAgents/com.ddf.server.plist``:

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.ddf.server</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/local/bin/python3</string>
           <string>-m</string>
           <string>ddf</string>
           <string>--server-mode</string>
       </array>
       <key>WorkingDirectory</key>
       <string>/Users/YOUR_USERNAME/projects</string>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
       <key>StandardOutPath</key>
       <string>/tmp/ddf-server.log</string>
       <key>StandardErrorPath</key>
       <string>/tmp/ddf-server.error.log</string>
   </dict>
   </plist>

Load and Start
~~~~~~~~~~~~~~

.. code-block:: bash

   # Load agent
   launchctl load ~/Library/LaunchAgents/com.ddf.server.plist
   
   # Start
   launchctl start com.ddf.server
   
   # Check status
   launchctl list | grep ddf
   
   # Stop
   launchctl stop com.ddf.server
   
   # Unload
   launchctl unload ~/Library/LaunchAgents/com.ddf.server.plist

Docker Container
----------------

Dockerfile
~~~~~~~~~~

.. code-block:: dockerfile

   FROM python:3.12-slim
   
   # Install dependencies
   RUN apt-get update && apt-get install -y \
       docker.io \
       && rm -rf /var/lib/apt/lists/*
   
   # Install DDF
   RUN pip install --no-cache-dir ddf[all]
   
   # Create workspace
   WORKDIR /workspace
   
   # Copy default config (optional)
   COPY ddf.ini /workspace/ddf.ini
   
   # Expose server port
   EXPOSE 9876
   
   # Run server
   CMD ["ddf", "--server-mode"]

Build and Run
~~~~~~~~~~~~~

.. code-block:: bash

   # Build
   docker build -t ddf-server .
   
   # Run
   docker run -d \
     --name ddf-server \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v $(pwd):/workspace \
     -p 127.0.0.1:9876:9876 \
     ddf-server
   
   # Check logs
   docker logs -f ddf-server
   
   # Stop
   docker stop ddf-server

Docker Compose
~~~~~~~~~~~~~~

.. code-block:: yaml

   version: '3.8'
   
   services:
     ddf-server:
       image: ddf-server:latest
       container_name: ddf-server
       restart: unless-stopped
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
         - ./:/workspace
       ports:
         - "127.0.0.1:9876:9876"
       environment:
         - REDIS_HOST=redis
         - REDIS_PORT=6379
       depends_on:
         - redis
     
     redis:
       image: redis:7-alpine
       container_name: ddf-redis
       restart: unless-stopped

Health Monitoring
-----------------

Check Server Status
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Simple check
   ddf --health-check
   
   # Output:
   # 🏥 Server Health Check:
   # 
   # ✅ Server Running: True
   # ✅ Lock File Exists: True
   # ✅ Port Available: True
   # ✅ Cache Available: True

Manual Check
~~~~~~~~~~~~

.. code-block:: bash

   # Check if process is running
   ps aux | grep "ddf --server-mode"
   
   # Check if port is listening
   netstat -tuln | grep 9876  # Linux
   netstat -an | findstr 9876 # Windows
   lsof -i :9876              # macOS

Python API
~~~~~~~~~~

.. code-block:: python

   from ddf import is_server_running, DDFServer
   
   # Check status
   if is_server_running():
       print("Server is running")
       
       # Get detailed health
       server = DDFServer()
       health = server.health_check()
       print(health)

Troubleshooting
---------------

Server Won't Start
~~~~~~~~~~~~~~~~~~

**Port Already in Use:**

.. code-block:: bash

   # Find process using port
   lsof -i :9876                    # Linux/macOS
   netstat -ano | findstr :9876     # Windows
   
   # Kill process
   kill <PID>                       # Linux/macOS
   taskkill /F /PID <PID>           # Windows
   
   # Or change port in config
   [server]
   port = 9877

**Stale Lock File:**

.. code-block:: bash

   # Remove lock file
   rm ~/.ddf_server.lock            # Linux/macOS
   del %USERPROFILE%\.ddf_server.lock  # Windows

**Permission Issues:**

.. code-block:: bash

   # Check file permissions
   ls -la ~/.ddf_server.lock
   
   # Fix permissions
   chmod 644 ~/.ddf_server.lock

Commands Not Forwarded
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Verify server mode is enabled
   grep "active" ddf.ini
   
   # Should show:
   # [server]
   # active = true
   
   # Check server is running
   ddf --health-check

Notifications Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install notification dependencies
   pip install git+https://github.com/cumulus13/ddf[server]
   
   # Test notifications
   python -c "import plyer; plyer.notification.notify('Test', 'Message')"
   
   # Check notification daemon (Linux)
   systemctl --user status dunst    # For dunst
   ps aux | grep notification       # Others

Performance Issues
~~~~~~~~~~~~~~~~~~

**High Memory Usage:**

- Reduce cache size
- Use Redis instead of pickle
- Clear old backups

**Slow Response:**

- Check cache backend connectivity
- Monitor system resources
- Check for I/O bottlenecks

Security Considerations
-----------------------

1. **Localhost Only**: Always bind to 127.0.0.1
2. **No Network Exposure**: Don't expose port to network
3. **File Permissions**: Ensure proper lock file permissions
4. **Process Isolation**: Run as limited user
5. **Input Validation**: All inputs are validated

**DO NOT:**

- Bind to 0.0.0.0 or public IP
- Run as root/administrator
- Expose port through firewall
- Use in untrusted environments

For more information, see :doc:`api/server`.