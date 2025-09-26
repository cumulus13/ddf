import os
import time
import threading
import hashlib
import shutil
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
import datetime

console = Console()

class FileChangeHandler(FileSystemEventHandler):
    """Handles file change events for monitoring edited files."""
    
    def __init__(self, file_path, callback, debounce_time=1.0):
        self.file_path = Path(file_path).resolve()
        self.callback = callback
        self.debounce_time = debounce_time
        self.last_modified = 0
        self._lock = threading.Lock()
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        event_path = Path(event.src_path).resolve()
        if event_path == self.file_path:
            current_time = time.time()
            with self._lock:
                if current_time - self.last_modified > self.debounce_time:
                    self.last_modified = current_time
                    # Use a timer to debounce rapid successive changes
                    threading.Timer(self.debounce_time, self._execute_callback).start()
    
    def _execute_callback(self):
        """Execute callback after debounce period."""
        try:
            self.callback(self.file_path)
        except Exception as e:
            console.print(f"❌ [red]Error in file change callback:[/] {e}")

class EnhancedBackupManager(BackupManager):
    """Enhanced backup manager with better integration and monitoring."""
    
    @staticmethod
    def create_backup_with_context(file_path, operation_type="edit", context_info=None):
        """
        Create backup with additional context information.
        
        Args:
            file_path: Path to file to backup
            operation_type: Type of operation (edit, update, delete, etc.)
            context_info: Additional context like service name, action type
        """
        if not os.path.isfile(file_path):
            console.print(f"⚠️ [yellow]File does not exist, cannot create backup: {file_path}[/]")
            return None
            
        try:
            backup_dir = EnhancedBackupManager.get_backup_dir()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            
            # Include context info in backup filename
            context_str = f".{context_info}" if context_info else ""
            backup_filename = f"{filename}.{operation_type}{context_str}.{timestamp}.backup"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(file_path, backup_path)
            console.print(f"💾 [cyan]Backup created:[/] {backup_filename}")
            return backup_path
        except Exception as e:
            console.print(f"❌ [red]Failed to create backup:[/] {e}")
            return None
    
    @staticmethod
    def should_create_backup(operation_type):
        """Determine if backup should be created for this operation type."""
        backup_operations = {
            'edit_service', 'edit_dockerfile', 'edit_entrypoint', 'edit_file',
            'remove_service', 'rename_service', 'set_dockerfile', 'new_service',
            'duplicate_service', 'copy_dockerfile_config'
        }
        return operation_type in backup_operations

class EditorManager:
    """Manages different types of editors and their behaviors."""
    
    BLOCKING_EDITORS = ['nano', 'vim', 'nvim', 'emacs']
    NON_BLOCKING_EDITORS = ['sublime_text', 'subl', 'code', 'atom', 'notepad++']
    
    @classmethod
    def get_editor_type(cls, editor_cmd):
        """Determine if editor is blocking or non-blocking."""
        editor_name = os.path.basename(editor_cmd).lower()
        
        if any(blocked in editor_name for blocked in cls.BLOCKING_EDITORS):
            return 'blocking'
        elif any(non_blocked in editor_name for non_blocked in cls.NON_BLOCKING_EDITORS):
            return 'non_blocking'
        else:
            # Default to blocking for unknown editors
            return 'blocking'
    
    @classmethod
    def edit_file_with_monitoring(cls, file_path, callback_on_save=None, timeout=300):
        """
        Edit file with appropriate monitoring based on editor type.
        
        Args:
            file_path: Path to file to edit
            callback_on_save: Function to call when file is saved
            timeout: Timeout for monitoring in seconds (5 minutes default)
        """
        editors = CONFIG.get_config_as_list('editor', 'names') or [
            r'c:\msys64\usr\bin\nano.exe', 'nvim', 'vim', 'subl', 'code'
        ]
        
        file_path = Path(file_path).resolve()
        original_hash = cls._get_file_hash(file_path) if file_path.exists() else None
        
        for editor in editors:
            if shutil.which(editor):
                editor_type = cls.get_editor_type(editor)
                
                try:
                    if editor_type == 'blocking':
                        # For blocking editors, just run and wait
                        result = subprocess.run([editor, str(file_path)], check=True)
                        if callback_on_save:
                            new_hash = cls._get_file_hash(file_path)
                            if new_hash != original_hash:
                                callback_on_save(file_path, changed=True)
                            else:
                                callback_on_save(file_path, changed=False)
                        return True
                    else:
                        # For non-blocking editors, start monitoring
                        return cls._edit_with_file_monitoring(
                            editor, file_path, callback_on_save, timeout, original_hash
                        )
                        
                except subprocess.CalledProcessError as e:
                    console.print(f"❌ [red]Error launching {editor}:[/] {e}")
                    continue
                except Exception as e:
                    console.print(f"❌ [red]Unexpected error with {editor}:[/] {e}")
                    continue
        
        console.print("❌ [red]No suitable editor found.[/]")
        return False
    
    @classmethod
    def _edit_with_file_monitoring(cls, editor, file_path, callback, timeout, original_hash):
        """Start non-blocking editor and monitor file changes."""
        # Start the editor process
        try:
            process = subprocess.Popen([editor, str(file_path)])
            console.print(f"🔧 [cyan]Started {editor} for {file_path.name}[/]")
            console.print(f"📝 [yellow]Monitoring file changes... (timeout: {timeout}s)[/]")
        except Exception as e:
            console.print(f"❌ [red]Failed to start {editor}:[/] {e}")
            return False
        
        # Set up file monitoring
        monitor_result = {'changed': False, 'completed': False}
        
        def on_file_change(changed_path):
            new_hash = cls._get_file_hash(changed_path)
            if new_hash != original_hash:
                monitor_result['changed'] = True
                console.print(f"✅ [green]File change detected: {changed_path.name}[/]")
                if callback:
                    callback(changed_path, changed=True)
                monitor_result['completed'] = True
        
        # Start file system watcher
        event_handler = FileChangeHandler(file_path, on_file_change)
        observer = Observer()
        observer.schedule(event_handler, str(file_path.parent), recursive=False)
        observer.start()
        
        try:
            # Wait for either file change or timeout
            start_time = time.time()
            while not monitor_result['completed'] and (time.time() - start_time) < timeout:
                time.sleep(0.5)
                
                # Check if editor process is still running
                if process.poll() is not None:
                    # Process ended, check for changes one last time
                    new_hash = cls._get_file_hash(file_path)
                    if new_hash != original_hash and not monitor_result['changed']:
                        monitor_result['changed'] = True
                        if callback:
                            callback(file_path, changed=True)
                    elif not monitor_result['changed'] and callback:
                        callback(file_path, changed=False)
                    break
            
            if not monitor_result['completed'] and (time.time() - start_time) >= timeout:
                console.print(f"⏰ [yellow]Monitoring timeout reached ({timeout}s)[/]")
                # Check final state
                new_hash = cls._get_file_hash(file_path)
                if new_hash != original_hash and callback:
                    callback(file_path, changed=True)
                elif callback:
                    callback(file_path, changed=False)
            
        finally:
            observer.stop()
            observer.join()
            
            # Clean up process if still running
            if process.poll() is None:
                console.print("🔄 [cyan]Editor still running in background[/]")
            
        return True
    
    @staticmethod
    def _get_file_hash(file_path):
        """Get SHA256 hash of file content."""
        try:
            if not file_path.exists():
                return None
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None

class EnhancedDDF(DDF):
    """Enhanced DDF class with improved backup and editor handling."""
    
    @classmethod
    def edit_service_enhanced(cls, file_path=None, service_name=None):
        """Enhanced edit_service with better backup and monitoring."""
        file_path = file_path or CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        
        if not service_name:
            console.print("❌ [red]No service name provided for editing.[/]")
            return

        if not os.path.isfile(file_path):
            console.print(f"❌ [red]YAML file not found:[/] {file_path}")
            return

        # Create backup before any changes
        backup_path = EnhancedBackupManager.create_backup_with_context(
            file_path, 
            operation_type="edit_service",
            context_info=service_name
        )

        # Load and prepare service data
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
        except Exception as e:
            console.print(f"❌ [red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        matched = [svc for svc in services if fnmatch.fnmatch(svc, service_name) or service_name in svc]
        
        if not matched:
            console.print(f"❌ [yellow]Service pattern '{service_name}' not found.[/]")
            return

        if len(matched) > 1:
            # Handle multiple matches
            for index, svc in enumerate(matched, start=1):
                console.print(f"{index}. [bold cyan]{svc}[/]")
            
            try:
                q = console.input(f"🔍 [yellow]Multiple services found. Select service (1-{len(matched)}): [/]")
                index = int(q) - 1
                if 0 <= index < len(matched):
                    matched = [matched[index]]
                else:
                    console.print("❌ [red]Invalid selection.[/]")
                    return
            except (ValueError, KeyboardInterrupt):
                console.print("❌ [red]Invalid input or cancelled.[/]")
                return

        # Edit each matched service
        for svc in matched:
            svc_data = services[svc]
            
            # Create temporary file
            with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.yml') as tf:
                temp_path = Path(tf.name)
                yaml.dump({svc: svc_data}, tf, sort_keys=False, allow_unicode=True)

            def on_save_callback(changed_path, changed=False):
                if changed:
                    try:
                        with open(changed_path, 'r') as f:
                            edited = yaml.safe_load(f)
                        
                        if edited and svc in edited:
                            content['services'][svc] = edited[svc]
                            
                            # Save main file
                            with open(file_path, 'w') as f:
                                yaml.dump(content, f, sort_keys=False, allow_unicode=True)
                            
                            console.print(f"✅ [green]Service '{svc}' updated successfully![/]")
                        else:
                            console.print(f"❌ [red]Invalid service format after editing '{svc}'[/]")
                            
                    except Exception as e:
                        console.print(f"❌ [red]Error updating service:[/] {e}")
                        # Offer backup restoration
                        if backup_path and EnhancedBackupManager.prompt_restore_backup(file_path):
                            console.print("✅ [green]Backup restored successfully[/]")
                else:
                    console.print(f"ℹ️ [yellow]No changes made to service '{svc}'[/]")
                
                # Clean up temp file
                try:
                    temp_path.unlink()
                except:
                    pass

            # Start editing with monitoring
            console.print(f"📝 [cyan]Opening service '{svc}' for editing...[/]")
            EditorManager.edit_file_with_monitoring(
                temp_path,
                callback_on_save=on_save_callback,
                timeout=600  # 10 minutes timeout
            )

    @classmethod
    def edit_dockerfile_enhanced(cls, path=None, service_name=None):
        """Enhanced edit_dockerfile with monitoring support."""
        dockerfile_path = None

        if service_name:
            dockerfile_path = cls.get_dockerfile(service_name)
        else:
            dockerfile_path = path

        if not dockerfile_path:
            console.print("❌ [red]No Dockerfile path provided or found.[/]")
            return

        # Create backup
        backup_path = EnhancedBackupManager.create_backup_with_context(
            dockerfile_path,
            operation_type="edit_dockerfile",
            context_info=service_name
        )

        def on_save_callback(changed_path, changed=False):
            if changed:
                console.print(f"✅ [green]Dockerfile updated: {changed_path}[/]")
            else:
                console.print("ℹ️ [yellow]No changes made to Dockerfile[/]")

        console.print(f"📝 [cyan]Opening Dockerfile for editing...[/]")
        success = EditorManager.edit_file_with_monitoring(
            dockerfile_path,
            callback_on_save=on_save_callback,
            timeout=600
        )
        
        if not success:
            console.print("❌ [red]Failed to open Dockerfile for editing[/]")

    @classmethod
    def edit_entrypoint_enhanced(cls, service_name):
        """Enhanced edit_entrypoint with monitoring support."""
        entrypoint_path = cls.read_entrypoint(service_name, read=False)
        if not entrypoint_path:
            console.print(f"❌ [red]No entrypoint script found for service '{service_name}'.[/]")
            return

        # Create backup
        backup_path = EnhancedBackupManager.create_backup_with_context(
            entrypoint_path,
            operation_type="edit_entrypoint", 
            context_info=service_name
        )

        def on_save_callback(changed_path, changed=False):
            if changed:
                console.print(f"✅ [green]Entrypoint script updated: {changed_path}[/]")
            else:
                console.print("ℹ️ [yellow]No changes made to entrypoint script[/]")

        console.print(f"📝 [cyan]Opening entrypoint script for editing...[/]")
        EditorManager.edit_file_with_monitoring(
            entrypoint_path,
            callback_on_save=on_save_callback,
            timeout=600
        )

    @classmethod
    def remove_service_enhanced(cls, service_name):
        """Enhanced remove_service with backup."""
        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        
        # Create backup before removal
        backup_path = EnhancedBackupManager.create_backup_with_context(
            file_path,
            operation_type="remove_service",
            context_info=service_name
        )
        
        # Proceed with original removal logic
        cls.remove_service(service_name)

    @classmethod
    def usage_enhanced(cls):
        """Enhanced usage method with backup-aware operations."""
        # Add backup-related arguments to parser
        # This would extend the original usage method
        # Implementation would mirror original but use enhanced methods
        pass

# Example of how to integrate with existing code:
def integrate_enhanced_backup():
    """
    Integration guide for existing DDF methods.
    Replace method calls with enhanced versions:
    """
    examples = {
        'edit_service': 'EnhancedDDF.edit_service_enhanced',
        'edit_dockerfile': 'EnhancedDDF.edit_dockerfile_enhanced', 
        'edit_entrypoint': 'EnhancedDDF.edit_entrypoint_enhanced',
        'remove_service': 'EnhancedDDF.remove_service_enhanced'
    }
    return examples