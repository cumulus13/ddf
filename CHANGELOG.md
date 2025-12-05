# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release planning
- Core documentation structure
- API reference documentation

## [0.37.x] - 2025-01-04

### Added
- Core DDF functionality for Docker Compose file management
- Multiple cache backends support (Redis, Memcached, Pickle)
- Server mode with system tray integration
- Automatic backup management before edits
- Advanced editor support with change detection
- Detached terminal mode for editors
- Port conflict detection and management
- Service management (create, edit, duplicate, rename, remove)
- Dockerfile and entrypoint script editing
- Pattern matching for service names (wildcards, regex, substring)
- File monitoring for non-blocking editors
- Health check command for server status
- Configuration via INI file
- Environment variable support for sensitive configs
- Comprehensive documentation on ReadTheDocs

### Features

#### Cache System
- Pickle-based file cache (default, no dependencies)
- Redis integration with JSON/Pickle serialization
- Memcached integration with JSON/Pickle serialization
- Automatic cache invalidation on file changes
- Pattern-based cache invalidation
- Configurable TTL per backend

#### Server Mode
- Background server with socket communication
- System tray icon with menu (Windows, Linux, macOS)
- Desktop notifications for operation results
- Command auto-forwarding for editing operations
- Health check endpoint
- Systemd service support (Linux)
- LaunchAgent support (macOS)
- Windows Service support (NSSM, Task Scheduler)

#### Backup System
- Automatic backups before editing operations
- Timestamped backup files with context
- Interactive backup restoration
- Backup listing and management
- Custom backup directory support

#### Editor Support
- Multiple editor support (vim, nvim, nano, emacs, Sublime Text, VS Code, etc.)
- Blocking and non-blocking editor detection
- Sublime Text --wait flag support
- Detached terminal mode (opens editor in new window)
- File change monitoring for non-blocking editors
- Configurable editor priority

#### Port Management
- Duplicate port detection across services
- Port usage search
- Port conflict resolution helpers
- Protocol-aware port checking (TCP/UDP)

#### Service Operations
- List all services
- Show service details with syntax highlighting
- Edit service configuration
- Create new services
- Duplicate services
- Rename services
- Remove services (with backup)
- Copy service to clipboard

#### File Operations
- Read and edit Dockerfiles
- Read and edit entrypoint scripts
- Edit files referenced in COPY instructions
- Syntax highlighting for various file types
- Line number toggle

#### Pattern Matching
- Wildcard matching (e.g., `web*`)
- Substring matching
- Regex filtering
- Multiple pattern support

### Documentation
- Complete user guide
- Installation instructions
- Configuration reference
- Usage examples
- API reference
- Server mode guide
- Caching system guide
- Backup & recovery guide
- Contributing guidelines
- ReadTheDocs integration

### Dependencies
- Python >= 3.8
- PyYAML >= 6.0
- rich >= 13.0.0
- richcolorlog >= 0.1.0
- pydebugger >= 0.1.0
- configset >= 0.1.0
- rich-argparse >= 1.0.0
- clipboard >= 0.0.4

### Optional Dependencies
- redis >= 4.0.0 (for Redis cache)
- pymemcache >= 3.5.0 (for Memcached cache)
- pystray >= 0.19.0 (for tray icon)
- Pillow >= 9.0.0 (for tray icon)
- plyer >= 2.0.0 (for notifications)
- watchdog >= 2.1.0 (for file monitoring)

## [0.11.0] - 2024-12-04

### Added
- Initial project structure
- Basic Docker Compose parsing
- Simple service listing

---

## Version History

### Version 0.37.x (Current)
First stable release with comprehensive feature set including:
- Multi-backend caching
- Server mode operation
- Advanced editing capabilities
- Comprehensive documentation

### Version 0.32.0 (Alpha)
Initial development version with basic functionality

---

## Future Releases

### Planned for 1.0.0
- [ ] Docker Swarm support
- [ ] Kubernetes integration
- [ ] Web UI for server mode
- [ ] Plugin system
- [ ] Multi-file docker-compose support
- [ ] Diff view for changes
- [ ] Undo/redo functionality

### Planned for 2.0.0
- [ ] Cloud storage for backups
- [ ] Team collaboration features
- [ ] CI/CD integration
- [ ] Custom validators
- [ ] Auto-formatting

### Under Consideration
- GraphQL API
- REST API
- Docker context support
- Registry integration
- Container inspection
- Log viewing

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Authors

* **Hadi Cahyadi** - *Initial work* - [cumulus13](https://github.com/cumulus13)

## Acknowledgments

* Built with [Rich](https://github.com/Textualize/rich)
* Inspired by Docker Compose CLI
* Community contributors

