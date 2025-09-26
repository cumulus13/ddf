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
    SPECIAL_HANDLING = {
        'subl': 'sublime_wait',
        'sublime_text': 'sublime_wait'
    }
    
    @classmethod
    def get_editor_type(cls, editor_cmd):
        """Determine if editor is blocking or non-blocking."""
        editor_name = os.path.basename(editor_cmd).lower()
        
        # Check for special handling first
        if editor_name in cls.SPECIAL_HANDLING:
            return cls.SPECIAL_HANDLING[editor_name]
        elif any(blocked in editor_name for blocked in cls.BLOCKING_EDITORS):
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
        
        print(f"EDITORS: {editors}")  # Debug output
        
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
                    elif editor_type == 'sublime_wait':
                        # Special handling for Sublime Text with wait flag
                        return cls._edit_with_sublime_wait(
                            editor, file_path, callback_on_save, original_hash
                        )
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
    def _edit_with_sublime_wait(cls, editor, file_path, callback, original_hash):
        """Special handling for Sublime Text with --wait flag."""
        try:
            # Try with --wait flag first
            console.print(f"🔧 [cyan]Starting {editor} with --wait flag for {file_path.name}[/]")
            result = subprocess.run([editor, '--wait', str(file_path)], check=True, timeout=600)
            
            # Check for changes after editor closes
            new_hash = cls._get_file_hash(file_path)
            changed = new_hash != original_hash
            
            if callback:
                callback(file_path, changed=changed)
                
            return True
            
        except subprocess.TimeoutExpired:
            console.print("⏰ [yellow]Sublime Text editing timeout (10 minutes)[/]")
            # Still check for changes
            new_hash = cls._get_file_hash(file_path)
            if callback and new_hash != original_hash:
                callback(file_path, changed=True)
            return True
            
        except subprocess.CalledProcessError:
            # If --wait doesn't work, try alternative approach
            console.print(f"⚠️ [yellow]--wait flag not supported, using alternative method[/]")
            return cls._edit_with_sublime_alternative(editor, file_path, callback, original_hash)
    
    @classmethod 
    def _edit_with_sublime_alternative(cls, editor, file_path, callback, original_hash):
        """Alternative method for Sublime Text without --wait flag."""
        # Create a more permanent temp file in a known location
        temp_dir = Path.home() / '.ddf_temp'
        temp_dir.mkdir(exist_ok=True)
        
        # Use a more descriptive filename
        timestamp = int(time.time())
        service_name = file_path.stem.split('.')[-1] if '.' in file_path.stem else 'service'
        temp_file = temp_dir / f"edit_{service_name}_{timestamp}.yml"
        
        # Copy content to the new temp file
        shutil.copy2(file_path, temp_file)
        
        console.print(f"📝 [cyan]Created temp file: {temp_file}[/]")
        console.print(f"🔧 [cyan]Opening in {editor}...[/]")
        console.print(f"💡 [yellow]Please save and close the file when done editing[/]")
        console.print(f"⏱️ [yellow]Waiting for changes... (Press Ctrl+C to cancel)[/]")
        
        # Start Sublime Text
        try:
            subprocess.Popen([editor, str(temp_file)])
        except Exception as e:
            console.print(f"❌ [red]Failed to start {editor}:[/] {e}")
            return False
        
        # Monitor the temp file for changes
        last_hash = original_hash
        start_time = time.time()
        
        try:
            while True:
                time.sleep(1)  # Check every second
                
                current_hash = cls._get_file_hash(temp_file)
                
                if current_hash != last_hash:
                    console.print("✅ [green]File change detected![/]")
                    console.print("⏳ [cyan]Waiting 2 seconds for additional changes...[/]")
                    
                    # Wait a bit more to catch any additional saves
                    time.sleep(2)
                    final_hash = cls._get_file_hash(temp_file)
                    
                    if final_hash != original_hash:
                        # Copy changes back to original file
                        shutil.copy2(temp_file, file_path)
                        
                        if callback:
                            callback(file_path, changed=True)
                        
                        console.print(f"✅ [green]Changes applied successfully![/]")
                    else:
                        if callback:
                            callback(file_path, changed=False)
                        console.print("ℹ️ [yellow]No final changes detected[/]")
                    
                    break
                
                # Timeout after 10 minutes
                if time.time() - start_time > 600:
                    console.print("⏰ [yellow]Timeout reached. Checking for any changes...[/]")
                    final_hash = cls._get_file_hash(temp_file)
                    
                    if final_hash != original_hash:
                        shutil.copy2(temp_file, file_path)
                        if callback:
                            callback(file_path, changed=True)
                        console.print("✅ [green]Changes found and applied![/]")
                    else:
                        if callback:
                            callback(file_path, changed=False)
                        console.print("ℹ️ [yellow]No changes made[/]")
                    break
                    
        except KeyboardInterrupt:
            console.print("\n⚠️ [yellow]Monitoring cancelled by user[/]")
            # Still check for changes before exiting
            final_hash = cls._get_file_hash(temp_file)
            if final_hash != original_hash:
                response = console.input("💾 [cyan]Changes detected. Apply them? (y/N): [/]")
                if response.lower() in ['y', 'yes']:
                    shutil.copy2(temp_file, file_path)
                    if callback:
                        callback(file_path, changed=True)
                    console.print("✅ [green]Changes applied![/]")
                else:
                    if callback:
                        callback(file_path, changed=False)
                    console.print("❌ [red]Changes discarded[/]")
            else:
                if callback:
                    callback(file_path, changed=False)
                console.print("ℹ️ [yellow]No changes to apply[/]")
        
        finally:
            # Clean up temp file
            try:
                temp_file.unlink()
                console.print(f"🧹 [cyan]Cleaned up temp file[/]")
            except:
                pass
        
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
    
    @staticmethod
    def cleanup_temp_files(max_age_hours=24):
        """Clean up old temporary files from .ddf_temp directory."""
        temp_dir = Path.home() / '.ddf_temp'
        if not temp_dir.exists():
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        try:
            for temp_file in temp_dir.glob('edit_*'):
                if temp_file.is_file():
                    file_age = current_time - temp_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        temp_file.unlink()
                        cleaned_count += 1
            
            if cleaned_count > 0:
                console.print(f"🧹 [cyan]Cleaned up {cleaned_count} old temporary files[/]")
                
        except Exception as e:
            console.print(f"⚠️ [yellow]Warning: Could not clean temp files: {e}[/]")

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