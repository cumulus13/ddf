Configuration
=============

DDF uses an INI-style configuration file named ``ddf.ini``. This file should be placed
in the same directory as your docker-compose.yml or in the directory where you run DDF.

Configuration File Location
---------------------------

DDF looks for configuration in the following order:

1. ``./ddf.ini`` - Current directory
2. ``~/.ddf/ddf.ini`` - User home directory
3. ``/etc/ddf/ddf.ini`` - System-wide (Linux/macOS)

Configuration Sections
----------------------

Docker Compose Settings
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [docker-compose]
   # Path to docker-compose.yml file
   file = /path/to/docker-compose.yml
   
   # Root path for relative paths in docker-compose.yml
   root_path = /path/to/project

**Options:**

* ``file`` - Path to the main docker-compose.yml file
* ``root_path`` - Base directory for resolving relative paths

Editor Settings
~~~~~~~~~~~~~~~

.. code-block:: ini

   [editor]
   # Comma-separated list of editors to try
   names = nvim, vim, nano, subl, code

**Options:**

* ``names`` - Comma-separated list of editor commands. DDF tries them in order.

**Common Editor Configurations:**

Linux/macOS:

.. code-block:: ini

   [editor]
   names = nvim, vim, nano

Windows:

.. code-block:: ini

   [editor]
   names = C:\msys64\usr\bin\nano.exe, nvim, notepad++

GUI Editors:

.. code-block:: ini

   [editor]
   names = subl, code, atom, notepad++

Cache Settings
~~~~~~~~~~~~~~

.. code-block:: ini

   [cache]
   # Cache backend: pickle, redis, redis_pickle, memcached, memcached_pickle, none
   backend = pickle
   
   # Enable or disable caching
   enabled = true
   
   # Time to live in seconds (optional)
   ttl = 3600
   
   # Redis settings
   redis_host = localhost
   redis_port = 6379
   redis_password =
   redis_db = 0
   
   # Memcached settings
   memcached_servers = localhost:11211
   
   # Pickle directory
   pickle_dir = /tmp/ddf_cache

**Backend Options:**

* ``pickle`` - File-based cache (default, no extra dependencies)
* ``redis`` - Redis cache with JSON serialization
* ``redis_pickle`` - Redis cache with pickle serialization
* ``memcached`` - Memcached with JSON serialization
* ``memcached_pickle`` - Memcached with pickle serialization
* ``none`` - Disable caching

**Redis Configuration:**

.. code-block:: ini

   [cache]
   backend = redis
   redis_host = 192.168.1.100
   redis_port = 6379
   redis_password = your_password
   redis_db = 0
   ttl = 3600

**Memcached Configuration:**

.. code-block:: ini

   [cache]
   backend = memcached
   memcached_servers = 192.168.1.100:11211, 192.168.1.101:11211
   ttl = 3600

**Environment Variables:**

You can also use environment variables for sensitive data:

.. code-block:: bash

   export REDIS_HOST=192.168.1.100
   export REDIS_PORT=6379
   export REDIS_PASSWORD=secret
   export REDIS_DB=0

Backup Settings
~~~~~~~~~~~~~~~

.. code-block:: ini

   [backup]
   # Directory for backup files
   directory = /path/to/backups

**Options:**

* ``directory`` - Path where backup files are stored. Defaults to ``./backups``

Server Mode Settings
~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [server]
   # Enable server mode
   active = true
   
   # Server host (usually 127.0.0.1)
   host = 127.0.0.1
   
   # Server port
   port = 9876

**Options:**

* ``active`` - Enable/disable server mode (true/false)
* ``host`` - Server bind address (default: 127.0.0.1)
* ``port`` - Server port (default: 9876)

**Security Note:** Server mode should only be used with ``127.0.0.1`` (localhost) 
unless you have proper network security in place.

Docker Settings
~~~~~~~~~~~~~~~

.. code-block:: ini

   [docker]
   # Docker host
   host = tcp://localhost:2375
   
   # Docker port (default 2375 for TCP, 2376 for TLS)
   port = 2375
   tls_port = 2376
   
   # TLS verification
   tls_verify = 1
   
   # Certificate path for TLS
   cert_path = /path/to/certs
   
   # Docker API version
   api_version = 1.41

**Options:**

* ``host`` - Docker daemon host
* ``port`` - Docker daemon port
* ``tls_verify`` - Enable TLS verification
* ``cert_path`` - Path to TLS certificates
* ``api_version`` - Docker API version to use

Complete Example
----------------

Here's a complete example configuration:

.. code-block:: ini

   [docker-compose]
   file = /home/user/projects/myapp/docker-compose.yml
   root_path = /home/user/projects/myapp
   
   [editor]
   names = nvim, vim, nano
   
   [cache]
   backend = redis
   enabled = true
   ttl = 3600
   redis_host = localhost
   redis_port = 6379
   redis_db = 0
   
   [backup]
   directory = /home/user/projects/myapp/backups
   
   [server]
   active = false
   host = 127.0.0.1
   port = 9876
   
   [docker]
   host = unix:///var/run/docker.sock

Configuration Validation
-------------------------

Validate your configuration:

.. code-block:: bash

   ddf --health-check

This checks:

* Configuration file syntax
* Cache backend connectivity
* Docker daemon connectivity (if configured)
* Server mode status (if enabled)

Troubleshooting
---------------

Configuration Not Found
~~~~~~~~~~~~~~~~~~~~~~~

If DDF can't find your configuration:

1. Check the file is named exactly ``ddf.ini``
2. Place it in the same directory as docker-compose.yml
3. Or specify the path explicitly in environment variable:

   .. code-block:: bash

      export DDF_CONFIG=/path/to/ddf.ini

Cache Connection Issues
~~~~~~~~~~~~~~~~~~~~~~~

If cache backend fails to connect:

1. Check Redis/Memcached is running
2. Verify host and port settings
3. Check network connectivity
4. DDF will automatically fall back to pickle cache

Editor Not Found
~~~~~~~~~~~~~~~~

If your editor isn't found:

1. Use full path to editor executable
2. Verify editor is in PATH
3. Try multiple editors in the ``names`` list

For more help, see the :doc:`usage` guide.