# Docker Duplicate Finder (DDF)

A Python tool to detect duplicate ports and list service ports in Docker Compose YAML files.

## Features

- Detect duplicate port mappings across Docker services
- List all ports used by a specific service
- Support for TCP/UDP protocol detection
- Rich console output with colored formatting

## Requirements

- Python 3.x
- PyYAML
- rich

## Installation

```bash
pip install pyyaml rich
```

## Usage

```bash
python ddf.py [-h] [-f FILE] [-l] [service]
```

### Arguments

- `service`: Service name to inspect (optional)
- `-f FILE, --file FILE`: Path to YAML file (default: c:\PROJECTS\docker-compose.yml)
- `-l, --list`: List ports for the given service
- `-h, --help`: Show help message

### Examples

List ports for a specific service:
```bash
python ddf.py myservice -l
```

Find duplicate ports for all services:
```bash
python ddf.py
```

Check duplicate ports for specific service:
```bash
python ddf.py myservice
```

Use custom docker-compose file:
```bash
python ddf.py -f path/to/docker-compose.yml
```

## Output Format

The tool provides colorized output:
- Service names in cyan
- Port numbers on blue/red background
- Protocols on green background
- Warnings in yellow
- Errors in red

## Error Handling

The tool validates:
- File existence
- YAML file extension
- File permissions
- File content
- YAML syntax

## License

MIT License

## author
[Hadi Cahyadi](mailto:cumulus13@gmail.com)
    

## Coffee
[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cumulus13)

[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)
 [Support me on Patreon](https://www.patreon.com/cumulus13)