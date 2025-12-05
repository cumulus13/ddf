Contributing to DDF
===================

Thank you for your interest in contributing to DDF! This document provides
guidelines and instructions for contributing.

Ways to Contribute
------------------

* **Bug Reports**: Report bugs via GitHub Issues
* **Feature Requests**: Suggest new features via GitHub Issues
* **Documentation**: Improve or translate documentation
* **Code**: Submit bug fixes or new features via Pull Requests
* **Testing**: Test new features and report issues
* **Translations**: Add support for new languages

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~~

1. Fork the repository on GitHub
2. Clone your fork locally:

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/ddf.git
      cd ddf

3. Create a virtual environment:

   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # Linux/macOS
      venv\Scripts\activate     # Windows

4. Install development dependencies:

   .. code-block:: bash

      pip install -e ".[dev]"

5. Create a branch for your changes:

   .. code-block:: bash

      git checkout -b feature/my-new-feature

Development Workflow
~~~~~~~~~~~~~~~~~~~~

1. Make your changes
2. Run tests: ``pytest``
3. Run linters: ``flake8 ddf/``
4. Format code: ``black ddf/``
5. Update documentation if needed
6. Commit your changes
7. Push to your fork
8. Open a Pull Request

Code Standards
--------------

Code Style
~~~~~~~~~~

* Follow PEP 8 style guide
* Use ``black`` for code formatting (line length: 100)
* Use ``isort`` for import sorting
* Use type hints where appropriate
* Write docstrings for all public functions/classes

Example:

.. code-block:: python

   def example_function(arg1: str, arg2: int = 0) -> bool:
       """
       Short description of function.
       
       Longer description if needed.
       
       Args:
           arg1: Description of arg1
           arg2: Description of arg2 (default: 0)
       
       Returns:
           bool: Description of return value
       
       Raises:
           ValueError: When arg2 is negative
       """
       if arg2 < 0:
           raise ValueError("arg2 must be non-negative")
       
       # Implementation
       return True

Testing
~~~~~~~

* Write tests for new features
* Ensure existing tests pass
* Aim for >80% code coverage
* Use pytest for testing
* Use fixtures for common test data

Example test:

.. code-block:: python

   import pytest
   from ddf import DDF
   
   @pytest.fixture
   def sample_compose():
       return {
           'services': {
               'web': {
                   'image': 'nginx',
                   'ports': ['80:80']
               }
           }
       }
   
   def test_find_service(sample_compose):
       result = DDF.find_service(sample_compose, 'web')
       assert result == 'web'
   
   def test_find_service_not_found(sample_compose):
       result = DDF.find_service(sample_compose, 'nonexistent')
       assert result is None

Documentation
~~~~~~~~~~~~~

* Update documentation for new features
* Use reStructuredText (RST) format
* Include code examples
* Build docs locally to verify: ``cd docs && make html``

Commit Messages
~~~~~~~~~~~~~~~

Use clear, descriptive commit messages:

.. code-block:: text

   Short summary (50 chars or less)
   
   Detailed explanation if needed. Wrap at 72 characters.
   
   - Use bullet points if helpful
   - Reference issues: Fixes #123
   - Multiple paragraphs are fine

Examples:

.. code-block:: text

   Good:
   Add support for detached terminal mode
   
   Bad:
   updated stuff

Pull Request Process
--------------------

1. **Update Documentation**

   * Add docstrings to new functions/classes
   * Update user documentation if adding features
   * Add examples to relevant docs

2. **Add Tests**

   * Write tests for new functionality
   * Ensure tests pass locally
   * Update existing tests if needed

3. **Run Quality Checks**

   .. code-block:: bash

      # Format code
      black ddf/
      isort ddf/
      
      # Run linters
      flake8 ddf/
      mypy ddf/
      
      # Run tests
      pytest
      pytest --cov=ddf

4. **Update Changelog**

   Add entry to CHANGELOG.md under "Unreleased" section

5. **Create Pull Request**

   * Use descriptive title
   * Reference related issues
   * Describe your changes
   * Include screenshots if UI changes

6. **Code Review**

   * Address review comments
   * Keep discussions constructive
   * Update PR based on feedback

Pull Request Template
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: markdown

   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## How Has This Been Tested?
   Describe testing approach
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added to complex code
   - [ ] Documentation updated
   - [ ] Tests added/updated
   - [ ] All tests pass
   - [ ] No new warnings
   - [ ] CHANGELOG.md updated

Reporting Bugs
--------------

Bug Report Template
~~~~~~~~~~~~~~~~~~~

When reporting bugs, include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Exact steps to trigger the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:

   * OS: (e.g., Ubuntu 22.04)
   * Python version: (e.g., 3.11.5)
   * DDF version: (e.g., 0.1.0)
   * Installation method: (pip, source, etc.)

6. **Additional Context**: Screenshots, logs, etc.

Example:

.. code-block:: markdown

   **Bug Description**
   Cache invalidation fails when using Redis backend
   
   **Steps to Reproduce**
   1. Configure Redis backend in ddf.ini
   2. Edit service: `ddf myservice -E`
   3. Cache is not invalidated
   
   **Expected Behavior**
   Cache should be invalidated after editing
   
   **Actual Behavior**
   Old cached data is returned
   
   **Environment**
   - OS: Ubuntu 22.04
   - Python: 3.11.5
   - DDF: 0.1.0
   - Redis: 7.0.12
   
   **Logs**
   ```
   [ERROR] Cache invalidation failed: Connection refused
   ```

Feature Requests
----------------

Feature Request Template
~~~~~~~~~~~~~~~~~~~~~~~~

When requesting features, include:

1. **Problem**: What problem does this solve?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other approaches considered
4. **Additional Context**: Examples, mockups, etc.

Example:

.. code-block:: markdown

   **Problem**
   No way to batch edit multiple services at once
   
   **Proposed Solution**
   Add `-M/--multiple` flag to edit multiple services:
   ```bash
   ddf web api worker -E -M
   ```
   
   **Alternatives**
   1. Use wildcards: `ddf "web*" -E`
   2. Use filter: `ddf -F "web" "api" -E`
   
   **Additional Context**
   Would save time when making similar changes to many services

Development Guidelines
----------------------

Architecture
~~~~~~~~~~~~

* Keep classes focused (Single Responsibility)
* Use dependency injection where appropriate
* Avoid circular dependencies
* Follow existing patterns

Error Handling
~~~~~~~~~~~~~~

* Use specific exceptions
* Provide helpful error messages
* Clean up resources in finally blocks
* Log errors appropriately

Example:

.. code-block:: python

   def process_file(file_path):
       """Process a file with proper error handling."""
       if not os.path.exists(file_path):
           raise FileNotFoundError(f"File not found: {file_path}")
       
       try:
           with open(file_path, 'r') as f:
               data = f.read()
           
           # Process data
           result = process_data(data)
           return result
           
       except PermissionError:
           logger.error(f"Permission denied: {file_path}")
           raise
       except Exception as e:
           logger.error(f"Error processing file: {e}")
           raise

Performance
~~~~~~~~~~~

* Cache expensive operations
* Use generators for large datasets
* Profile before optimizing
* Document performance considerations

Security
~~~~~~~~

* Validate all user input
* Use safe YAML loading (``yaml.safe_load``)
* Sanitize file paths
* Don't expose sensitive data in logs

Adding New Features
-------------------

Cache Backend Example
~~~~~~~~~~~~~~~~~~~~~

To add a new cache backend:

1. Add enum value to ``CacheBackend``
2. Implement client initialization in ``CacheManager._get_client()``
3. Add serialization if needed
4. Add configuration options
5. Write tests
6. Document usage

.. code-block:: python

   class CacheBackend(Enum):
       # ... existing backends ...
       MONGODB = "mongodb"  # New backend
   
   class CacheManager:
       def _get_client(self):
           # ... existing code ...
           elif backend == 'mongodb':
               try:
                   import pymongo
                   client = pymongo.MongoClient(
                       host=CACHE_CONFIG.mongo_host,
                       port=CACHE_CONFIG.mongo_port
                   )
                   # Test connection
                   client.admin.command('ping')
                   return client
               except Exception as e:
                   console.print(f"MongoDB unavailable: {e}")
                   self.backend = CacheBackend.PICKLE
                   return self._get_client()

Editor Support Example
~~~~~~~~~~~~~~~~~~~~~~

To add support for a new editor:

1. Add to appropriate editor list
2. Implement special handling if needed
3. Test on all platforms
4. Document configuration

.. code-block:: python

   class EditorManager:
       BLOCKING_EDITORS = [
           'nano', 'vim', 'nvim', 'emacs',
           'joe'  # New editor
       ]

Community
---------

* Be respectful and inclusive
* Follow the Code of Conduct
* Help others in discussions
* Share knowledge and experiences

Getting Help
------------

* GitHub Discussions: Questions and discussions
* GitHub Issues: Bug reports and feature requests
* Documentation: https://ddf.readthedocs.io

License
-------

By contributing, you agree that your contributions will be licensed under
the MIT License.