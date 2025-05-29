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
            devices = value.get('devices', [])
            if devices:
                found = True
                console.print(f"[bold cyan]{svc}:[/]")
                console.print("  devices:")
                for dev in devices:
                    console.print(f"    - {dev}")
        if not found:
            if service:
                console.print(f"[yellow]No devices found for service pattern:[/] {service}")
            else:
                console.print(f"[yellow]No devices found in any service.[/]")
    
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
        
        editors = ['nvim', 'nano', 'vim']
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
        parser.add_argument('-L', '--list-service-name', action='store_true', help="List all service names in the YAML file")
        # parser.add_argument('-r', '--dockerfile', metavar='SERVICE', help="Read and display the Dockerfile for the given service")
        parser.add_argument('-r', '--dockerfile', action = 'store_true', help="Read and display the Dockerfile for the given service")
        parser.add_argument('-e', '--edit-dockerfile', action='store_true', help="Edit the Dockerfile for the given service using nvim, nano, or vim")
        
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
        elif args.service and args.edit_dockerfile:
            DDF.edit_dockerfile(service_name=args.service)
        elif args.list_service_name:
            DDF.list_service_names(content)
        else:
            DDF.find_duplicate_port(content, target_service=args.service)

if __name__ == '__main__':
    DDF.usage()