#!/usr/bin/env python
import yaml
import os
import sys
import argparse
from rich import print_json, console
console = console.Console()

class DDF:
    
    @classmethod
    def open_file(cls, file_path):
        """
        Open a file and return its content.
        """
        content = None
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        if not file_path.endswith('.yml') and not file_path.endswith('.yaml'):
            raise ValueError(f"The file {file_path} is not a YAML file.")
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"The file {file_path} is not readable.")
        # Check if the file is empty
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"The file {file_path} is empty.")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            content = yaml.load(content, Loader=yaml.FullLoader)
            if not content:
                raise ValueError(f"The file {file_path} is empty or contains invalid YAML.")
        return content
    
    @classmethod
    def find_duplicate_keys(cls, yaml_file = None, content = None, path=""):
        """
        Find duplicate keys in a YAML file, including nested structures.
        """
        if content is None and yaml_file: content = cls.open_file(yaml_file)
        if content is None:
            raise ValueError("No content provided to find duplicates.")
        if not isinstance(content, dict):
            raise ValueError("Invalid content: Expected a dictionary.")
        
        duplicates = []
        seen_host_ports = {}
        
        for key, value in content.get('services').items():
            # print("key:", key)
            for key1, value1 in value.items():
                if key1 == 'ports':
                    # Handle docker-compose port mappings
                    if all(isinstance(x, str) and ':' in x for x in value1):
                        # Extract both host and container ports
                        value2 = [
                            (
                                str(x.split(':')[0]) + "/tcp" if not "/" in x.split(':')[0] and not "/udp" in x.split(':')[1] else str(x.split(':')[0]) + "/udp" if "/udp" in x.split(':')[1] else str(x.split(':')[0]) + "/tcp", 
                                str(x.split(':')[1]) + "/tcp" if not "/" in x.split(':')[1] else str(x.split(':')[1])
                            ) for x in value1]
                        # print("value2:", value2)
                        
                        # Create a dictionary to store seen host ports
                        
                        for host_port, container_port in value2:
                            if host_port in seen_host_ports:
                                duplicates.append((f"{key}/ports/{host_port}", f"{seen_host_ports[host_port]}/ports/{host_port}", host_port))
                            else:
                                seen_host_ports[host_port] = key
        # print("duplicates:", duplicates)
        for d in duplicates:
            s1, _, port1, protocol1 = d[0].split("/")
            s2, _, port2, protocol2 = d[1].split("/")
            console.print(
                f"[bold #00FFFF]{s1}[/]/"
                f"[white on #0000FF]{port1}[/]/"
                f"[black on #55FF00]{protocol1}[/] "
                f"[bold #FFAA00]-->[/] "
                f"[bold #00FFFF]{s2}[/]/"
                f"[white on #550000]{port2}[/]/"
                f"[black on #55FF00]{protocol2}[/] "
            )
        # def process_value(value):
        #     if isinstance(value, dict):
        #         return {k: process_value(v) for k, v in value.items()}
        #     elif isinstance(value, list):
        #         print("VALUE:", value)
        #         if all(isinstance(x, str) and ':' in x for x in value):
        #             # Handle docker-compose port mappings
        #             return [(x.split(':')[0], x.split(':')[1]) for x in value]  # Extract both host and container ports
        #         return [process_value(item) for item in value]
        #     return value
        
        # for key, value in content.items():
        #     current_path = f"{path}/{key}" if path else key
        #     processed_value = process_value(value)
        #     print("PROCESSED_VALUE:", processed_value)
            
        #     value_str = str(processed_value)
            
        #     if value_str in seen_values:
        #         duplicates.append((current_path, seen_values[value_str], processed_value))
        #     else:
        #         seen_values[value_str] = current_path
                
        #     if isinstance(value, dict):
        #         nested_duplicates = cls.find_duplicate_keys(content=value, path=current_path)
        #         if nested_duplicates:
        #             duplicates.extend(nested_duplicates)

        # if duplicates:
        #     console.print("Found duplicate values:")
        #     for key1, key2, value in duplicates:
        #         console.print(f"Value '{value}' found in paths '{key1}' and '{key2}'")
        # return duplicates if duplicates else None
        
if __name__ == '__main__':
    content = DDF.open_file(sys.argv[1] if len(sys.argv) > 1 else r"c:\PROJECTS\docker-compose.yml" if os.path.isfile(r"c:\PROJECTS\docker-compose.yml") else console.print(f"[white on red blink]Invalid YAML File ![/]"))
    # console.print_json(data=content, indent=2)
    DDF.find_duplicate_keys(content=content)