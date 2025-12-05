Backup & Recovery
=================

DDF automatically creates backups before making changes to your docker-compose files,
providing a safety net for recovering from mistakes or unwanted changes.

Overview
--------

Key Features:

* **Automatic Backups**: Created before editing operations
* **Timestamped Files**: Each backup includes date/time
* **Operation Context**: Backup name includes operation type
* **Quick Recovery**: Easy restoration from backups
* **Multiple Versions**: Keep history of changes

Backup Operations
-----------------

When Backups Are Created
~~~~~~~~~~~~~~~~~~~~~~~~~

Backups are automatically created before:

* Editing service configuration (``-E``)
* Editing Dockerfile (``-e``)
* Editing entrypoint script (``-ed``)
* Removing service (``-rm``)
* Renaming service (``-rn``)
* Setting Dockerfile path (``-sd``)
* Duplicating service (``-dd``)

Backup File Format
~~~~~~~~~~~~~~~~~~

Backup filenames follow this pattern:

.. code-block:: text

   <original_filename>.<operation>.<context>.<timestamp>.backup

Examples:

.. code-block:: text

   docker-compose.yml.edit_service.web.20251204_150131.backup
   docker-compose.yml.remove_service.api.20251204_151045.backup
   Dockerfile.edit.web.20251204_152300.backup
   entrypoint.sh.edit.api.20251204_153415.backup

Configuration
-------------

Backup Directory
~~~~~~~~~~~~~~~~

Configure where backups are stored in ``ddf.ini``:

.. code-block:: ini

   [backup]
   directory = /path/to/backups

Default locations:

* Same directory as DDF script: ``./backups``
* Custom path: As configured

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   export DDF_BACKUP_DIR=/path/to/backups

Using Backups
-------------

Listing Backups
~~~~~~~~~~~~~~~

Command Line:

.. code-block:: bash

   # List all backups in backup directory
   ls -lht backups/
   
   # Find backups for specific file
   ls -lht backups/docker-compose.yml*
   
   # Find recent backups (last 24 hours)
   find backups/ -name "*.backup" -mtime -1

Python API:

.. code-block:: python

   from ddf import BackupManager
   
   # List all backups
   backups = BackupManager.list_backups()
   for name, path, mtime in backups:
       print(f"{name} - {path}")
   
   # List backups for specific file
   backups = BackupManager.list_backups('/path/to/docker-compose.yml')

Manual Backup
~~~~~~~~~~~~~

Python API:

.. code-block:: python

   from ddf import BackupManager
   
   # Create backup
   backup_path = BackupManager.create_backup(
       '/path/to/file',
       operation_type='manual'
   )
   print(f"Backup created: {backup_path}")

Restoring Backups
~~~~~~~~~~~~~~~~~

Interactive Restoration:

When an error occurs during editing, DDF offers automatic restoration:

.. code-block:: text

   ❌ Error saving YAML file: Invalid syntax
   
   📋 Available backups for docker-compose.yml:
   1. docker-compose.yml.edit_service.web.20251204_150131.backup (2025-12-04 15:01:31)
   2. docker-compose.yml.edit_service.api.20251204_145500.backup (2025-12-04 14:55:00)
   3. docker-compose.yml.remove_service.old.20251204_143000.backup (2025-12-04 14:30:00)
   
   🔄 Would you like to restore from a backup? (1-3/n):

Manual Restoration:

Python API:

.. code-block:: python

   from ddf import BackupManager
   
   # Restore from specific backup
   success = BackupManager.restore_from_backup(
       backup_path='/path/to/backups/file.backup',
       original_path='/path/to/original/file'
   )
   
   if success:
       print("✅ File restored successfully")

Command Line:

.. code-block:: bash

   # Copy backup manually
   cp backups/docker-compose.yml.edit_service.web.20251204_150131.backup docker-compose.yml

Advanced Usage
--------------

Enhanced Backup Manager
~~~~~~~~~~~~~~~~~~~~~~~

The EnhancedBackupManager provides additional context:

.. code-block:: python

   from ddf import EnhancedBackupManager
   
   # Create backup with context
   backup_path = EnhancedBackupManager.create_backup_with_context(
       file_path='/path/to/file',
       operation_type='edit_service',
       context_info='myservice'
   )
   
   # Backup filename will be:
   # file.edit_service.myservice.20251204_150131.backup

Checking if Backup Should Be Created
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EnhancedBackupManager
   
   # Check if operation requires backup
   if EnhancedBackupManager.should_create_backup('edit_service'):
       # Create backup
       backup_path = EnhancedBackupManager.create_backup_with_context(...)

Batch Operations
~~~~~~~~~~~~~~~~

Backup Multiple Files:

.. code-block:: python

   from ddf import BackupManager
   import glob
   
   # Backup all YAML files
   for yaml_file in glob.glob('*.yml'):
       BackupManager.create_backup(yaml_file, operation_type='batch_backup')

Restore Multiple Files:

.. code-block:: bash

   # Restore all backups from specific time
   for backup in backups/*.20251204_15*; do
       original=$(echo $backup | sed 's/\..*\.backup$//')
       cp "$backup" "$original"
   done

Best Practices
--------------

Regular Cleanup
~~~~~~~~~~~~~~~

Backups can accumulate over time. Regular cleanup is recommended:

.. code-block:: bash

   # Remove backups older than 30 days
   find backups/ -name "*.backup" -mtime +30 -delete
   
   # Keep only last 10 backups per file
   for file in backups/*.yml.*; do
       ls -t "$file"* | tail -n +11 | xargs rm -f
   done

Automated Cleanup Script:

.. code-block:: bash

   #!/bin/bash
   # cleanup_backups.sh
   
   BACKUP_DIR="$HOME/projects/backups"
   DAYS_TO_KEEP=30
   MAX_BACKUPS_PER_FILE=10
   
   # Remove old backups
   find "$BACKUP_DIR" -name "*.backup" -mtime +$DAYS_TO_KEEP -delete
   
   # Keep only recent backups per file
   for original in $(ls "$BACKUP_DIR"/*.backup | sed 's/\..*\.backup$//' | sort -u); do
       ls -t "$original".*.backup 2>/dev/null | tail -n +$((MAX_BACKUPS_PER_FILE + 1)) | xargs rm -f
   done
   
   echo "Backup cleanup completed"

Schedule with Cron:

.. code-block:: bash

   # Add to crontab
   # Run daily at 2 AM
   0 2 * * * /path/to/cleanup_backups.sh

Backup Storage
~~~~~~~~~~~~~~

**Local Storage:**

- Fast access
- No network dependency
- Limited by disk space

**Network Storage:**

.. code-block:: bash

   # Mount network share
   mount //server/backups /mnt/backups
   
   # Configure DDF
   [backup]
   directory = /mnt/backups

**Cloud Storage:**

.. code-block:: bash

   # Sync to S3
   aws s3 sync backups/ s3://mybucket/ddf-backups/
   
   # Sync to Google Drive (using rclone)
   rclone sync backups/ gdrive:ddf-backups/

Version Control Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integrate with Git for better tracking:

.. code-block:: bash

   # Initialize Git in project
   cd /path/to/project
   git init
   
   # Create .gitignore
   echo "backups/" >> .gitignore
   
   # Commit before DDF changes
   git add docker-compose.yml
   git commit -m "Before DDF edit"
   
   # After DDF changes
   git add docker-compose.yml
   git commit -m "After editing service: myservice"

Automated Git Integration:

.. code-block:: bash

   #!/bin/bash
   # ddf_with_git.sh
   
   # Auto-commit before DDF operation
   git add docker-compose.yml
   git commit -m "Auto-backup before: $*"
   
   # Run DDF
   ddf "$@"
   
   # Auto-commit after
   git add docker-compose.yml
   git commit -m "After DDF: $*"

Recovery Scenarios
------------------

Accidental Deletion
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Service was deleted by mistake
   ddf myservice -rm
   
   # Find the backup
   ls -lt backups/ | head -n 1
   
   # Restore
   cp backups/docker-compose.yml.remove_service.myservice.20251204_150131.backup docker-compose.yml

Bad Edit
~~~~~~~~

.. code-block:: bash

   # Edited service but made mistakes
   ddf myservice -E
   # ... made errors in editor ...
   
   # DDF detects YAML error and offers restoration:
   # ❌ YAML syntax error: ...
   # 📋 Available backups for docker-compose.yml:
   # 1. docker-compose.yml.edit_service.myservice.20251204_150131.backup
   # 
   # 🔄 Would you like to restore from a backup? (1/n): 1
   # ✅ Backup restored successfully

System Crash
~~~~~~~~~~~~

.. code-block:: bash

   # System crashed during edit
   # Find most recent backup
   ls -lt backups/docker-compose.yml.* | head -n 1
   
   # Restore
   cp backups/docker-compose.yml.edit_service.api.20251204_150131.backup docker-compose.yml
   
   # Verify
   ddf -L

Compare Versions
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Compare current with backup
   diff docker-compose.yml backups/docker-compose.yml.edit_service.web.20251204_150131.backup
   
   # Or use a better diff tool
   vimdiff docker-compose.yml backups/docker-compose.yml.edit_service.web.20251204_150131.backup
   
   # Or graphical diff
   meld docker-compose.yml backups/docker-compose.yml.edit_service.web.20251204_150131.backup

Troubleshooting
---------------

Backup Not Created
~~~~~~~~~~~~~~~~~~

**Check Backup Directory:**

.. code-block:: bash

   # Verify directory exists and is writable
   ls -ld backups/
   touch backups/test
   rm backups/test

**Check Configuration:**

.. code-block:: ini

   [backup]
   # Ensure path is correct and absolute
   directory = /full/path/to/backups

**Check Permissions:**

.. code-block:: bash

   # Fix permissions
   chmod 755 backups/
   
   # Fix ownership
   chown -R $USER:$USER backups/

Backup Directory Full
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check disk space
   df -h backups/
   
   # Clean old backups
   find backups/ -name "*.backup" -mtime +7 -delete
   
   # Or move to archive
   mkdir -p archive
   find backups/ -name "*.backup" -mtime +7 -exec mv {} archive/ \;

Cannot Restore Backup
~~~~~~~~~~~~~~~~~~~~~~

**File Locked:**

.. code-block:: bash

   # Check if file is in use
   lsof docker-compose.yml
   
   # Close applications using the file

**Permission Issues:**

.. code-block:: bash

   # Check permissions
   ls -l docker-compose.yml
   
   # Fix if needed
   chmod 644 docker-compose.yml

**Corrupted Backup:**

.. code-block:: bash

   # Verify backup is valid YAML
   python -c "import yaml; yaml.safe_load(open('backups/file.backup'))"
   
   # Try older backup
   ls -lt backups/ | head -n 5

For more information, see :doc:`api/backup`.