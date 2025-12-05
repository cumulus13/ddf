Caching System
==============

DDF includes a sophisticated caching system to improve performance by storing
parsed YAML files, service listings, and other frequently accessed data.

Overview
--------

The caching system supports multiple backends:

* **Pickle** - File-based cache (default, no dependencies)
* **Redis** - In-memory cache with persistence
* **Memcached** - Pure in-memory cache

Cache Keys
----------

DDF uses hierarchical cache keys:

.. code-block:: text

   yaml:hash              - SHA256 hash of docker-compose.yml
   open_file              - Parsed YAML content
   service_names:<hash>   - List of service names
   dockerfile:<service>   - Dockerfile path for service

Cache Invalidation
------------------

Automatic Invalidation
~~~~~~~~~~~~~~~~~~~~~~

Cache is automatically invalidated when:

1. docker-compose.yml file changes (detected by SHA256 hash)
2. Service is edited
3. Service is removed or renamed
4. Manual flush is triggered

Manual Invalidation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import CACHE
   
   # Invalidate specific key
   CACHE.delete('open_file')
   
   # Invalidate pattern
   CACHE.invalidate_pattern('service:')
   
   # Flush all cache
   CACHE.flush_all()

Cache Backends
--------------

Pickle Backend
~~~~~~~~~~~~~~

**Configuration:**

.. code-block:: ini

   [cache]
   backend = pickle
   enabled = true
   pickle_dir = /tmp/ddf_cache
   ttl = 3600

**Characteristics:**

* No external dependencies
* Stores data as Python pickle files
* TTL enforced by file modification time
* Suitable for single-user scenarios
* Not suitable for multi-process use

**When to Use:**

* Development environments
* Single-user workstations
* No Redis/Memcached available
* Offline operation required

**Performance:**

* Read: ~1ms per key
* Write: ~2ms per key
* Limited by disk I/O

Redis Backend
~~~~~~~~~~~~~

**Configuration:**

.. code-block:: ini

   [cache]
   backend = redis
   enabled = true
   ttl = 3600
   redis_host = localhost
   redis_port = 6379
   redis_password = your_password
   redis_db = 0

**Characteristics:**

* Fast in-memory storage
* Persistent data (configurable)
* Automatic TTL expiration
* Pattern-based operations
* Multi-process safe

**When to Use:**

* Production environments
* Multi-user scenarios
* Need persistence across restarts
* Need advanced features (patterns, TTL)

**Performance:**

* Read: ~0.1ms per key
* Write: ~0.2ms per key
* Network overhead minimal on localhost

**Installation:**

.. code-block:: bash

   # Install Redis
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   
   # Start Redis
   redis-server
   
   # Install Python client
   pip install redis

Redis with Pickle Serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [cache]
   backend = redis_pickle
   enabled = true
   # ... same Redis settings ...

Uses pickle serialization instead of JSON. Better for complex Python objects.

Memcached Backend
~~~~~~~~~~~~~~~~~

**Configuration:**

.. code-block:: ini

   [cache]
   backend = memcached
   enabled = true
   ttl = 3600
   memcached_servers = localhost:11211, server2:11211

**Characteristics:**

* Very fast pure in-memory storage
* No persistence (data lost on restart)
* Simple protocol
* Multi-process safe
* Distributed caching support

**When to Use:**

* Need highest performance
* Don't need persistence
* Distributed systems
* Simple caching needs

**Performance:**

* Read: ~0.05ms per key
* Write: ~0.1ms per key
* Lowest overhead

**Installation:**

.. code-block:: bash

   # Install Memcached
   # Ubuntu/Debian
   sudo apt-get install memcached
   
   # macOS
   brew install memcached
   
   # Start Memcached
   memcached -d
   
   # Install Python client
   pip install pymemcache

Memcached with Pickle
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   [cache]
   backend = memcached_pickle
   enabled = true
   # ... same Memcached settings ...

Uses pickle serialization for complex objects.

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Sensitive configuration can use environment variables:

.. code-block:: bash

   export REDIS_HOST=192.168.1.100
   export REDIS_PORT=6379
   export REDIS_PASSWORD=secret_password
   export REDIS_DB=0

These override config file settings.

INI File
~~~~~~~~

.. code-block:: ini

   [cache]
   # Backend selection
   backend = redis
   
   # Enable/disable caching
   enabled = true
   
   # Time to live (seconds)
   ttl = 3600
   
   # Redis settings
   redis_host = localhost
   redis_port = 6379
   redis_password = 
   redis_db = 0
   
   # Memcached settings
   memcached_servers = localhost:11211
   
   # Pickle settings
   pickle_dir = /tmp/ddf_cache

TTL Settings
~~~~~~~~~~~~

Time-to-live controls how long cached data is valid:

.. code-block:: ini

   [cache]
   # 1 hour
   ttl = 3600
   
   # 1 day
   ttl = 86400
   
   # No expiration
   ttl = 

**Recommendations:**

* Development: 600 (10 minutes)
* Production: 3600 (1 hour)
* Stable configs: 86400 (1 day)
* Frequently changing: 300 (5 minutes)

Usage Examples
--------------

Basic Operations
~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import CACHE
   
   # Set value
   CACHE.set('my_key', 'my_value', ttl=3600)
   
   # Get value
   value = CACHE.get('my_key')
   if value:
       print(f"Found: {value}")
   else:
       print("Not in cache")
   
   # Delete value
   CACHE.delete('my_key')

Complex Data
~~~~~~~~~~~~

.. code-block:: python

   from ddf import CACHE
   
   # Cache complex data
   service_data = {
       'name': 'web',
       'ports': ['8080:80'],
       'volumes': ['/data:/app/data']
   }
   
   CACHE.set('service:web', service_data)
   
   # Retrieve
   cached = CACHE.get('service:web')

Pattern Operations
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import CACHE
   
   # Store related keys
   CACHE.set('service:web:config', config1)
   CACHE.set('service:web:ports', ports1)
   CACHE.set('service:api:config', config2)
   
   # Invalidate all 'web' related keys
   count = CACHE.invalidate_pattern('service:web:')
   print(f"Invalidated {count} keys")

Using Decorator
~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import cache_with_invalidation
   
   @cache_with_invalidation(ttl=3600, key_prefix='expensive')
   def expensive_operation(arg1, arg2):
       # Expensive computation
       result = perform_calculation(arg1, arg2)
       return result
   
   # First call: computed and cached
   result1 = expensive_operation('a', 'b')
   
   # Second call: retrieved from cache
   result2 = expensive_operation('a', 'b')

Performance Optimization
------------------------

Best Practices
~~~~~~~~~~~~~~

1. **Use appropriate TTL**:

   - Short for frequently changing data
   - Long for stable configurations

2. **Batch operations**:

   .. code-block:: python

      # Instead of:
      for key in keys:
          CACHE.delete(key)
      
      # Use pattern:
      CACHE.invalidate_pattern('prefix:')

3. **Monitor cache hit rate**:

   .. code-block:: python

      hits = 0
      misses = 0
      
      value = CACHE.get(key)
      if value:
          hits += 1
      else:
          misses += 1
      
      hit_rate = hits / (hits + misses)

4. **Use correct serialization**:

   - JSON for simple data (faster)
   - Pickle for complex objects (more compatible)

5. **Connection pooling** (handled automatically):

   - Redis and Memcached clients maintain connection pools
   - No manual management needed

Benchmark Results
~~~~~~~~~~~~~~~~~

Average operation times (localhost):

+-------------------+--------+--------+----------+
| Backend           | Get    | Set    | Delete   |
+===================+========+========+==========+
| Pickle            | 1.0ms  | 2.0ms  | 0.5ms    |
+-------------------+--------+--------+----------+
| Redis             | 0.1ms  | 0.2ms  | 0.1ms    |
+-------------------+--------+--------+----------+
| Redis (pickle)    | 0.15ms | 0.25ms | 0.1ms    |
+-------------------+--------+--------+----------+
| Memcached         | 0.05ms | 0.1ms  | 0.05ms   |
+-------------------+--------+--------+----------+
| Memcached (pickle)| 0.08ms | 0.12ms | 0.05ms   |
+-------------------+--------+--------+----------+

Monitoring
----------

Check Cache Status
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import CACHE, CACHE_CONFIG
   
   # Check configuration
   print(f"Backend: {CACHE_CONFIG.backend}")
   print(f"Enabled: {CACHE_CONFIG.enabled}")
   print(f"TTL: {CACHE_CONFIG.ttl}")
   
   # Test cache
   CACHE.set('test', 'value')
   result = CACHE.get('test')
   print(f"Cache working: {result == 'value'}")

Redis Monitoring
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Connect to Redis CLI
   redis-cli
   
   # View all keys
   KEYS *
   
   # View DDF keys
   KEYS ddf:*
   
   # Get key value
   GET open_file
   
   # Monitor operations
   MONITOR
   
   # View memory usage
   INFO memory

Memcached Monitoring
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Connect to Memcached
   telnet localhost 11211
   
   # View stats
   stats
   
   # View items
   stats items
   
   # View slabs
   stats slabs

Troubleshooting
---------------

Cache Not Working
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Check if enabled
   from ddf import CACHE_CONFIG
   print(f"Enabled: {CACHE_CONFIG.enabled}")
   
   # Test set/get
   from ddf import CACHE
   CACHE.set('test', 'value')
   result = CACHE.get('test')
   if result != 'value':
       print("Cache not working!")

Connection Errors
~~~~~~~~~~~~~~~~~

**Redis:**

.. code-block:: bash

   # Check Redis is running
   redis-cli ping
   # Should return: PONG
   
   # Check connection
   redis-cli -h localhost -p 6379 -a password ping

**Memcached:**

.. code-block:: bash

   # Check Memcached is running
   echo stats | nc localhost 11211

**Fallback Behavior:**

DDF automatically falls back to pickle cache if Redis/Memcached fails:

.. code-block:: text

   Warning: Redis not available (Connection refused), falling back to pickle
   ✓ Using pickle cache: /tmp/ddf_cache

TTL Not Working
~~~~~~~~~~~~~~~

**Pickle Backend:**

- TTL enforced by file modification time
- Old files are deleted on next access
- Manual cleanup: ``rm /tmp/ddf_cache/*.pkl``

**Redis/Memcached:**

- TTL handled by server
- Check server is honoring TTL
- Use ``TTL key`` command in Redis CLI

Memory Issues
~~~~~~~~~~~~~

**High Memory Usage:**

.. code-block:: bash

   # Check cache size
   du -sh /tmp/ddf_cache              # Pickle
   redis-cli INFO memory | grep used  # Redis
   
   # Clear cache
   ddf --flush-cache  # If implemented
   
   # Or manually
   rm -rf /tmp/ddf_cache/*.pkl        # Pickle
   redis-cli FLUSHDB                  # Redis
   echo flush_all | nc localhost 11211  # Memcached

For more information, see :doc:`api/cache`.