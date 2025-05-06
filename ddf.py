#!/usr/bin/env python
import yaml
import os
import sys
import argparse
from rich.console import Console

console = Console()

class DDF:

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
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = yaml.load(file.read(), Loader=yaml.FullLoader)
            if not content:
                raise ValueError(f"The file {file_path} is empty or contains invalid YAML.")
        return content

    @classmethod
    def list_service_ports(cls, content, service):
        services = content.get('services', {})
        ports = services.get(service, {}).get('ports', [])
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

if __name__ == '__main__':
    default_file = r"c:\PROJECTS\docker-compose.yml"

    parser = argparse.ArgumentParser(description="Detect or list ports in a Docker Compose file.")
    parser.add_argument('service', nargs='?', help="Service name to inspect")
    parser.add_argument('-f', '--file', default=default_file, help="Path to YAML file")
    parser.add_argument('-l', '--list', action='store_true', help="List ports for the given service")

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        console.print(f"[white on red]YAML file not found:[/] {args.file}")
        sys.exit(1)

    try:
        content = DDF.open_file(args.file)
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)

    if args.service and args.list:
        DDF.list_service_ports(content, args.service)
    else:
        DDF.find_duplicate_port(content, target_service=args.service)
