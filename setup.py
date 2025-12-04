#!/usr/bin/env python3
# File: setup.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-04
# Description: 
# License: MIT

"""
DDF - Enhanced Docker Compose Tools
====================================

A powerful tool for managing Docker Compose configurations with advanced features
like caching, server mode, backup management, and more.

Author: Hadi Cahyadi
Email: cumulus13@gmail.com
URL: https://github.com/cumulus13/ddf
License: MIT
"""

from setuptools import setup, find_packages
from pathlib import Path
import re
import shutil

shutil.copy2("__version__.py", "ddf/__version__.py")

# Read version from __version__.py
def get_version():
    version_file = Path(__file__).parent / "ddf" / "__version__.py"
    if not version_file.exists():
        version_file = Path(__file__).parent / "__version__.py"
    if version_file.exists():
        with open(version_file, "r") as f:
            content = f.read()
            match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if match:
                return match.group(1)
    return "0.1.0"

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
def read_requirements(filename):
    req_file = Path(__file__).parent / filename
    if req_file.exists():
        with open(req_file, "r") as f:
            return [
                line.strip()
                for line in f
                if line.strip()
                and not line.startswith("#")
                and not line.startswith("-r")
            ]
    return []

setup(
    name="ddf",
    version=get_version(),
    author="Hadi Cahyadi",
    author_email="cumulus13@gmail.com",
    description="Enhanced Docker Compose Tools with caching, server mode, and backup management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cumulus13/ddf",
    project_urls={
        "Bug Reports": "https://github.com/cumulus13/ddf/issues",
        "Source": "https://github.com/cumulus13/ddf",
        "Documentation": "https://ddf.readthedocs.io",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Systems Administration",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    keywords="docker docker-compose devops container management yaml",
    python_requires=">=3.8",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "cache": [
            "redis>=4.0.0",
            "pymemcache>=3.5.0",
        ],
        "server": [
            "pystray>=0.19.0",
            "Pillow>=9.0.0",
            "plyer>=2.0.0",
        ],
        "monitoring": [
            "watchdog>=2.1.0",
        ],
        "all": [
            "redis>=4.0.0",
            "pymemcache>=3.5.0",
            "pystray>=0.19.0",
            "Pillow>=9.0.0",
            "plyer>=2.0.0",
            "watchdog>=2.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ddf=ddf.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ddf": [
            "*.ini",
            "*.yaml",
            "*.yml",
        ],
    },
    zip_safe=False,
    license="MIT",
    license_files=["LICENSE"]
)