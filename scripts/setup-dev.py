#!/usr/bin/env python3
"""
Complete development environment setup script for Mental Health Agent.
This script sets up everything needed for development.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def run_command(command, check=True, cwd=None):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            return None
        return e

def check_prerequisites():
    """Check if required tools are installed."""
    print("Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 11):
        print("❌ Error: Python 3.11 or higher is required")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check Docker
    docker_result = run_command("docker --version", check=False)
    if docker_result and docker_result.returncode == 0:
        print("✅ Docker is available")
    else:
        print("⚠️  Docker not found - Docker features will be unavailable")
    
    # Check Docker Compose
    compose_result = run_command("docker-compose --version", check=False)
    if compose_result and compose_result.returncode == 0:
        print("✅ Docker Compose is available")
    else:
        print("⚠️  Docker Compose not found - Docker features will be unavailable")
    
    # Check Node.js (for frontend)
    node_result = run_command("node --version", check=False)
    if node_result and node_result.returncode == 0:
        print("✅ Node.js is available")
    else:
        print("⚠️  Node.js not found - Frontend development will require Node.js")
    
    return True

def setup_python_environment():
    """Set up Python virtual environment and install dependencies."""
    print("\n" + "="*50)
    print("Setting up Python environment...")
    print("="*50)
    
    project_root = Path(__file__).parent.parent
    venv_dir = project_root / "venv"
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print("Creating virtual environment...")
        result = run_command(f"{sys.executable} -m venv {venv_dir}")
        if not result:
            print("❌ Failed to create virtual environment")
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Determine pip path based on OS
    if platform.system() == "Windows":
        pip_path = venv_dir / "Scripts" / "pip.exe"
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"
        python_path = venv_dir / "bin" / "python"
    
    # Upgrade pip
    print("Upgrading pip...")
    result = run_command(f"{pip_path} install --upgrade pip")
    if not result:
        print("❌ Failed to upgrade pip")
        return False
    
    # Install requirements
    print("Installing requirements...")
    result = run_command(f"{pip_path} install -r requirements.txt")
    if not result:
        print("❌ Failed to install requirements")
        return False
    
    print("✅ Python environment setup complete")
    return True

def setup_environment_files():
    """Set up environment configuration files."""
    print("\n" + "="*50)
    print("Setting up environment files...")
    print("="*50)
    
    project_root = Path(__file__).parent.parent
    
    # Create .env file if it doesn't exist
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from .env.example...")
        shutil.copy(env_example, env_file)
        print("✅ .env file created")
        print("⚠️  Please update .env file with your actual configuration values")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ .env.example not found")
        return False
    
    # Create docker-compose.override.yml if it doesn't exist
    override_file = project_root / "docker-compose.override.yml"
    override_example = project_root / "docker-compose.override.yml.example"
    
    if not override_file.exists() and override_example.exists():
        print("Creating docker-compose.override.yml...")
        shutil.copy(override_example, override_file)
        print("✅ docker-compose.override.yml created")
    elif override_file.exists():
        print("✅ docker-compose.override.yml already exists")
    
    return True

def setup_frontend():
    """Set up frontend dependencies."""
    print("\n" + "="*50)
    print("Setting up frontend...")
    print("="*50)
    
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    
    # Check if Node.js is available
    node_result = run_command("node --version", check=False)
    if not node_result or node_result.returncode != 0:
        print("⚠️  Node.js not found - skipping frontend setup")
        return True
    
    # Install frontend dependencies
    if (frontend_dir / "package.json").exists():
        print("Installing frontend dependencies...")
        result = run_command("npm install", cwd=frontend_dir)
        if result and result.returncode == 0:
            print("✅ Frontend dependencies installed")
        else:
            print("❌ Failed to install frontend dependencies")
            return False
    else:
        print("⚠️  package.json not found in frontend directory")
    
    return True

def run_tests():
    """Run configuration tests."""
    print("\n" + "="*50)
    print("Running configuration tests...")
    print("="*50)
    
    # Run the test configuration script
    result = run_command("python scripts/test-config.py", check=False)
    if result and result.returncode == 0:
        print("✅ All configuration tests passed")
        return True
    else:
        print("⚠️  Some configuration tests failed - check output above")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*60)
    print("🎉 Development Environment Setup Complete!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Update your .env file with actual API keys and configuration")
    print("2. Choose your development approach:")
    print("\n   🐍 Python Development:")
    if platform.system() == "Windows":
        print("      - Activate virtual environment: venv\\Scripts\\activate")
    else:
        print("      - Activate virtual environment: source venv/bin/activate")
    print("      - Run backend: python -m uvicorn backend.src.main:app --reload")
    
    print("\n   🐳 Docker Development:")
    print("      - Start all services: docker-compose up --build")
    print("      - View logs: docker-compose logs -f")
    print("      - Stop services: docker-compose down")
    
    print("\n🔧 Development Tools:")
    print("   - Backend API: http://localhost:8000")
    print("   - Frontend: http://localhost:3000")
    print("   - ChromaDB: http://localhost:8001")
    print("   - PostgreSQL: localhost:5432")
    print("   - Redis: localhost:6379")
    print("   - PgAdmin: http://localhost:5050 (with dev-tools profile)")
    
    print("\n📚 Documentation:")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Development Guide: DEVELOPMENT.md")
    
    print("\n⚠️  Important:")
    print("   - Never commit .env files to version control")
    print("   - Update API keys in .env before running")
    print("   - Check DEVELOPMENT.md for detailed instructions")

def main():
    """Main setup function."""
    print("🚀 Mental Health Agent - Development Environment Setup")
    print("="*60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites check failed")
        sys.exit(1)
    
    # Setup steps
    setup_steps = [
        ("Python Environment", setup_python_environment),
        ("Environment Files", setup_environment_files),
        ("Frontend Setup", setup_frontend),
    ]
    
    failed_steps = []
    for step_name, step_func in setup_steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    # Run tests (optional)
    print("\n" + "="*50)
    print("Running final validation...")
    print("="*50)
    run_tests()
    
    # Print results
    if failed_steps:
        print(f"\n⚠️  Setup completed with issues in: {', '.join(failed_steps)}")
        print("Please check the output above and resolve any issues.")
    else:
        print("\n✅ All setup steps completed successfully!")
    
    print_next_steps()

if __name__ == "__main__":
    main()