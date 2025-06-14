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
from typing import ClassVar
from rich.table import Table
from rich import box
from typing import List
import fnmatch
import subprocess
from pathlib import Path
import shutil
import clipboard
import tempfile
import shlex
import re
# import importlib
import importlib.util

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
            raise FileNotFoundError(f"❌ The file {file_path} does not exist.")
        # if not file_path.endswith(('.yml', '.yaml')):
        #     raise ValueError(f"❌ The file {file_path} is not a YAML file.")
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"❌ The file {file_path} is not readable.")
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"❌ The file {file_path} is empty.")

        # Create the hash from the contents of the file
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Check Cache
        if file_hash in cls._file_cache:
            return cls._file_cache[file_hash]

        # Parse yaml if not in the cache
        try:
            content = yaml.load(file_bytes.decode('utf-8'), Loader=yaml.FullLoader)
        except Exception as e:
            raise ValueError(f"❌ The file {file_path} is not a valid YAML file: {e}")

        if not content or not isinstance(content, dict):
            raise ValueError(f"❌ The file {file_path} is empty or not a valid YAML mapping.")

        cls._file_cache[file_hash] = content
        return content
    
    @classmethod
    def find_service(cls, content, service):
        """
        Find a service in the YAML content.
        Supports pattern matching and substring search.
        """
        services = content.get('services', {})
        # Support the pattern/wildcard and substring
        matched = [
            svc for svc in services
            if fnmatch.fnmatch(svc, service) or service in svc
        ]
        if not matched:
            console.print(f"\n❌ [yellow]Service pattern '{service}' not found.[/]")
            return None
        return matched[0] if len(matched) == 1 else matched
    
    @classmethod
    def show_service_detail(cls, content, service, line_numbers=True):
        """
        Show the full configuration for a given service.
        """
        services = content.get('services', {})
        matched = cls.find_service(content, service)
        if not matched:
            return
        
        if isinstance(matched, str):
            service_val = services.get(matched)
            if not service_val:
                console.print(f"\n❌ [yellow]Service '{matched}' not found.[/]")
                return
            console.print(f"\n🔧 [bold cyan]Configuration for service '{matched}':[/]\n")
            yaml_str = yaml.dump({matched: service_val}, sort_keys=False, allow_unicode=True)
            syntax = Syntax(yaml_str, "yaml", theme="fruity", line_numbers=True if line_numbers else False)
            console.print(syntax)
        else:
            for svc in matched:
                service_val = services.get(svc)
                if not service_val:
                    console.print(f"\n❌ [yellow]Service '{svc}' not found.[/]")
                    continue
                console.print(f"\n🔧 [bold cyan]Configuration for service '{svc}':[/]\n")
                yaml_str = yaml.dump({svc: service_val}, sort_keys=False, allow_unicode=True)
                syntax = Syntax(yaml_str, "yaml", theme="fruity", line_numbers=True)
                console.print(syntax)
            
    @classmethod
    def list_service_ports(cls, content, service):
        services = content.get('services', {})
        # debug(services = services)
        service_val = services.get(service)
        if not isinstance(service_val, dict):
            console.print(f"\n❌ [yellow]Service '{service}' is not a dictionary or has no ports defined.[/]")
            return
        ports = service_val.get('ports', [])
        if not ports:
            console.print(f"\n❌ [yellow]No ports found for service:[/] {service}")
            return
        console.print(f"\n🚩 [bold cyan]Ports for service '{service}':[/]\n")
        for port in ports:
            console.print(f"• [green]{port}[/]")

    @classmethod
    def find_duplicate_port(cls, content, target_service=None):
        if content is None or not isinstance(content, dict):
            raise ValueError("❌ Invalid YAML content.")

        console.print("🔍 [bold #FFFF00]Scanning for duplicate ports...\n[/]")
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
                "❌ "
                f"[bold #00FFFF]{s1}[/]/"
                f"[white on #0000FF]{port1}[/]/"
                f"[black on #55FF00]{protocol1}[/] "
                f"[bold #FFAA00]-->[/] "
                f"[bold #00FFFF]{s2}[/]/"
                f"[white on #550000]{port2}[/]/"
                f"[black on #55FF00]{protocol2}[/] "
            )
            
    @classmethod
    def find_port(cls, content, port, compact=True):
        services = content.get('services', {})
        found_any = False
        output_lines = []
        compact_lines = []

        for service, value in services.items():
            if not isinstance(value, dict):
                continue
            ports = value.get('ports', [])
            if not ports:
                continue
            matched_ports = []
            for p in ports:
                p1, p2 = p.split(":")
                if p1.strip() == port or p2.strip() == port:
                    matched_ports.append(f"[white on #550000]{p1}[/]:[white on #550000]{p2}[/]")
                    # matched_ports.append(f"{p1}:{p2}")
            if matched_ports:
                found_any = True
                # Format default (lama): tampilkan semua port
                output_lines.append(f"- [bold #FFFF00]{service}[/]:")
                output_lines.append("  ports:")
                for p in ports:
                    p1, p2 = p.split(":")
                    p2 = p2.replace("/udp", f"[bold #FF00FF]/udp[/]").replace("/tcp", f"[bold #FF00FF]/tcp[/]")
                    if p1.strip() == port or p2.strip() == port:
                        output_lines.append(f"    - [white on #550000]{p1}[/]:[white on #550000]{p2}[/]")
                    else:
                        # output_lines.append(f"    - {p}")
                        output_lines.append(f"    - [#00FFFF]{p1}[/]:[#00FFFF]{p2}[/]")
                # Format compact: hanya port yang cocok
                img = value.get('image', '')
                ports_str = ', '.join([f'"{x}"' for x in matched_ports])
                compact_lines.append(f"- [bold #FFFF00]{service}[/]: ports: [{ports_str}]{f' image: [#00FFFF]{img}' if img else ''}[/]")

        if found_any:
            console.print("\n✅ [bold #00FFFF]Found service using port[/] [bold #FFAA00]{}[/]:\n".format(port))
            if compact:
                for line in compact_lines:
                    console.print(line)
            else:
                for line in output_lines:
                    console.print(line)
        else:
            console.print(f"👍 [black in #FFFF00]No service found with port {port}[/]")        
            
    @classmethod
    def check_duplicate_port(cls, content, port):
        """
        Check whether a particular port is duplicate among all services.
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
            console.print(f"❌ [#FF00FF]Port[/] [bold #FFFF00]{port}[/] [#FF00FF]is DUPLICATE in these services:[/]")
            for svc, p in found:
                console.print(f"  - [bold cyan]{svc}[/]: [yellow]{p}[/]")
        elif len(found) == 1:
            svc, p = found[0]
            console.print(f"🚩 [bold #00FFFF]Port {port} only found in service:[/] [bold #FFAA00]{svc}[/] ([yellow]{p}[/])")
        else:
            console.print(f"⚠️ [bold #FF007F]Port[/] [#FFFF00]{port}[/] [bold #FF007F]not found in any service.[/]")
        
        return found
            
    @classmethod
    def list_service_devices(cls, content, service=None):
        services = content.get('services', {})
        found = False
        for svc, value in services.items():
            # Support the pattern/wildcard and substring
            if service and not (fnmatch.fnmatch(svc, service) or service in svc):
                continue
            if not isinstance(value, dict):
                continue
            # debug(value = value)
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
                console.print(f"⚠️ [yellow]No devices found for service pattern:[/] {service}")
            else:
                console.print(f"❌ [yellow]No devices found in any service.[/]")
                
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
                console.print(f"\n🔧 [bold cyan]Volumes for service[/] [#FFFF00]'{svc}'[/]:\n")
                found = True
                console.print(f"[white on #5500FF italic underline]{svc}[/]:")
                console.print("  volumes:")
                for vol in volumes:
                    vo = vol.split(':')
                    console.print(f"    - [bold #00AAFF]{vo[0]}[/]: [bold #FFAA00]{vo[1]}[/]" if len(vo) > 1 else f"    - [bold #00AAFF]{vol}[/]")
        if not found:
            if service:
                console.print(f"⚠️ [yellow]No volumes found for service pattern:[/] {service}")
            else:
                console.print(f"❌ [yellow]No volumes found in any service.[/]")
                
    @classmethod
    def list_hostnames(cls, content, service=None):
        """
        List the hostname(s) for a given service, or all hostnames if no service is specified.
        """
        services = content.get('services', {})
        found = False
        lines = []
        for svc, value in services.items():
            if service and not (fnmatch.fnmatch(svc, service) or service in svc):
                continue
            if not isinstance(value, dict):
                continue
            hostname = value.get('hostname')
            if hostname:
                found = True
                # lines.append(f"[bold cyan]{svc}:[/]  hostname: [bold #00AAFF]{hostname}[/]")
                lines.append([f"[bold #FFFF00]{svc}[/]", f"[bold #00AAFF]{hostname}[/]"])
        if not found:
            if service:
                console.print(f"⚠️ [yellow]No hostname found for service pattern:[/] [white on blue]{service}[/]")
            else:
                console.print(f"❌ [yellow]No hostnames found in any service.[/]")
        else:
            console.print("\n✅ [bold #00FFFF]Hostnames found:[/]\n")
            table = Table(show_header=False, show_edge=False, box=None, show_lines=False, pad_edge=False)
            # table = Table(box=box.SQUARE, show_lines = True)
            table.add_column("service", justify = "left")
            table.add_column("", justify = "left")
            table.add_column('hostname', justify = "left")
            for line in lines:
                table.add_row(line[0], "[#FF55FF]hostname:[/]", line[1])
            console.print(table)
        
    @classmethod
    def list_service_ports(cls, content, service):
        """
        List all ports for a given service.
        """
        services = content.get('services', {})
        service_val = services.get(service)
        if not service_val:
            console.print(f"\n❌ [yellow]Service '{service}' not found.[/]")
            return
        ports = service_val.get('ports', [])
        if not ports:
            console.print(f"[yellow]No ports found for service:[/] {service}")
            return
        console.print(f"\n📌 [bold cyan]Ports for service '{service}':[/]\n")
        for port in ports:
            console.print(f"  - [green]{port}[/]")
    
    @classmethod
    def list_service_names(cls, content, filter: list = []):
        """
            filter support regex, wildchar, or substring matching.
        """
        services = content.get('services', {})
        if not services:
            console.print("\n❌ [yellow]No services found in the YAML file.[/]")
            return
        service_names = list(services.keys())
        if filter:
            filtered = set()
            for f in filter:
                # Try regex
                try:
                    regex = re.compile(f)
                    filtered.update([svc for svc in service_names if regex.search(svc)])
                    continue
                except re.error:
                    pass
                # Wildcard (fnmatch)
                import fnmatch
                filtered.update([svc for svc in service_names if fnmatch.fnmatch(svc, f)])
                # Substring
                filtered.update([svc for svc in service_names if f in svc])
            service_names = sorted(filtered)
        if service_names:
            console.print("\n🍁 [bold #FFFF00]Available service names:[/]\n")
            for service in service_names:
                console.print(f"  - [bold #00FFFF]{service}[/]")
        else:
            console.print("\n❌ [yellow]No matching services found.[/]")
            
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
            console.print(f"\n❌ [yellow]Service '{service_name}' not found.[/]")
            return None
        dockerfile = service_val.get('build', {}).get('dockerfile')
        build_path = service_val.get('build', {}).get('context', '.')
        debug(build_path = build_path)
        if not dockerfile:
            console.print(f"\n❌ [yellow]No Dockerfile specified for service '{service_name}'.[/]")
            return None
        return str(Path(root_path) / build_path / dockerfile)
    
    @classmethod
    def read_dockerfile(cls, path = None, service_name = None, line_numbers = True):
        """
        Read the Dockerfile content from the given path with color syntax by rich.Syntax.
        """
        path = cls.get_dockerfile(service_name) if service_name else path
        # print(f"path: {path}")
        if not path:
            console.print("\n❌ [white on red]No Dockerfile path provided or found.[/]")
            return None
        content = None
        if not os.path.isfile(path):
            console.print(f"\n❌ [white on red]Dockerfile not found:[/] {path}")
            return None
        try:
            with open(path, 'r') as f:
                content = f.read()
            if not content:
                console.print(f"\n🔵 [yellow]Dockerfile is empty:[/] {path}")
                return None
            syntax = Syntax(content, "dockerfile", theme="fruity", line_numbers=True if line_numbers else False)
            console.print(f"\n[bold cyan]Dockerfile for service[/] '[#FFFF00]{service_name}[/]':\n" if service_name else "[bold cyan]Dockerfile content:[/]\n")
            console.print(syntax)
        except Exception as e:
            console.print(f"\n❌ [red]Error reading Dockerfile:[/] {e}")
            return None
    
    @classmethod
    def read_entrypoint(cls, service_name, read = True, line_numbers = True):
        """
        Read the entrypoint script for a given service.
        Tries to resolve the entrypoint path by analyzing COPY instructions in the Dockerfile.
        """
        dockerfile_path = cls.get_dockerfile(service_name)
        if not dockerfile_path:
            console.print(f"\n❌ [white on red]No Dockerfile found for service '{service_name}'.[/]")
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
            console.print(f"\n❌ [red]Error reading Dockerfile:[/] {e}")
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
            console.print(f"\n❌ [yellow]No ENTRYPOINT found in Dockerfile for service '{service_name}'.[/]")
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
            # debug(entrypoint_src_file = entrypoint_src_file)
            entrypoint_path = os.path.join(base_dir, build_ctx, entrypoint_src_file)
            # debug(entrypoint_path = entrypoint_path)
        elif entrypoint_src:
            entrypoint_path = os.path.join(base_dir, build_ctx, entrypoint_src)
            # debug(entrypoint_path = entrypoint_path)
        else:
            # fallback: try to resolve entrypoint as relative to Dockerfile
            # debug(dockerfile_path = dockerfile_path)
            entrypoint_path = os.path.join(os.path.dirname(dockerfile_path), os.path.basename(entrypoint))
            # debug(entrypoint_path = entrypoint_path)

        # debug(entrypoint = entrypoint, entrypoint_src = entrypoint_src, entrypoint_path = entrypoint_path)
        # debug(entrypoint_path_is_file = os.path.isfile(entrypoint_path))
        # Try absolute path if entrypoint is absolute and not found yet
        if entrypoint_path and not os.path.isfile(entrypoint_path):
            if os.path.isabs(entrypoint):
                alt_path = os.path.join(base_dir, build_ctx, entrypoint.lstrip('/\\'))
                # debug(alt_path = alt_path)
                if os.path.isfile(alt_path):
                    entrypoint_path = alt_path

        # print(f"entrypoint: {entrypoint}")
        # print(f"entrypoint_path: {entrypoint_path}")
        # print(f"os.path.isfile(entrypoint_path): {os.path.isfile(entrypoint_path)}")
        if not entrypoint_path or not os.path.isfile(entrypoint_path):
            console.print(f"\n❌ [white on red]Entrypoint script not found:[/] {entrypoint_path or entrypoint}")
            return None

        if read:
            try:
                with open(entrypoint_path, 'r') as f:
                    script_content = f.read()
                syntax = Syntax(script_content, "bash", theme="fruity", line_numbers=True if line_numbers else False)
                console.print(f"\n✅ [bold cyan]Entrypoint script for service[/] '[black on #FFFF00]{service_name}[/]':\n")
                console.print(syntax)
            except Exception as e:
                console.print(f"\n❌ [red]Error reading entrypoint script:[/] {e}")
        return entrypoint_path
    
    @classmethod
    def edit_entrypoint(cls, service_name):
        """
        Edit the entrypoint script for a given service using nvim, nano, or vim.
        """
        entrypoint_path = cls.read_entrypoint(service_name, read=False)
        if not entrypoint_path:
            console.print(f"\n❌ [white on red]No entrypoint script found for service '{service_name}'.[/]")
            return None
        
        editors = CONFIG.get_config_as_list('editor', 'names') or [r'c:\msys64\usr\bin\nano.exe', 'nvim', 'vim']
        for editor in editors:
            if shutil.which(editor):
                try:
                    subprocess.run([editor, entrypoint_path], check=True)
                    return
                except subprocess.CalledProcessError as e:
                    console.print(f"\n❌ [red]Error launching {editor}:[/] {e}")
                    continue
        console.print("\n❌ [white on red]No suitable editor found to edit the entrypoint script.[/]")
    
    @classmethod
    def edit_dockerfile(cls, path=None, service_name=None):
        """
        Edit the Dockerfile using nvim, nano, or vim. Uses subprocess.run() and checks if the editor is installed.
        If the Dockerfile does not exist, create a new one in the build context directory.
        Handles absolute and relative dockerfile paths correctly, and always uses the build context if specified.
        """
        dockerfile_path = None

        if service_name:
            compose_file = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
            try:
                content = cls.open_file(compose_file)
                services = content.get('services', {})
                service_val = services.get(service_name, {})
                build = service_val.get('build', {})
                build_ctx = build.get('context', '.')
                dockerfile_name = build.get('dockerfile', 'Dockerfile')
                root_path = CONFIG.get_config('docker-compose', 'root_path')
                if root_path and os.path.isdir(root_path):
                    base_dir = root_path
                else:
                    base_dir = os.path.dirname(os.path.abspath(compose_file))
                # --- FIXED PATH LOGIC ---
                # If build_ctx is absolute, use as is, else join with base_dir
                if os.path.isabs(build_ctx):
                    build_dir = build_ctx
                else:
                    build_dir = os.path.normpath(os.path.join(base_dir, build_ctx))
                # If dockerfile_name is absolute, use as is, else join with build_dir
                if os.path.isabs(dockerfile_name):
                    dockerfile_path = dockerfile_name
                else:
                    dockerfile_path = os.path.normpath(os.path.join(build_dir, dockerfile_name))
            except Exception as e:
                console.print(f"\n❌ [red]Error resolving Dockerfile path:[/] {e}")
                return None
        else:
            dockerfile_path = path

        if not dockerfile_path:
            console.print("\n❌ [white on red]No Dockerfile path provided or found.[/]")
            return None

        # If Dockerfile does not exist, create an empty one in the build context
        if not os.path.isfile(dockerfile_path):
            try:
                os.makedirs(os.path.dirname(dockerfile_path), exist_ok=True)
                with open(dockerfile_path, 'w') as f:
                    f.write("# New Dockerfile\n")
                console.print(f"\n[bold yellow]Created new Dockerfile at:[/] {dockerfile_path}")
            except Exception as e:
                console.print(f"\n❌ [red]Error creating Dockerfile:[/] {e}")
                return None

        # Select editor
        editors = CONFIG.get_config_as_list('editor', 'names') or [r'c:\msys64\usr\bin\nano.exe', 'nvim', 'vim']
        for editor in editors:
            if shutil.which(editor):
                try:
                    subprocess.run([editor, dockerfile_path], check=True)
                    return
                except subprocess.CalledProcessError as e:
                    console.print(f"\n❌ [red]Error launching {editor}:[/] {e}")
                    continue
        console.print("\n❌ [white on red]No suitable editor found to edit the Dockerfile.[/]")
        
    @classmethod
    def edit_service(cls, file_path=None, service_name=None):
        """
        Edit a service section in the YAML file using nvim, nano, or vim.
        Only the selected service section will be edited and replaced back.
        """
        is_changed = True
        file_path = file_path or CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        
        if not service_name:
            console.print("⚠️ [white on red]No service name provided for editing.[/]")
            return

        if not os.path.isfile(file_path):
            console.print(f"⚠️ [white on red]YAML file not found:[/] {file_path}")
            return

        # Load YAML
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
        except Exception as e:
            console.print(f"❌ [red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        # Cari service yang cocok (pattern/wildcard/substring)
        matched = [svc for svc in services if fnmatch.fnmatch(svc, service_name) or service_name in svc]
        if not matched:
            console.print(f"⚠️ [yellow]Service pattern '{service_name}' not found.[/]")
            return

        if len(matched) > 1:
            for index, svc in enumerate(matched, start=1):
                console.print(f"{index}. [bold cyan]{svc}[/]")
                
            q = console.input(f"⚠️ [bold yellow]Multiple services match '{service_name}': {', '.join(matched)}. Please specify which service to edit: [/]")
            try:
                index = int(q) - 1
                if index < 0 or index >= len(matched):
                    console.print("❌ [red]Invalid service selection.[/]")
                    return
                matched = [matched[index]]
            except ValueError:
                console.print("❌ [red]Invalid input. Please enter a number.[/]")
                return
            except Exception as e:
                console.print(f"❌ [red]Unexpected error:[/] {e}")
                return
            
        for svc in matched:
            console.print(f"📝 [bold #FFFF00]Opening[/] [bold #00FFFF]{svc}[/] [bold #FFFF00]service config in editor...\n[/]")
            svc_data = services[svc]
            # Save Section to Temporary Files
            with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.yml') as tf:
                temp_path = tf.name
                yaml.dump({svc: svc_data}, tf, sort_keys=False, allow_unicode=True)
            # --- Tambahkan hash sebelum edit
            with open(temp_path, 'rb') as f:
                before_hash = hashlib.sha256(f.read()).hexdigest()
            # Select Editor
            editors = CONFIG.get_config_as_list('editor', 'names') or [r'c:\msys64\usr\bin\nano.exe', 'nvim', 'vim']
            for editor in editors:
                if shutil.which(editor):
                    try:
                        subprocess.run([editor, temp_path], check=True)
                        break
                    except subprocess.CalledProcessError as e:
                        console.print(f"❌ [red]Error launching {editor}:[/] {e}")
                        continue
                    except Exception as e:
                        console.print(f"❌ [red]Unexpected error launching {editor}:[/] {e}")
                        continue
            else:
                console.print("⚠️ [white on red]No suitable editor found to edit the service section.[/]")
                os.unlink(temp_path)
                return
            # After editing, reread and replace the section
            try:
                with open(temp_path, 'rb') as tf:
                    after_bytes = tf.read()
                    after_hash = hashlib.sha256(after_bytes).hexdigest()
                    tf.seek(0)
                    edited = yaml.safe_load(after_bytes.decode())
                if before_hash == after_hash:
                    is_changed = False
                    console.print(f"ℹ️ [yellow]No changes made to service '{svc}'.[/]")
                    os.unlink(temp_path)
                    continue
                if not edited or svc not in edited:
                    console.print(f"❌ [red]No valid service section found after editing. Skipped update for[/] [bold #FFFF00]'{svc}'.[/]")
                    os.unlink(temp_path)
                    continue
                content['services'][svc] = edited[svc]
                os.unlink(temp_path)
            except Exception as e:
                console.print(f"❌ [red]Error reading edited service section:[/] {e}")
                os.unlink(temp_path)
                console.print(f"⚠️ [bold red]YAML not updated due to error above. Please fix indentation (use spaces, not tabs).[/bold red]")
                return  

        if is_changed:
            # Save back to the original file
            try:
                with open(file_path, 'w') as f:
                    yaml.dump(content, f, sort_keys=False, allow_unicode=True)
                console.print(f"✅ [bold green]Service section(s) updated successfully in {file_path}[/bold green]")
            except Exception as e:
                console.print(f"❌ [red]Error writing YAML file:[/] {e}")
    
    @classmethod
    def edit_file(cls, filename, service_name):
        """
        Edit a spesific file by line containt 'COPY' in the Dockerfile.
        check relative path before if is file or not then edit
        if not or any not then show warning
        if success after edit then show info too but,
        if edit and not changed then show info too
        """
        dockerfile_path = cls.get_dockerfile(service_name)
        if not dockerfile_path or not os.path.isfile(dockerfile_path):
            console.print(f"\n❌ [red]Dockerfile for service '{service_name}' not found.[/]")
            return

        # Cari baris COPY yang mengandung filename
        copy_line = None
        with open(dockerfile_path, 'r') as f:
            for line in f:
                if line.strip().startswith('COPY') and filename in line:
                    copy_line = line.strip()
                    break

        if not copy_line:
            console.print(f"\n❌ [yellow]No COPY line containing '{filename}' found in Dockerfile for '{service_name}'.[/]")
            return

        # Ambil path sumber dari COPY
        parts = copy_line.split()
        if len(parts) < 3:
            console.print(f"\n❌ [yellow]Malformed COPY line: {copy_line}[/]")
            return
        src_path = parts[1]
        # Hilangkan './' jika ada
        if src_path.startswith('./'):
            src_path = src_path[2:]
        # Resolve path relatif terhadap build context
        compose_file = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        base_dir = os.path.dirname(os.path.abspath(compose_file))
        content = cls.open_file(compose_file)
        services = content.get('services', {})
        service_val = services.get(service_name, {})
        build_ctx = service_val.get('build', {}).get('context', '.')
        file_path = os.path.normpath(os.path.join(base_dir, build_ctx, src_path))

        if not os.path.isfile(file_path):
            console.print(f"\n❌ [yellow]File to edit not found: {file_path}[/]")
            return

        # Hash sebelum edit
        with open(file_path, 'rb') as f:
            before_hash = hashlib.sha256(f.read()).hexdigest()

        # Pilih editor
        editors = CONFIG.get_config_as_list('editor', 'names') or [r'c:\msys64\usr\bin\nano.exe', 'nvim', 'vim']
        for editor in editors:
            if shutil.which(editor):
                try:
                    subprocess.run([editor, file_path], check=True)
                    break
                except subprocess.CalledProcessError as e:
                    console.print(f"❌ [red]Error launching {editor}:[/] {e}")
                    continue
        else:
            console.print("\n❌ [white on red]No suitable editor found to edit the file.[/]")
            return

        # Hash setelah edit
        with open(file_path, 'rb') as f:
            after_hash = hashlib.sha256(f.read()).hexdigest()

        if before_hash == after_hash:
            console.print(f"ℹ️ [yellow]No changes made to file '{file_path}'.[/]")
        else:
            console.print(f"✅ [green]File '{file_path}' edited successfully.[/]")
    
    @classmethod
    def set_dockerfile(cls, service_name, dockerfile_path):
        """
        Set the Dockerfile path for a given service in the docker-compose.yml.
        If the service does not exist, it will be created.
        """
        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not os.path.isfile(file_path):
            console.print(f"\n❌ [white on red]YAML file not found:[/] {file_path}")
            return
        
        # Load YAML
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
        except Exception as e:
            console.print(f"\n❌ [red]Error loading YAML:[/] {e}")
            return

        # Ensure content is a dict
        if not isinstance(content, dict):
            content = {}

        # Ensure 'services' is a dict
        if 'services' not in content or not isinstance(content['services'], dict):
            content['services'] = {}

        services = content['services']
        if service_name not in services or not isinstance(services[service_name], dict):
            services[service_name] = {}

        # Set Dockerfile path
        if 'build' not in services[service_name] or not isinstance(services[service_name]['build'], dict):
            services[service_name]['build'] = {}
        services[service_name]['build']['dockerfile'] = dockerfile_path

        # Save back to the original file
        try:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, sort_keys=False, allow_unicode=True)
            console.print(f"\n✅ [bold green]Dockerfile path set successfully for service '{service_name}' in {file_path}[/bold green]")
        except Exception as e:
            console.print(f"\n❌ [red]Error writing YAML file:[/] {e}")
    
    @classmethod
    def new_service(cls, service_name, service_config=None):
        """
        Create a new service section in the YAML file.
        If service exists, it will not be overwritten.
        If service_config is provided, it will be used as the initial configuration.
        After creation, open the new service in the editor for user to fill in.
        """
        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not os.path.isfile(file_path):
            console.print(f"\n❌ [white on red]YAML file not found:[/] {file_path}")
            return

        try:
            content = cls.open_file(file_path)
        except Exception as e:
            console.print(f"\n❌ [red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        if service_name in services:
            console.print(f"\n ⚠️ [yellow]Service '{service_name}' already exists.[/]")
            return

        # Add the new service
        if not service_config:
            service_config = {}
        services[service_name] = service_config
        content['services'] = services

        # Save back to the file
        try:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, sort_keys=False, allow_unicode=True)
            console.print(f"\n✅ [bold green]New service '{service_name}' created successfully in {file_path}[/bold green]")
        except Exception as e:
            console.print(f"\n❌ [red]Error writing YAML file:[/] {e}")
            return

        # Open the new service in the editor for user to fill in
        cls.edit_service(file_path=file_path, service_name=service_name)
        
    @classmethod
    def copy_service(cls, service_name):
        """
        Copy a service section to the clipboard.
        The service section will be formatted as YAML and copied.
        """

        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not os.path.isfile(file_path):
            console.print(f"\n❌ [white on red]YAML file not found:[/] {file_path}")
            return

        try:
            content = cls.open_file(file_path)
        except Exception as e:
            console.print(f"\n❌ [red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        if service_name not in services:
            console.print(f"\n❌ [yellow]Service '{service_name}' not found.[/]")
            return

        # Get the service section
        service_section = {service_name: services[service_name]}
        yaml_str = yaml.dump(service_section, sort_keys=False, allow_unicode=True)

        # Copy to clipboard
        clipboard.copy(yaml_str)
        console.print(f"\n✅ [bold green]Service '{service_name}' copied to clipboard successfully.[/]")
    
    @classmethod
    def rename_service(cls, old_service_name, new_service_name):
        """
        Rename a service section in the YAML file.
        If the new service name already exists, it will not overwrite it.
        """
        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not os.path.isfile(file_path):
            console.print(f"\n❌ [white on red]YAML file not found:[/] {file_path}")
            return

        try:
            content = cls.open_file(file_path)
        except Exception as e:
            console.print(f"\n❌ [red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        if old_service_name not in services:
            console.print(f"\n❌ [yellow]Service '{old_service_name}' not found.[/]")
            return
        if new_service_name in services:
            console.print(f"\n❌ [yellow]Service '{new_service_name}' already exists. Cannot rename.[/]")
            return

        # Rename the service
        services[new_service_name] = services.pop(old_service_name)
        content['services'] = services

        # Save back to the file
        try:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, sort_keys=False, allow_unicode=True)
            console.print(f"\n✅ [bold green]Service '{old_service_name}' renamed to '{new_service_name}' successfully in {file_path}[/bold green]")
        except Exception as e:
            console.print(f"\n❌ [red]Error writing YAML file:[/] {e}")
    
    @classmethod
    def copy_dockerfile(cls, service_name):
        """
        Copy the Dockerfile content to the clipboard for a given service.
        If the Dockerfile does not exist, it will not copy anything.
        """
        dockerfile_path = cls.get_dockerfile(service_name)
        if not dockerfile_path:
            console.print(f"\n❌ [white on red]No Dockerfile found for service '{service_name}'.[/]")
            return

        if not os.path.isfile(dockerfile_path):
            console.print(f"\n❌ [white on red]Dockerfile not found:[/] {dockerfile_path}")
            return

        try:
            with open(dockerfile_path, 'r') as f:
                content = f.read()
            clipboard.copy(content)
            console.print(f"\n✅ [#FFFF00]Dockerfile content for service[/] [#00FFFF]'{service_name}'[/] [#FFFF00]copied to clipboard successfully.[/]")
        except Exception as e:
            console.print(f"\n❌ [red]Error reading Dockerfile:[/] [white on red]{e}[/]")
    
    @classmethod
    def duplicate_server(cls, service_name, new_service_name):
        """
        Duplicate a service section in the YAML file.
        The new service will have the same configuration as the original service.
        """
        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not os.path.isfile(file_path):
            console.print(f"\n❌ [white on red]YAML file not found:[/] {file_path}")
            return

        try:
            content = cls.open_file(file_path)
        except Exception as e:
            console.print(f"\n❌ [red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        if service_name not in services:
            console.print(f"\n❌ [yellow]Service '{service_name}' not found.[/]")
            return

        # Duplicate the service
        services[new_service_name] = services[service_name]
        content['services'] = services

        # Save back to the file
        try:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, sort_keys=False, allow_unicode=True)
            console.print(f"\n✅ [bold green]Service '{service_name}' duplicated to '{new_service_name}' successfully in {file_path}[/bold green]")
        except Exception as e:
            console.print(f"\n❌ [red]Error writing YAML file:[/] {e}")
    
    @classmethod
    def remove_service(cls, service_name):
        """
        Remove a service section from the YAML file.
        """
        file_path = CONFIG.get_config('docker-compose', 'file') or r"c:\PROJECTS\docker-compose.yml"
        if not os.path.isfile(file_path):
            console.print(f"\n❌ [white on red]YAML file not found:[/] {file_path}")
            return

        try:
            content = cls.open_file(file_path)
        except Exception as e:
            console.print(f"\n❌ [red]Error loading YAML:[/] {e}")
            return

        services = content.get('services', {})
        if service_name not in services:
            console.print(f"\n❌ [yellow]Service '{service_name}' not found.[/]")
            return

        # Remove the service
        del services[service_name]
        content['services'] = services

        # Save back to the file
        try:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, sort_keys=False, allow_unicode=True)
            console.print(f"\n ⚠️ [bold green]Service '{service_name}' removed successfully from {file_path}[/bold green]")
        except Exception as e:
            console.print(f"\n ❌ [red]Error writing YAML file:[/] {e}")
    
    @classmethod
    def get_version(cls):
        """
        Get the version of the ddf module.
        Version is taken from the __version__.py file if it exists.
        The content of __version__.py should be:
        version = "0.33"
        """
        try:
            version_file = Path(__file__).parent / "__version__.py"
            if version_file.is_file():
                with open(version_file, "r") as f:
                    for line in f:
                        if line.strip().startswith("version"):
                            parts = line.split("=")
                            if len(parts) == 2:
                                return parts[1].strip().strip('"').strip("'")
        except Exception as e:
            debug(error=str(e))

        return "UNKNOWN VERSION"
        
    @classmethod
    def show_debug(cls):
        os.environ.update({'DEBUG':'1'})
        os.environ.update({'DEBUG_SERVER':'1'})
    
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
        parser.add_argument('-sd', '--set-dockerfile', metavar='DOCKERFILE_PATH', help="Set the Dockerfile path for the given service")
        parser.add_argument('-E', '--edit-service', action='store_true', help="Edit the service section for the given service")
        parser.add_argument('-dd', '--duplicate-service', metavar='NEW_SERVICE_NAME', help="Duplicate the service section with a new service name")
        parser.add_argument('-cs', '--copy-service', help = "copy service section to clipboar", action = 'store_true')
        parser.add_argument('-rn', '--rename-service', metavar='NEW_SERVICE_NAME', help="Rename the service section to a new name")
        parser.add_argument('-cd', '--copy-dockerfile', action='store_true', help="Copy the Dockerfile content to clipboard")
        parser.add_argument('-en', '--entrypoint', action='store_true', help="Read and display the entrypoint script for the given service")
        parser.add_argument('-ed', '--edit-entrypoint', action='store_true', help="Edit the entrypoint script for the given service")
        parser.add_argument('-rm', '--remove-service', action='store_true', help="Remove the service section for the given service")
        parser.add_argument('-a', '--all', action='store_true', help="Show all services and their ports, devices, and volumes")
        parser.add_argument('-nl', '--no-line-numbers', action='store_false', help="Disable line numbers in syntax highlighting")
        parser.add_argument('-hn', '--hostname', action='store_true', help="Show hostname for the service if available")
        parser.add_argument('-n', '--new', action='store_true', help="Create a new service section in the YAML file")
        parser.add_argument('-F', '--filter', action='store', help="Filter services by name or pattern", nargs='*', default=[])
        parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {cls.get_version()}', help="Show the version of ddf module")
        parser.add_argument('-ef', '--edit-file', metavar='FILENAME', help="Edit a specific file in the Dockerfile COPY command", type=str)
        
        
        if len(sys.argv) == 1:
            try:
                content = DDF.open_file(default_file)
                DDF.find_duplicate_port(content)
            except Exception as e:
                console.print(f"\n❌ [red]Error:[/] {e}")
                sys.exit(1)
            sys.exit(1)
            
        if '-h' in sys.argv or '--help' in sys.argv:
            parser.print_help()
            sys.exit(0)
            
        args = parser.parse_args()

        if not os.path.isfile(args.file):
            console.print(f"\n❌ [white on red]YAML file not found:[/] {args.file}")
            sys.exit(1)

        try:
            content = DDF.open_file(args.file)
        except Exception as e:
            console.print(f"\n❌ [red]Error:[/] {e}")
            sys.exit(1)

        if args.device:
            DDF.list_service_devices(content, args.service)
        if args.volumes:
            DDF.list_service_volumes(content, args.service)
        if args.list_port:
            if args.service:
                DDF.list_service_ports(content, args.service)
            else:
                console.print("\n❌ [white on red]No service specified for listing ports.[/]")
                sys.exit(1)
        if args.hostname:
            DDF.list_hostnames(content, args.service)
        if args.port:
            DDF.check_duplicate_port(content, args.port)
        if args.find or (args.service and args.service.isdigit()):
            DDF.find_port(content, args.find or args.service, compact=False if args.all else True)
        if args.service and args.detail:
            DDF.show_service_detail(content, args.service, args.no_line_numbers)
        if args.service and args.list:
            DDF.list_service_ports(content, args.service)
        if args.service and args.dockerfile:
            DDF.read_dockerfile(service_name=args.service, line_numbers=args.no_line_numbers)
        if args.service and args.entrypoint:
            DDF.read_entrypoint(service_name=args.service, line_numbers=args.no_line_numbers)
        if args.service and args.edit_entrypoint:
            DDF.edit_entrypoint(service_name=args.service)
        if args.service and args.remove_service:
            DDF.remove_service(args.service)
        if args.service and args.edit_dockerfile:
            DDF.edit_dockerfile(service_name=args.service)
        if args.service and args.set_dockerfile:
            if not args.set_dockerfile:
                console.print("\n❌ [white on red]No Dockerfile path provided for setting.[/]")
                sys.exit(1)
            DDF.set_dockerfile(args.service, args.set_dockerfile)
            if args.edit_dockerfile:
                DDF.edit_dockerfile(service_name=args.service)
            elif args.edit_service:
                DDF.edit_service(file_path=args.file, service_name=args.service)
            elif args.read_dockerfile:
                DDF.read_dockerfile(service_name=args.service, line_numbers=args.no_line_numbers)
        if args.service and args.edit_file:
            if not args.edit_file:
                console.print("\n❌ [white on red]No filename provided for editing.[/]")
                sys.exit(1)
            DDF.edit_file(args.edit_file, args.service)
        if args.list_service_name:
            DDF.list_service_names(content, args.filter)
        if args.service and args.edit_service:
            DDF.edit_service(file_path=args.file, service_name=args.service)
        if args.new:
            if not args.service:
                console.print("\n❌ [white on red]No service name provided for new service.[/]")
                sys.exit(1)
            DDF.new_service(args.service)
        if args.service and args.copy_service:
            if not args.service:
                console.print("\n❌ [white on red]No service name provided for copying.[/]")
                sys.exit(1)
            DDF.copy_service(args.service)
        elif args.copy_dockerfile:
            if not args.service:
                console.print("\n❌ [white on red]No service name provided for copying Dockerfile.[/]")
                sys.exit(1)
            DDF.copy_dockerfile(args.service)
        elif args.rename_service:
            if not args.service:
                console.print("\n❌ [white on red]No service name provided for copying Dockerfile.[/]")
                sys.exit(1)
            DDF.rename_service(args.service, args.rename_service)
        if args.duplicate_service:
            if not args.service:
                console.print("\n❌ [white on red]No service name provided for duplication.[/]")
                sys.exit(1)
            DDF.duplicate_server(args.service, args.duplicate_service)
        #if only service is provided, check for duplicate ports
        debug(_option_string_actions = parser.__dict__.get('_option_string_actions').keys())
        debug(len_filter__option_string_actions = len(list(filter(lambda k: k in parser.__dict__.get('_option_string_actions').keys(), [i for i in sys.argv[1:]]))))
        # if args.service and not (args.list or args.detail or args.dockerfile or args.entrypoint or args.edit_dockerfile or args.edit_entrypoint or args.set_dockerfile or args.edit_service or args.remove_service or args.copy_service or args.copy_dockerfile or args.duplicate_service):
        if len(list(filter(lambda k: k in parser.__dict__.get('_option_string_actions').keys(), [i for i in sys.argv[1:]]))) == 0 and args.service:
            DDF.find_duplicate_port(content, target_service=args.service)

if __name__ == '__main__':
    DDF.usage()