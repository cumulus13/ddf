Editor API
==========

This section documents the editor management functionality.

EditorManager Class
-------------------

Manages different types of editors and their behaviors.

.. autoclass:: ddf.EditorManager
   :members:
   :undoc-members:
   :show-inheritance:
   
   Editor Type Detection
   ~~~~~~~~~~~~~~~~~~~~~
   
   .. automethod:: get_editor_type
      :no-index:
   
   File Editing
   ~~~~~~~~~~~~
   
   .. automethod:: edit_file_with_monitoring
      :no-index:
   
   Specialized Editors
   ~~~~~~~~~~~~~~~~~~~
   
   .. automethod:: _edit_with_sublime_wait
      :no-index:

   .. automethod:: _edit_with_sublime_alternative
      :no-index:

   .. automethod:: _edit_with_detached_terminal
      :no-index:

   .. automethod:: _edit_with_file_monitoring
      :no-index:
   
   Utility Methods
   ~~~~~~~~~~~~~~~
   
   .. automethod:: _get_file_hash
      :no-index:

   .. automethod:: cleanup_temp_files
      :no-index:

Editor Types
------------

Blocking Editors
~~~~~~~~~~~~~~~~

Editors that block until closed:

.. code-block:: python

   BLOCKING_EDITORS = [
       'nano',
       'vim',
       'nvim',
       'emacs',
       'vi'
   ]

**Characteristics:**

* Terminal blocks until editor closes
* Changes detected immediately after close
* Simple workflow
* No monitoring needed

Non-Blocking Editors
~~~~~~~~~~~~~~~~~~~~~

GUI editors that return immediately:

.. code-block:: python

   NON_BLOCKING_EDITORS = [
       'sublime_text',
       'subl',
       'code',
       'atom',
       'notepad++'
   ]

**Characteristics:**

* Command returns immediately
* File monitoring required
* User can work on multiple files
* Complex workflow

Special Handling
~~~~~~~~~~~~~~~~

Editors requiring special handling:

.. code-block:: python

   SPECIAL_HANDLING = {
       'subl': 'sublime_wait',
       'sublime_text': 'sublime_wait'
   }

**Sublime Text:**

* Supports ``--wait`` flag
* Blocks until tab/window closed
* Best of both worlds

Usage Examples
--------------

Basic File Editing
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   
   def on_save(file_path, changed):
       if changed:
           print(f"File changed: {file_path}")
       else:
           print(f"No changes: {file_path}")
   
   # Edit file
   success = EditorManager.edit_file_with_monitoring(
       file_path=Path('/path/to/file.yml'),
       callback_on_save=on_save,
       timeout=300
   )

With Detached Mode
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   
   # Open in new terminal window
   success = EditorManager.edit_file_with_monitoring(
       file_path=Path('/path/to/file.yml'),
       callback_on_save=lambda p, c: print(f"Changed: {c}"),
       timeout=600,
       detached=True  # Opens in new terminal
   )

Custom Callback
~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   import yaml
   
   def validate_and_process(file_path, changed):
       if not changed:
           print("No changes made")
           return
       
       try:
           # Validate YAML
           with open(file_path, 'r') as f:
               data = yaml.safe_load(f)
           
           print(f"✅ Valid YAML with {len(data)} keys")
           
           # Process data
           # ... your logic ...
           
       except yaml.YAMLError as e:
           print(f"❌ Invalid YAML: {e}")
       except Exception as e:
           print(f"❌ Error: {e}")
   
   # Edit with validation
   EditorManager.edit_file_with_monitoring(
       file_path=Path('/path/to/file.yml'),
       callback_on_save=validate_and_process,
       timeout=300
   )

Multiple Files
~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   import threading
   
   def edit_multiple_files(files):
       """Edit multiple files in parallel."""
       threads = []
       
       for file_path in files:
           def edit_file(path):
               EditorManager.edit_file_with_monitoring(
                   file_path=Path(path),
                   callback_on_save=lambda p, c: print(f"Done: {p}"),
                   detached=True
               )
           
           thread = threading.Thread(target=edit_file, args=(file_path,))
           thread.start()
           threads.append(thread)
       
       # Wait for all edits to complete
       for thread in threads:
           thread.join()
   
   # Usage
   files = [
       'docker-compose.yml',
       'Dockerfile',
       'entrypoint.sh'
   ]
   edit_multiple_files(files)

File Hash Utilities
-------------------

Get File Hash
~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   
   # Get SHA256 hash
   file_hash = EditorManager._get_file_hash(Path('/path/to/file'))
   print(f"Hash: {file_hash}")
   
   # Compare hashes
   hash1 = EditorManager._get_file_hash(Path('file1.txt'))
   hash2 = EditorManager._get_file_hash(Path('file2.txt'))
   
   if hash1 == hash2:
       print("Files are identical")
   else:
       print("Files differ")

Detect Changes
~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   
   file_path = Path('/path/to/file.yml')
   
   # Get original hash
   original_hash = EditorManager._get_file_hash(file_path)
   
   # User edits file...
   input("Press Enter after editing...")
   
   # Check for changes
   new_hash = EditorManager._get_file_hash(file_path)
   
   if new_hash != original_hash:
       print("✅ File was modified")
   else:
       print("ℹ️ No changes detected")

Cleanup Operations
------------------

Cleanup Temp Files
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   
   # Cleanup files older than 24 hours (default)
   EditorManager.cleanup_temp_files()
   
   # Cleanup files older than 1 hour
   EditorManager.cleanup_temp_files(max_age_hours=1)
   
   # Cleanup files older than 7 days
   EditorManager.cleanup_temp_files(max_age_hours=168)

Scheduled Cleanup
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import schedule
   import time
   from ddf import EditorManager
   
   def cleanup_job():
       """Scheduled cleanup job."""
       print("Running cleanup...")
       EditorManager.cleanup_temp_files(max_age_hours=24)
       print("Cleanup complete")
   
   # Schedule cleanup daily at 2 AM
   schedule.every().day.at("02:00").do(cleanup_job)
   
   # Run scheduler
   while True:
       schedule.run_pending()
       time.sleep(3600)  # Check every hour

Advanced Features
-----------------

Detached Terminal
~~~~~~~~~~~~~~~~~

Opens editor in new terminal window:

**Windows:**

.. code-block:: python

   # Opens in new cmd window
   # Command: cmd /c start cmd /k editor file.txt

**macOS:**

.. code-block:: python

   # Opens in Terminal.app
   # Uses AppleScript

**Linux:**

.. code-block:: python

   # Tries multiple terminal emulators:
   # - gnome-terminal
   # - konsole
   # - xterm
   # - alacritty
   # - kitty
   # - terminator

Sublime Text Wait Mode
~~~~~~~~~~~~~~~~~~~~~~

Special handling for Sublime Text:

.. code-block:: python

   # 1. Try --wait flag first
   subl --wait file.txt
   
   # 2. If fails, use alternative method:
   #    - Create temp file
   #    - Monitor for changes
   #    - Copy back to original

File Monitoring
~~~~~~~~~~~~~~~

For non-blocking editors:

.. code-block:: python

   # Monitoring loop:
   while True:
       current_hash = get_file_hash()
       
       if current_hash != last_hash:
           # Change detected
           callback(file_path, changed=True)
           break
       
       if timeout_reached:
           callback(file_path, changed=False)
           break
       
       time.sleep(1)

Configuration
-------------

Editor Priority
~~~~~~~~~~~~~~~

Configure editor preference in ``ddf.ini``:

.. code-block:: ini

   [editor]
   names = nvim, vim, nano, subl, code

**Behavior:**

1. DDF tries ``nvim`` first
2. If not found, tries ``vim``
3. If not found, tries ``nano``
4. ... and so on

Platform-Specific Config
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   # Linux/macOS
   [editor]
   names = nvim, vim, nano
   
   # Windows
   [editor]
   names = C:\msys64\usr\bin\nano.exe, nvim, notepad++
   
   # GUI preference
   [editor]
   names = subl, code, atom, vim

Error Handling
--------------

Editor Not Found
~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   
   try:
       success = EditorManager.edit_file_with_monitoring(
           file_path=Path('file.txt'),
           callback_on_save=lambda p, c: None
       )
       
       if not success:
           print("❌ No suitable editor found")
           
   except FileNotFoundError as e:
       print(f"❌ Editor not found: {e}")

Timeout Handling
~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   
   def on_save(file_path, changed):
       if changed:
           print("✅ Changes saved")
       else:
           print("⏰ Timeout - no changes detected")
   
   # Set shorter timeout
   EditorManager.edit_file_with_monitoring(
       file_path=Path('file.txt'),
       callback_on_save=on_save,
       timeout=60  # 1 minute
   )

Permission Errors
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   import os
   
   file_path = Path('/path/to/file.txt')
   
   # Check if writable
   if not os.access(file_path, os.W_OK):
       print("❌ File is not writable")
   else:
       EditorManager.edit_file_with_monitoring(
           file_path=file_path,
           callback_on_save=lambda p, c: print("Done")
       )

Integration Examples
--------------------

With DDF Edit Operations
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager, EnhancedBackupManager, DDF
   from pathlib import Path
   
   def safe_edit_service(service_name):
       compose_file = Path('/path/to/docker-compose.yml')
       
       # Create backup
       backup = EnhancedBackupManager.create_backup_with_context(
           file_path=str(compose_file),
           operation_type='edit_service',
           context_info=service_name
       )
       
       # Extract service to temp file
       # ... create temp file with service config ...
       
       # Edit
       def on_save(temp_path, changed):
           if changed:
               # Update main file
               DDF.update_service_from_temp(service_name, temp_path)
               print("✅ Service updated")
       
       EditorManager.edit_file_with_monitoring(
           file_path=temp_file,
           callback_on_save=on_save
       )

Custom Editor Wrapper
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ddf import EditorManager
   from pathlib import Path
   
   class CustomEditor:
       def __init__(self, editor='vim'):
           self.editor = editor
       
       def edit(self, file_path, **kwargs):
           """Edit file with custom behavior."""
           # Pre-edit hook
           print(f"Opening {file_path} with {self.editor}...")
           
           # Edit
           success = EditorManager.edit_file_with_monitoring(
               file_path=Path(file_path),
               callback_on_save=self._on_save,
               **kwargs
           )
           
           # Post-edit hook
           if success:
               print("Edit completed")
           
           return success
       
       def _on_save(self, file_path, changed):
           if changed:
               print(f"✅ Saved: {file_path}")
               # Custom post-save processing
               self.process_file(file_path)
       
       def process_file(self, file_path):
           # Custom processing logic
           pass
   
   # Usage
   editor = CustomEditor(editor='nvim')
   editor.edit('myfile.txt', timeout=600, detached=True)

For more information, see :doc:`../usage` and :doc:`../configuration`.