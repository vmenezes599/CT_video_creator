# Copilot Instructions

## VS Code Copilot Instructions

- Always run tests using terminal and not using integrated VSCode's builtin Testing feature.
- In tests, always create local copy of files

## Python Copilot Instructions

These instructions guide GitHub Copilot when assisting with Python development.

### Naming Conventions

- Use `__` (double underscore) for private variables and methods.
  - Example: `self.__settings`, `self.__queue`
- Use `_` (single underscore) for protected variables and methods.
  - Example: `self._cleanup_zip_file`
- Use no prefix for public methods and attributes.
  - Example: `get_queue_list()`, `add_to_queue()`

### Guidelines

- Default to private (`__`) unless there's a reason to expose.
- Use protected (`_`) only if needed for testing.
- Keep the public API minimal and well-documented.

### Typing

- Use built-in types (`list`, `dict`, etc.) instead of `typing` equivalents.

```python
# Correct
def get_items() -> list[str]: ...

# Avoid
from typing import List
def get_items() -> List[str]: ...
