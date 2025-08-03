# .temp Directory

This directory contains temporary files, caches, and build artifacts to keep the main project directory clean.

## Contents:
- `ruff/` - Ruff linter cache
- `mypy/` - MyPy type checker cache  
- `pytest/` - Pytest cache directory
- `htmlcov/` - HTML coverage reports
- Other temporary build and test artifacts

## Benefits:
- Keeps main project directory clean
- All temporary files in one location
- Easy to clean up with `rm -rf .temp/*`
- Excluded from git via .gitignore

## Usage:
Tools are configured in pyproject.toml and pytest.ini to automatically use this directory.