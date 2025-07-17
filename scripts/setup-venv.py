#!/usr/bin/env python3
"""
Setup script for creating and configuring Python virtual environment
for the Mental Health Agent project.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def main():
    """Main setup function."""
    print("Setting up Mental Health Agent development environment...")
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 11):
        print("Error: Python 3.11 or higher is required")
        sys.exit(1)
    
    print(f"Using Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Determine virtual environment directory
    venv_dir = project_root / "venv"
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv {venv_dir}")
    else:
        print("Virtual environment already exists")
    
    # Determine activation script path based on OS
    if platform.system() == "Windows":
        activate_script = venv_dir / "Scripts" / "activate.bat"
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        activate_script = venv_dir / "bin" / "activate"
        pip_path = venv_dir / "bin" / "pip"
    
    # Upgrade pip in virtual environment
    print("Upgrading pip...")
    run_command(f"{pip_path} install --upgrade pip")
    
    # Install requirements
    print("Installing requirements...")
    run_command(f"{pip_path} install -r requirements.txt")
    
    # Install development dependencies
    print("Installing development dependencies...")
    dev_requirements = [
        "pre-commit==3.6.0",
        "isort==5.13.2",
        "bandit==1.7.5",
    ]
    
    for req in dev_requirements:
        run_command(f"{pip_path} install {req}")
    
    # Create .env file if it doesn't exist
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from .env.example...")
        import shutil
        shutil.copy(env_example, env_file)
        print("Please update .env file with your actual configuration values")
    
    # Setup pre-commit hooks
    print("Setting up pre-commit hooks...")
    run_command(f"{pip_path} install pre-commit", check=False)
    
    # Create pre-commit config if it doesn't exist
    precommit_config = project_root / ".pre-commit-config.yaml"
    if not precommit_config.exists():
        with open(precommit_config, "w") as f:
            f.write("""repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-r", "src/", "backend/", "config/"]
""")
    
    print("\n" + "="*60)
    print("Setup completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"   {activate_script}")
    else:
        print(f"   source {activate_script}")
    print("2. Update .env file with your configuration")
    print("3. Run the application with: python -m uvicorn backend.src.main:app --reload")
    print("\nFor Docker development:")
    print("   docker-compose up --build")

if __name__ == "__main__":
    main()