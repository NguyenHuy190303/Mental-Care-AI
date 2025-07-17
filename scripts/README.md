# Development Scripts

This directory contains utility scripts for setting up and managing the Mental Health Agent development environment.

## Scripts

### `setup-dev.py`
Complete development environment setup script that:
- Checks prerequisites (Python, Docker, Node.js)
- Sets up Python virtual environment
- Installs all dependencies
- Creates configuration files
- Sets up frontend dependencies
- Runs validation tests

**Usage:**
```bash
python scripts/setup-dev.py
```

### `setup-venv.py`
Python virtual environment setup script that:
- Creates virtual environment
- Installs Python dependencies
- Sets up pre-commit hooks
- Creates .env file from template

**Usage:**
```bash
python scripts/setup-venv.py
```

### `test-config.py`
Configuration validation script that tests:
- Environment variable loading
- Logging configuration
- Directory structure
- Required dependencies

**Usage:**
```bash
python scripts/test-config.py
```

## Quick Start

For a complete development environment setup:

```bash
# Run the complete setup
python scripts/setup-dev.py

# Or just setup Python environment
python scripts/setup-venv.py

# Test configuration
python scripts/test-config.py
```

## Prerequisites

- Python 3.11+
- Docker (optional, for containerized development)
- Node.js 18+ (optional, for frontend development)