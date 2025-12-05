Backup API
==========

This section documents the backup management classes.

BackupManager Class
-------------------

Basic backup operations for files and directory management.

.. autoclass:: ddf.BackupManager
   :members:
   :undoc-members:
   :show-inheritance:
   
   Directory Management
   ~~~~~~~~~~~~~~~~~~~~
   
   .. automethod:: get_backup_dir
      :no-index:
   
   Backup Operations
   ~~~~~~~~~~~~~~~~~
   
   .. automethod:: create_backup
      :no-index:

   .. automethod:: restore_from_backup
      :no-index:

   .. automethod:: list_backups
      :no-index:

   .. automethod:: prompt_restore_backup
      :no-index:

EnhancedBackupManager Class
---------------------------

Enhanced backup manager with better integration and monitoring.

.. autoclass:: ddf.EnhancedBackupManager
   :members:
   :undoc-members:
   :show-inheritance:
   
   .. automethod:: create_backup_with_context
      :no-index:
      
   .. automethod:: should_create_backup
      :no-index:

Usage Examples
--------------

Basic Backup
~~~~~~~~~~~~

.. code-block:: python

   from ddf import BackupManager
   
   # Create backup
   backup_path = BackupManager.create_backup(
       file_path='/path/to/docker-compose.yml',
       operation_type='edit'
   )
   
   if backup_path:
       print(f"Backup created: {backup_path}")
   else:
       print("Backup failed")

Backup with Context
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EnhancedBackupManager
   
   # Create backup with service context
   backup_path = EnhancedBackupManager.create_backup_with_context(
       file_path='/path/to/docker-compose.yml',
       operation_type='edit_service',
       context_info='myservice'
   )
   
   # Filename will be:
   # docker-compose.yml.edit_service.myservice.TIMESTAMP.backup

List Backups
~~~~~~~~~~~~

.. code-block:: python

   from ddf import BackupManager
   
   # List all backups
   all_backups = BackupManager.list_backups()
   
   for backup_name, backup_path, mtime in all_backups:
       import datetime
       timestamp = datetime.datetime.fromtimestamp(mtime)
       print(f"{backup_name} ({timestamp})")
   
   # List backups for specific file
   file_backups = BackupManager.list_backups(
       file_path='/path/to/docker-compose.yml'
   )

Restore Backup
~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import BackupManager
   
   # Restore from backup
   success = BackupManager.restore_from_backup(
       backup_path='/path/to/backups/file.backup',
       original_path='/path/to/original/file'
   )
   
   if success:
       print("File restored successfully")

Interactive Restore
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import BackupManager
   
   # Prompt user to restore
   restored = BackupManager.prompt_restore_backup(
       original_path='/path/to/docker-compose.yml'
   )
   
   if restored:
       print("Backup was restored")
   else:
       print("No backup was restored")

Check if Backup Needed
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EnhancedBackupManager
   
   # Check if operation requires backup
   operations = [
       'edit_service',
       'edit_dockerfile',
       'edit_entrypoint',
       'remove_service',
       'duplicate_service'
   ]
   
   for op in operations:
       needs_backup = EnhancedBackupManager.should_create_backup(op)
       print(f"{op}: {'Yes' if needs_backup else 'No'}")

Backup Directory
~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import BackupManager
   import os
   
   # Get backup directory
   backup_dir = BackupManager.get_backup_dir()
   print(f"Backups stored in: {backup_dir}")
   
   # Create if doesn't exist
   os.makedirs(backup_dir, exist_ok=True)
   
   # List contents
   backups = os.listdir(backup_dir)
   print(f"Total backups: {len(backups)}")

Integration Examples
--------------------

With Error Handling
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EnhancedBackupManager, DDF
   
   def safe_edit_service(service_name):
       file_path = '/path/to/docker-compose.yml'
       
       # Create backup
       backup_path = EnhancedBackupManager.create_backup_with_context(
           file_path=file_path,
           operation_type='edit_service',
           context_info=service_name
       )
       
       try:
           # Perform edit
           DDF.edit_service(file_path=file_path, service_name=service_name)
           print("✅ Service edited successfully")
           
       except Exception as e:
           print(f"❌ Error: {e}")
           
           if backup_path:
               # Restore backup
               success = BackupManager.restore_from_backup(
                   backup_path=backup_path,
                   original_path=file_path
               )
               if success:
                   print("🔄 Backup restored")

Automated Cleanup
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import BackupManager
   import time
   import os
   
   def cleanup_old_backups(days=30):
       """Remove backups older than specified days."""
       backup_dir = BackupManager.get_backup_dir()
       current_time = time.time()
       max_age = days * 86400  # days to seconds
       
       removed = 0
       for filename in os.listdir(backup_dir):
           if not filename.endswith('.backup'):
               continue
           
           filepath = os.path.join(backup_dir, filename)
           file_age = current_time - os.path.getmtime(filepath)
           
           if file_age > max_age:
               os.remove(filepath)
               removed += 1
       
       print(f"Removed {removed} old backups")
       return removed

Backup Verification
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import yaml
   from ddf import BackupManager
   
   def verify_backup(backup_path):
       """Verify backup file is valid YAML."""
       try:
           with open(backup_path, 'r') as f:
               yaml.safe_load(f)
           return True
       except Exception as e:
           print(f"Invalid backup: {e}")
           return False
   
   # Verify all backups
   backups = BackupManager.list_backups()
   valid = 0
   invalid = 0
   
   for name, path, mtime in backups:
       if verify_backup(path):
           valid += 1
       else:
           invalid += 1
   
   print(f"Valid: {valid}, Invalid: {invalid}")

Backup History
~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import BackupManager
   import datetime
   
   def show_backup_history(file_path, limit=10):
       """Show recent backup history for a file."""
       backups = BackupManager.list_backups(file_path)
       
       print(f"Backup history for {file_path}:")
       print("-" * 80)
       
       for i, (name, path, mtime) in enumerate(backups[:limit], 1):
           timestamp = datetime.datetime.fromtimestamp(mtime)
           size = os.path.getsize(path)
           
           print(f"{i}. {timestamp:%Y-%m-%d %H:%M:%S} - {size:,} bytes")
           print(f"   {name}")
       
       if len(backups) > limit:
           print(f"\n... and {len(backups) - limit} more")
   
   # Usage
   show_backup_history('/path/to/docker-compose.yml')

Constants
---------

Backup Operations
~~~~~~~~~~~~~~~~~

Operations that trigger automatic backups:

.. code-block:: python

   BACKUP_OPERATIONS = {
       'edit_service',
       'edit_dockerfile',
       'edit_entrypoint',
       'edit_file',
       'remove_service',
       'rename_service',
       'set_dockerfile',
       'new_service',
       'duplicate_service',
       'copy_dockerfile_config'
   }

Backup File Pattern
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Backup filename format:
   BACKUP_PATTERN = "{original}.{operation}.{context}.{timestamp}.backup"
   
   # Timestamp format:
   TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
   
   # Example:
   # docker-compose.yml.edit_service.web.20251204_150131.backup

Error Handling
--------------

Common Exceptions
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import BackupManager
   
   try:
       backup_path = BackupManager.create_backup(
           file_path='/path/to/file',
           operation_type='edit'
       )
   except FileNotFoundError:
       print("File not found")
   except PermissionError:
       print("Permission denied")
   except OSError as e:
       print(f"OS error: {e}")
   except Exception as e:
       print(f"Unexpected error: {e}")

Handling Failed Backups
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EnhancedBackupManager
   
   backup_path = EnhancedBackupManager.create_backup_with_context(
       file_path=file_path,
       operation_type='edit',
       context_info='test'
   )
   
   if not backup_path:
       # Backup failed - decide what to do
       proceed = input("Backup failed. Continue anyway? (y/N): ")
       if proceed.lower() != 'y':
           print("Operation cancelled")
           return

For more information, see :doc:`../backup`.