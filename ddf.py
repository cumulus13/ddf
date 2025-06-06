#!/usr/bin/env python
import yaml
import os
import sys
import argparse
from rich.console import Console
from rich.syntax import Syntax
from pydebugger.debug import debug
import hashlib
from configset import configset
from rich_argparse import RichHelpFormatter, _lazy_rich as rr
from rich.syntax import Syntax
from typing import ClassVar
from typing import List
import fnmatch
import subprocess
from pathlib import Path
import shutil
import clipboard
import tempfile
import shlex

console = Console()
CONFIGFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ddf.ini')
CONFIG = configset(CONFIGFILE)

class CustomRichHelpFormatter(RichHelpFormatter):
    """A custom RichHelpFormatter with modified styles."""

    styles: ClassVar[dict[str, rr.StyleType]] = {
        "argparse.args": "bold #FFFF00",  # Changed from cyan
        "argparse.groups": "#AA55FF",   # Changed from dark_orange
        "argparse.help": "bold #00FFFF",    # Changed from default
        "argparse.metavar": "bold #FF00FF", # Changed from dark_cyan
        "argparse.syntax": "underline", # Changed from bold
        "argparse.text": "white",   # Changed from default
        "argparse.prog": "bold #00AAFF italic",     # Changed from grey50
        "argparse.default": "bold", # Changed from italic
    }

class DDF:

    _file_cache = {}

    @classmethod
    def open_file(cls, file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        if not file_path.endswith(('.yml', '.yaml')):
            raise ValueError(f"The file {file_path} is not a YAML file.")
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"The file {file_path} is not readable.")
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"The file {file_path} is empty.")

        # Buat hash dari isi file
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Cek cache
        if file_hash in cls._file_cache:
            return cls._file_cache[file_hash]

        # Parse YAML jika belum ada di cache
        content = yaml.load(file_bytes.decode('utf-8'), Loader=yaml.FullLoader)
        if not content:
            raise ValueError(f"The file {file_path} is empty or contains invalid YAML.")
        cls._file_cache[file_hash] = content
        return content
    
    @classmethod
    def show_service_detail(cls, content, service):
        services = content.get('services', {})
        # Support the pattern/wildcard and substring
        matched = [
            svc for svc in services
            if fnmatch.fnmatch(svc, service) or service in svc
        ]
        if not matched:
            console.print(f"[yellow]Service pattern '{service}' not found.[/]")
            return
        for svc in matched:
            service_val = services.get(svc)
            console.print(f"[bold cyan]Configuration for service '{svc}':[/]")
            yaml_str = yaml.dump(service_val, sort_keys=False, allow_unicode=True)
            syntax = Syntax(yaml_str, "yaml", theme="fruity", line_numbers=True)
            console.print(syntax)
            
    @classmethod
    def list_service_ports(cls, content, service):
        services = content.get('services', {})
        # debug(services = services)
        service_val = services.get(service)
        if not isinstance(service_val, dict):
            console.print(f"[yellow]Service '{service}' is not a dictionary or has no ports defined.[/]")
            return
        ports = service_val.get('ports', [])
        if not ports:
            console.print(f"[yellow]No ports found for service:[/] {service}")
            return
        console.print(f"[bold cyan]Ports for service '{service}':[/]")
        for port in ports:
            console.print(f"• [green]{port}[/]")

    @classmethod
    def find_duplicate_port(cls, content, target_service=None):
        if content is None or not isinstance(content, dict):
            raise ValueError("Invalid YAML content.")

        duplicates = []
        seen_host_ports = {}

        for service, value in content.get('services', {}).items():
            if not isinstance(value, dict):
                continue  # skip jika value bukan dict
            ports = value.get('ports', [])
            if all(isinstance(x, str) and ':' in x for x in ports):
                parsed_ports = []
                for x in ports:
                    hp, cp = x.split(':')
                    hp_proto = f"{hp}/tcp" if '/' not in hp and '/udp' not in cp else f"{hp}/udp" if '/udp' in cp else f"{hp}/tcp"
                    cp_proto = cp if '/' in cp else f"{cp}/tcp"
                    parsed_ports.append((hp_proto, cp_proto))
                
                for host_port, container_port in parsed_ports:
                    if host_port in seen_host_ports:
                        existing = seen_host_ports[host_port]
                        duplicates.append((f"{service}/ports/{host_port}", f"{existing}/ports/{host_port}", host_port))
                    else:
                        seen_host_ports[host_port] = service

        for d in duplicates:
            s1, _, port1, protocol1 = d[0].split("/")
            s2, _, port2, protocol2 = d[1].split("/")

            if target_service and target_service not in (s1, s2):
                continue

            console.print(
                f"[bold #00FFFF]{s1}[/]/"
                f"[white on #0000FF]{port1}[/]/"
                f"[black on #55FF00]{protocol1}[/] "
                f"[bold #FFAA00]-->[/] "
                f"[bold #00FFFF]{s2}[/]/"
                f"[white on #550000]{port2}[/]/"
                f"[black on #55FF00]{protocol2}[/] "
            )
            
    @classmethod
    def find_port(cls, content, port):
        services = content.get('services', {})
        found_any = False
        for service, value in services.items():
            if not isinstance(value, dict):
                continue
            ports = value.get('ports', [])
            if not ports:
                continue
            matched_ports = []
            found_in_service: List[str] = []
            for p in ports:
                p1, p2 = p.split(":")
                if p1.strip() == port or p2.strip() == port:
                    matched_ports.append(f"[white on #550000]{p1}[/]:[white on #550000]{p2}[/]")
                    found_in_service.append(service)
                else:
                    matched_ports.append(p)
            if list(set(found_in_service)):
                found_any = True
                console.print(f"- [bold cyan]{service}[/]:")
                console.print("  ports:")
                for mp in matched_ports:
                    console.print(f"    - {mp}")
        if not found_any:
            console.print(f"[black in #FFFF00]No service found with port {port}[/]")

    @classmethod
    def check_duplicate_port(cls, content, port):
        """
        Cek apakah port tertentu duplicate di antara semua service.
        """
        services = content.get('services', {})
        found = []
        for service, value in services.items():
            if not isinstance(value, dict):
                continue
            ports = value.get('ports', [])
            for p in ports:
                # Support format host:container or just port
                parts = p.split(":")
                # if port in [x.strip() for x in parts]:
                if port == parts[0].strip():
                    found.append((service, p))
        if len(found) > 1:
            console.print(f"[white on red]Port {port} is DUPLICATE in these services:[/]")
            for svc, p in found:
                console.print(f"  - [bold cyan]{svc}[/]: [yellow]{p}[/]")
        elif len(found) == 1:
            svc, p = found[0]
            console.print(f"[bold #00FFFF]Port {port} only found in service:[/] [bold #FFAA00]{svc}[/] ([yellow]{p}[/])")
        else:
            console.print(f"[bold #FFFF00]Port {port} not found in any service.[/]")
        
        return found
            
    @classmethod
    def list_service_devices(cls, content, service=None):
        services = content.get('services', {})
        found = False
        for svc, value in services.items():
            # Dukung pattern/wildcard dan substring
            if service and not (fnmatch.fnmatch(svc, service) or service in svc):
                continue
            if not isinstance(value, dict):
                continue
            # debug(value = value, debug = 1)
            devices = value.get('devices', [])
            if devices:
                found = True
                console.print(f"[bold cyan]{svc}:[/]")
                console.print("  devices:")
                for dev in devices:
                    de = dev.split(':')
                    console.print(f"    [bold #FFAA00]- {de[0]}[/]: [bold #00AAFF]{de[1]}[/]" if len(de) > 1 else f"    [bold #FFAA00]- {dev}[/]")
        if not found:
            if service:
                console.print(f"[yellow]No devices found for service pattern:[/] {service}")
            else:
                console.print(f"[yellow]No devices found in any service.[/]")
                
    @classmethod
    def list_service_volumes(cls, content, service=None):
        """
        List all volumes for a given service.
        """
        services = content.get('services', {})
        found = False
        for svc, value in services.items():
            if service and not (fnmatch.fnmatch(svc, service) or service in svc):
                continue
            if not isinstance(value, dict):
                continue
            volumes = value.get('volumes', [])
            if volumes:
                found = True
                console.print(f"[bold cyan]{svc}:[/]")
                console.print("  volumes:")
                for vol in volumes:
                    vo = vol.split(':')
                    console.print(f"    - [bold #00AAFF]{vo[0]}[/]: [bold #FFAA00]{vo[1]}[/]" if len(vo) > 1 else f"    - [bold #00AAFF]{vol}[/]")
        if not found:
            if service:
                console.print(f"[yellow]No volumes found for service pattern:[/] {service}")
            else:
                console.print(f"[yellow]No volumes found in any service.[/]")
    
    @classmethod
    def list_service_ports(cls, content, service):
        """
        List all ports for a given service.
        """
        services = content.get('services', {})
        service_val = services.get(service)
        if not service_val:
            console.print(f"[yellow]Service '{service}' not found.[/]")
            return
        ports = service_val.get('ports', [])
        if not ports:
            console.print(f"[yellow]No ports found for service:[/] {service}")
            return
        console.print(f"[bold cyan]Ports for service '{service}':[/]")
        for port in ports:
            console.print(f"  - [green]{port}[/]")
    
    @classmethod
    def list_service_names(cls, content):
        services = content.get('services', {})
        if not services:
            console.print("[yellow]No services found in the YAML file.[/]")
            return
        console.print("[bold cyan]Available service names:[/]")
        for service in services.keys():
            console.print(f"  - [bold #00FFFF]{service}[/]")
    
    @classmethod
    def get_dockerfile(cls, service_name):
        """
        Get the Dockerfile path for a given service name.
        """
        root_path = CONFIG.get_config('docker-compose', 'root_path') if CONFIG.get_config('docker-compose', 'root_path') and os.path.isdir(CONFIG.get_config('docker-compose', 'root_path')) else r"c:\PROJECTS" if os.path.isdir(r"c:\PROJECTS") else os.getcwd()
        content = cls.open_file(CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml")
        services = content.get('services', {})
        service_val = services.get(service_name)
        if not service_val:
            console.print(f"[yellow]Service '{service_name}' not found.[/]")
            return None
        dockerfile = service_val.get('build', {}).get('dockerfile')
        build_path = service_val.get('build', {}).get('context', '.')
        debug(build_path = build_path)
        if not dockerfile:
            console.print(f"[yellow]No Dockerfile specified for service '{service_name}'.[/]")
            return None
        return str(Path(root_path) / build_path / dockerfile)
    
    @classmethod
    def read_dockerfile(cls, path = None, service_name = None):
        """
        Read the Dockerfile content from the given path with color syntax by rich.Syntax.
        """
        path = cls.get_dockerfile(service_name) if service_name else path
        if not path:
            console.print("[white on red]No Dockerfile path provided or found.[/]")
            return None
        content = None
        if not os.path.isfile(path):
            console.print(f"[white on red]Dockerfile not found:[/] {path}")
            return None
        try:
            with open(path, 'r') as f:
                content = f.read()
            if not content:
                console.print(f"[yellow]Dockerfile is empty:[/] {path}")
                return None
            syntax = Syntax(content, "dockerfile", theme="fruity", line_numbers=True)
            console.print(f"\n[bold cyan]Dockerfile for service[/] [black on #FFFF00]'{service_name}[/]':\n" if service_name else "[bold cyan]Dockerfile content:[/]\n")
            console.print(syntax)
        except Exception as e:
            console.print(f"[red]Error reading Dockerfile:[/] {e}")
            return None
    
    @classmethod
    def read_entrypoint(cls, service_name, read = True):
        """
        Read the entrypoint script for a given service.
        Tries to resolve the entrypoint path by analyzing COPY instructions in the Dockerfile.
        """
        dockerfile_path = cls.get_dockerfile(service_name)
        if not dockerfile_path:
            console.print(f"[white on red]No Dockerfile found for service '{service_name}'.[/]")
            return None

        # Get docker-compose.yml path and context dir
        compose_file = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        base_dir = os.path.dirname(os.path.abspath(compose_file))
        content = cls.open_file(compose_file)
        services = content.get('services', {})
        service_val = services.get(service_name, {})
        build_ctx = service_val.get('build', {}).get('context', '.')

        entrypoint = None
        entrypoint_src = None

        # Parse Dockerfile for ENTRYPOINT and COPY
        try:
            with open(dockerfile_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            console.print(f"[red]Error reading Dockerfile:[/] {e}")
            return None

        # Find ENTRYPOINT line
        for line in lines:
            line_strip = line.strip()
            if line_strip.startswith('ENTRYPOINT'):
                # Support both ENTRYPOINT ["..."] and ENTRYPOINT "..."
                try:
                    if '[' in line_strip and ']' in line_strip:
                        # ENTRYPOINT ["..."] or ENTRYPOINT ['...']
                        entrypoint_str = line_strip.split('ENTRYPOINT', 1)[1].strip()
                        try:
                            entrypoint_list = yaml.safe_load(entrypoint_str)
                            if isinstance(entrypoint_list, list) and entrypoint_list:
                                entrypoint = entrypoint_list[0]
                            else:
                                entrypoint = entrypoint_str
                        except Exception:
                            entrypoint = entrypoint_str
                    else:
                        # ENTRYPOINT ...
                        entrypoint = line_strip.split('ENTRYPOINT', 1)[1].strip().strip('"').strip("'")
                except Exception:
                    entrypoint = None
                break

        if not entrypoint:
            console.print(f"[yellow]No ENTRYPOINT found in Dockerfile for service '{service_name}'.[/]")
            return None

        # Find COPY line that copies to the entrypoint destination
        for line in lines:
            line_strip = line.strip()
            if line_strip.startswith('COPY') and entrypoint in line_strip:
                # Example: COPY ./entrypoint.sh /usr/local/bin/entrypoint.sh
                parts = line_strip.split()
                if len(parts) >= 3:
                    entrypoint_src = parts[1]
                break

        # If COPY ./entrypoint.sh ... found, resolve the source path
        entrypoint_path = None
        if entrypoint_src and entrypoint_src.startswith('./'):
            entrypoint_src_file = entrypoint_src[2:]  # remove ./
            # debug(entrypoint_src_file = entrypoint_src_file, debug = 1)
            entrypoint_path = os.path.join(base_dir, build_ctx, entrypoint_src_file)
            # debug(entrypoint_path = entrypoint_path, debug = 1)
        elif entrypoint_src:
            entrypoint_path = os.path.join(base_dir, build_ctx, entrypoint_src)
            # debug(entrypoint_path = entrypoint_path, debug = 1)
        else:
            # fallback: try to resolve entrypoint as relative to Dockerfile
            # debug(dockerfile_path = dockerfile_path, debug = 1)
            entrypoint_path = os.path.join(os.path.dirname(dockerfile_path), os.path.basename(entrypoint))
            # debug(entrypoint_path = entrypoint_path, debug = 1)

        # debug(entrypoint = entrypoint, entrypoint_src = entrypoint_src, entrypoint_path = entrypoint_path, debug = 1)
        # debug(entrypoint_path_is_file = os.path.isfile(entrypoint_path), debug = 1)
        # Try absolute path if entrypoint is absolute and not found yet
        if entrypoint_path and not os.path.isfile(entrypoint_path):
            if os.path.isabs(entrypoint):
                alt_path = os.path.join(base_dir, build_ctx, entrypoint.lstrip('/\\'))
                # debug(alt_path = alt_path, debug = 1)
                if os.path.isfile(alt_path):
                    entrypoint_path = alt_path

        # print(f"entrypoint: {entrypoint}")
        # print(f"entrypoint_path: {entrypoint_path}")
        # print(f"os.path.isfile(entrypoint_path): {os.path.isfile(entrypoint_path)}")
        if not entrypoint_path or not os.path.isfile(entrypoint_path):
            console.print(f"[white on red]Entrypoint script not found:[/] {entrypoint_path or entrypoint}")
            return None

        if read:
            try:
                with open(entrypoint_path, 'r') as f:
                    script_content = f.read()
                syntax = Syntax(script_content, "bash", theme="fruity", line_numbers=True)
                console.print(f"\n[bold cyan]Entrypoint script for service[/] '[black on #FFFF00]{service_name}[/]':\n")
                console.print(syntax)
            except Exception as e:
                console.print(f"[red]Error reading entrypoint script:[/] {e}")
        return entrypoint_path
    
    @classmethod
    def edit_entrypoint(cls, service_name):
        """
        Edit the entrypoint script for a given service using nvim, nano, or vim.
        """
        entrypoint_path = cls.read_entrypoint(service_name, read=False)
        if not entrypoint_path:
            console.print(f"[white on red]No entrypoint script found for service '{service_name}'.[/]")
            return None
        
        editors = CONFIG.get_config_as_list('editor', 'names') or [r'c:\msys64\usr\bin\nano.exe', 'nvim', 'vim']
        for editor in editors:
            if shutil.which(editor):
                try:
                    subprocess.run([editor, entrypoint_path], check=True)
                    return
                except subprocess.CalledProcessError as e:
                    console.print(f"[red]Error launching {editor}:[/] {e}")
                    continue
        console.print("[white on red]No suitable editor found to edit the entrypoint script.[/]")
    
    @classmethod
    def edit_dockerfile(cls, path = None, service_name = None):
        """
        Edit the Dockerfile using nvim if exist, if not then nano if exists, if not then vim. use subprocess.run() and check beforehand if the editor is installed.
        """
        path = cls.get_dockerfile(service_name) if service_name else path
        if not path:
            console.print("[white on red]No Dockerfile path provided or found.[/]")
            return None
        if not os.path.isfile(path):
            console.print(f"[white on red]Dockerfile not found:[/] {path}")
            return None
        
        editors = CONFIG.get_config_as_list('editor', 'names') or [r'c:\msys64\usr\bin\nano.exe', 'nvim', 'vim']
        for editor in editors:
            if shutil.which(editor):
                try:
                    subprocess.run([editor, path], check=True)
                    return
                except subprocess.CalledProcessError as e:
                    console.print(f"[red]Error launching {editor}:[/] {e}")
                    continue
        console.print("[white on red]No suitable editor found to edit the Dockerfile.[/]")
        
    @classmethod
    def edit_service(cls, file_path=None, service_name=None):
        """
        Edit a service section in the YAML file using nvim, nano, or vim.
        Only the selected service section will be edited and replaced back.
        """
        
        file_path = file_path or CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not service_name:
            console.print("[white on red]No service name provided for editing.[/]")
            return

        if not os.path.isfile(file_path):
            console.print(f"[white on red]YAML file not found:[/] {file_path}")
            return

        # Load YAML
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
        except Exception as e:
            console.print(f"[red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        # Cari service yang cocok (pattern/wildcard/substring)
        matched = [svc for svc in services if fnmatch.fnmatch(svc, service_name) or service_name in svc]
        if not matched:
            console.print(f"[yellow]Service pattern '{service_name}' not found.[/]")
            return

        for svc in matched:
            svc_data = services[svc]
            # Simpan section ke file sementara
            with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.yml') as tf:
                temp_path = tf.name
                yaml.dump({svc: svc_data}, tf, sort_keys=False, allow_unicode=True)
            # Pilih editor
            editors = CONFIG.get_config_as_list('editor', 'names') or [r'c:\msys64\usr\bin\nano.exe', 'nvim', 'vim']
            for editor in editors:
                if shutil.which(editor):
                    try:
                        subprocess.run([editor, temp_path], check=True)
                        break
                    except subprocess.CalledProcessError as e:
                        console.print(f"[red]Error launching {editor}:[/] {e}")
                        continue
            else:
                console.print("[white on red]No suitable editor found to edit the service section.[/]")
                os.unlink(temp_path)
                return
            # Setelah diedit, baca kembali dan replace section
            try:
                with open(temp_path, 'r') as tf:
                    edited = yaml.safe_load(tf)
                if not edited or svc not in edited:
                    console.print(f"[red]No valid service section found after editing. Skipped update for '{svc}'.[/]")
                    os.unlink(temp_path)
                    continue
                content['services'][svc] = edited[svc]
                os.unlink(temp_path)
            except Exception as e:
                console.print(f"[red]Error reading edited service section:[/] {e}")
                os.unlink(temp_path)
                # Hentikan proses update file utama jika error parsing YAML
                console.print(f"[bold red]YAML not updated due to error above. Please fix indentation (use spaces, not tabs).[/bold red]")
                return  # <--- tambahkan return di sini!

        # Simpan kembali ke file asli
        try:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, sort_keys=False, allow_unicode=True)
            console.print(f"[bold green]Service section(s) updated successfully in {file_path}[/bold green]")
        except Exception as e:
            console.print(f"[red]Error writing YAML file:[/] {e}")
        
    @classmethod
    def copy_service(cls, service_name):
        """
        Copy a service section to the clipboard.
        The service section will be formatted as YAML and copied.
        """

        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not os.path.isfile(file_path):
            console.print(f"[white on red]YAML file not found:[/] {file_path}")
            return

        try:
            content = cls.open_file(file_path)
        except Exception as e:
            console.print(f"[red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        if service_name not in services:
            console.print(f"[yellow]Service '{service_name}' not found.[/]")
            return

        # Get the service section
        service_section = {service_name: services[service_name]}
        yaml_str = yaml.dump(service_section, sort_keys=False, allow_unicode=True)

        # Copy to clipboard
        clipboard.copy(yaml_str)
        console.print(f"[bold green]Service '{service_name}' copied to clipboard successfully.[/]")
    
    @classmethod
    def duplicate_server(cls, service_name, new_service_name):
        """
        Duplicate a service section in the YAML file.
        The new service will have the same configuration as the original service.
        """
        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not os.path.isfile(file_path):
            console.print(f"[white on red]YAML file not found:[/] {file_path}")
            return

        try:
            content = cls.open_file(file_path)
        except Exception as e:
            console.print(f"[red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        if service_name not in services:
            console.print(f"[yellow]Service '{service_name}' not found.[/]")
            return

        # Duplicate the service
        services[new_service_name] = services[service_name]
        content['services'] = services

        # Save back to the file
        try:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, sort_keys=False, allow_unicode=True)
            console.print(f"[bold green]Service '{service_name}' duplicated to '{new_service_name}' successfully in {file_path}[/bold green]")
        except Exception as e:
            console.print(f"[red]Error writing YAML file:[/] {e}")
    
    @classmethod
    def usage(cls):
        default_file = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"

        parser = argparse.ArgumentParser(description="Detect or list ports in a Docker Compose file.", formatter_class=CustomRichHelpFormatter)
        parser.add_argument('service', nargs='?', help="Service name to inspect")
        parser.add_argument('-c', '--file', default=default_file, help="Path to YAML file")
        parser.add_argument('-l', '--list', action='store_true', help="List ports for the given service")
        parser.add_argument('-d', '--detail', action='store_true', help="Show full configuration for the given service")
        parser.add_argument('-f', '--find', metavar='PORT', help="Find port in all services", type=str)
        parser.add_argument('-p', '--port', metavar='PORT', help="Check if PORT is duplicate among all services", type=str)
        parser.add_argument('-D', '--device', action='store_true', help="Show devices for the given service or all services")
        parser.add_argument('-vol', '--volumes', action='store_true', help="Show devices for the given service or all services")
        parser.add_argument('-P', '--list-port', action='store_true', help="List all ports in the YAML file")
        parser.add_argument('-L', '--list-service-name', action='store_true', help="List all service names in the YAML file")
        # parser.add_argument('-r', '--dockerfile', metavar='SERVICE', help="Read and display the Dockerfile for the given service")
        parser.add_argument('-r', '--dockerfile', action = 'store_true', help="Read and display the Dockerfile for the given service")
        parser.add_argument('-e', '--edit-dockerfile', action='store_true', help="Edit the Dockerfile for the given service using nvim, nano, or vim")
        parser.add_argument('-E', '--edit-service', action='store_true', help="Edit the service section for the given service")
        parser.add_argument('-dd', '--duplicate-service', metavar='NEW_SERVICE_NAME', help="Duplicate the service section with a new service name")
        parser.add_argument('-cs', '--copy-service', help = "copy service section to clipboar", action = 'store_true')
        parser.add_argument('-en', '--entrypoint', action='store_true', help="Read and display the entrypoint script for the given service")
        parser.add_argument('-ed', '--edit-entrypoint', action='store_true', help="Edit the entrypoint script for the given service")
        
        args = parser.parse_args()

        if not os.path.isfile(args.file):
            console.print(f"[white on red]YAML file not found:[/] {args.file}")
            sys.exit(1)

        try:
            content = DDF.open_file(args.file)
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")
            sys.exit(1)

        if args.device:
            DDF.list_service_devices(content, args.service)
        if args.volumes:
            DDF.list_service_volumes(content, args.service)
        elif args.list_port:
            if args.service:
                DDF.list_service_ports(content, args.service)
            else:
                console.print("[white on red]No service specified for listing ports.[/]")
                sys.exit(1)
        elif args.port:
            DDF.check_duplicate_port(content, args.port)
        elif args.find or (args.service and args.service.isdigit()):
            DDF.find_port(content, args.find or args.service)
        elif args.service and args.detail:
            DDF.show_service_detail(content, args.service)
        elif args.service and args.list:
            DDF.list_service_ports(content, args.service)
        elif args.service and args.dockerfile:
            DDF.read_dockerfile(service_name=args.service)
        elif args.service and args.entrypoint:
            DDF.read_entrypoint(service_name=args.service)
        elif args.service and args.edit_entrypoint:
            DDF.edit_entrypoint(service_name=args.service)
        elif args.service and args.edit_dockerfile:
            DDF.edit_dockerfile(service_name=args.service)
        elif args.list_service_name:
            DDF.list_service_names(content)
        elif args.service and args.edit_service:
            DDF.edit_service(file_path=args.file, service_name=args.service)
        elif args.service and args.copy_service:
            if not args.service:
                console.print("[white on red]No service name provided for copying.[/]")
                sys.exit(1)
            DDF.copy_service(args.service)
        elif args.duplicate_service:
            if not args.service:
                console.print("[white on red]No service name provided for duplication.[/]")
                sys.exit(1)
            DDF.duplicate_server(args.service, args.duplicate_service)
        else:
            DDF.find_duplicate_port(content, target_service=args.service)

if __name__ == '__main__':
    DDF.usage()