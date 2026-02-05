# Python Automation Project Standards and Guidelines

## Project Structure

All automation projects must follow a consistent, single-folder structure:

```
project-name/
├── README.md
├── requirements.txt
├── config.yaml (or config.json)
├── .env.example
├── .gitignore
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── API.md (if applicable)
└── logs/
    └── .gitkeep
```

- All code, configuration, and documentation must reside within a single project folder
- No scattered files across multiple directories
- Each project is self-contained and portable

## Git Commit Message Standards

Follow conventional commit format with clear, concise messages:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat: add email notification system for price alerts

Implement SMTP integration with configurable templates and error handling.
Add retry logic for failed email deliveries.

fix: resolve duplicate file detection issue in organizer script

Correct hash comparison logic to prevent false positives when files have identical content but different metadata.

docs: update README with installation instructions

Add step-by-step setup guide and environment variable configuration details.
```

### Rules
- Use imperative mood ("add" not "added" or "adds")
- First line should be 50 characters or less
- Capitalize first letter of subject
- No period at end of subject line
- Reference issues in footer when applicable: `Closes #123`

## Documentation Requirements

### README.md Structure

Every project must include a comprehensive README with:

1. **Project Title and Description**
   - Clear, concise project purpose
   - What problem it solves
   - Target audience

2. **Features**
   - Bulleted list of key capabilities
   - What the automation does

3. **Prerequisites**
   - Python version requirements
   - System dependencies
   - Required external services or APIs

4. **Installation**
   - Step-by-step setup instructions
   - Virtual environment setup
   - Dependency installation
   - Configuration file setup

5. **Configuration**
   - Environment variables
   - Configuration file structure
   - Required credentials and API keys
   - Example configuration

6. **Usage**
   - Command-line usage examples
   - Configuration options
   - Common use cases

7. **Project Structure**
   - Directory tree explanation
   - File purpose descriptions

8. **Testing**
   - How to run tests
   - Test coverage information

9. **Troubleshooting**
   - Common issues and solutions
   - Error message explanations

10. **Contributing**
    - Development setup
    - Code style guidelines
    - Pull request process

11. **License**
    - License information

### Code Documentation

- All functions and classes must have docstrings following Google or NumPy style
- Module-level docstrings explaining purpose and usage
- Complex logic must have inline comments explaining the "why", not the "what"
- Type hints required for all function parameters and return values

### Docstring Format

```python
def process_files(source_dir: str, destination_dir: str, pattern: str = "*.txt") -> dict:
    """Process files matching pattern and move to destination.
    
    Scans source directory for files matching the specified pattern,
    validates each file, and moves valid files to destination directory.
    Maintains metadata and logs all operations.
    
    Args:
        source_dir: Path to source directory containing files to process
        destination_dir: Path to destination directory for processed files
        pattern: File pattern to match (default: "*.txt")
    
    Returns:
        Dictionary containing:
            - processed: Number of files successfully processed
            - failed: Number of files that failed processing
            - errors: List of error messages for failed files
    
    Raises:
        FileNotFoundError: If source_dir does not exist
        PermissionError: If destination_dir is not writable
    
    Example:
        >>> result = process_files("/data/source", "/data/dest", "*.log")
        >>> print(result['processed'])
        42
    """
```

## Code Quality Standards

### Python Style Guide

- Follow PEP 8 strictly
- Maximum line length: 88 characters (Black formatter standard)
- Use type hints for all function signatures
- Use meaningful variable and function names
- Avoid abbreviations unless widely understood
- Use descriptive names: `user_email_address` not `ueml`

### Code Organization

- One class per file (unless closely related)
- Functions should do one thing well
- Maximum function length: 50 lines
- Maximum class length: 300 lines
- Use composition over inheritance when possible

### Error Handling

- Always use specific exception types
- Never use bare `except:` clauses
- Provide meaningful error messages
- Log errors with appropriate levels
- Use context managers for resource management

```python
# Good
try:
    with open(filepath, 'r') as f:
        data = f.read()
except FileNotFoundError:
    logger.error(f"Configuration file not found: {filepath}")
    raise
except PermissionError:
    logger.error(f"Insufficient permissions to read: {filepath}")
    raise

# Bad
try:
    data = open(filepath).read()
except:
    pass
```

### Logging

- Use Python's logging module, not print statements
- Configure logging with appropriate levels
- Include timestamps and context in log messages
- Use structured logging for production code

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing started", extra={"file_count": len(files)})
logger.warning("Low disk space detected", extra={"available_gb": 2.5})
logger.error("Failed to connect to API", extra={"endpoint": url, "status": 503})
```

### Configuration Management

- Never hardcode configuration values
- Use environment variables for secrets
- Use configuration files (YAML/JSON) for settings
- Provide `.env.example` template
- Validate configuration on startup

### Dependencies

- Pin exact versions in `requirements.txt` for reproducibility
- Document why each dependency is needed
- Keep dependencies minimal
- Regularly update and audit dependencies

```txt
requests==2.31.0  # HTTP library for API calls
python-dotenv==1.0.0  # Environment variable management
pydantic==2.5.0  # Data validation and settings management
```

## Commenting Guidelines

### What to Comment

- Complex algorithms or business logic
- Non-obvious design decisions
- Workarounds for known issues
- Performance optimizations
- Integration points with external systems

### What NOT to Comment

- Obvious code (self-documenting code is preferred)
- What the code does (code should be clear)
- AI-generated placeholder comments
- TODO comments without context or ticket numbers
- Commented-out code (remove it)

### Comment Style

```python
# Good: Explains why, not what
# Using binary search here because the list is pre-sorted
# and we need O(log n) performance for large datasets
index = bisect.bisect_left(sorted_list, target)

# Bad: States the obvious
# Loop through the list
for item in items:
    # Process each item
    process(item)
```

## Professional Standards

### Prohibited Elements

- No emojis in code, comments, or documentation
- No em dashes (use regular hyphens or colons)
- No casual language or slang
- No placeholder text or lorem ipsum
- No "Hello World" or example code in production

### Language and Tone

- Use professional, technical language
- Be precise and specific
- Avoid marketing speak
- Write for an audience of experienced developers
- Assume reader has Python knowledge but not domain knowledge

### Code Examples

- All examples must be production-ready
- Include error handling
- Show best practices
- Use realistic data and scenarios

## Testing Standards

- Write tests for all public functions and classes
- Aim for minimum 80% code coverage
- Use descriptive test names that explain what is being tested
- Follow Arrange-Act-Assert pattern
- Use fixtures for common setup
- Mock external dependencies

```python
def test_process_files_handles_missing_source_directory():
    """Test that FileNotFoundError is raised when source directory doesn't exist."""
    with pytest.raises(FileNotFoundError):
        process_files("/nonexistent/path", "/tmp/dest")
```

## Security Best Practices

- Never commit secrets, API keys, or passwords
- Use environment variables for sensitive data
- Validate and sanitize all user inputs
- Use parameterized queries for database operations
- Implement rate limiting for API calls
- Use HTTPS for all network communications
- Keep dependencies updated for security patches

## Performance Considerations

- Profile code before optimizing
- Use appropriate data structures
- Avoid premature optimization
- Cache expensive operations when appropriate
- Use generators for large datasets
- Consider async/await for I/O-bound operations

## File Naming Conventions

- Use lowercase with underscores: `file_processor.py`
- Be descriptive: `email_notifier.py` not `email.py`
- Match module purpose: `config_loader.py` for configuration loading
- Test files: `test_<module_name>.py`

## Import Organization

Follow PEP 8 import order:

1. Standard library imports
2. Related third-party imports
3. Local application/library imports

Separate groups with blank lines.

```python
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

from src.config import Settings
from src.utils import validate_path
```

## Version Control

- Use meaningful branch names: `feature/email-notifications`, `fix/duplicate-detection`
- Keep commits atomic and focused
- Write clear commit messages
- Review code before committing
- Never commit:
  - `.env` files
  - `__pycache__/` directories
  - IDE-specific files
  - Large binary files

## Checklist Before Submission

- [ ] All code follows PEP 8
- [ ] Type hints added to all functions
- [ ] Docstrings for all public functions and classes
- [ ] README.md is complete and accurate
- [ ] Requirements.txt is up to date
- [ ] Tests written and passing
- [ ] No hardcoded secrets or credentials
- [ ] Error handling implemented
- [ ] Logging configured appropriately
- [ ] Code is commented where necessary (explaining why, not what)
- [ ] No emojis or casual language
- [ ] Professional documentation
- [ ] All files in single project folder
- [ ] .gitignore properly configured

## Additional Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Real Python Best Practices](https://realpython.com/python-code-quality/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
