# Mental Health Agent Startup Script for Windows PowerShell
# This script helps set up and start the Mental Health Agent system on Windows

param(
    [switch]$SkipChecks,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to test if port is available
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $false  # Port is in use
    }
    catch {
        return $true   # Port is available
    }
}

# Function to generate random password
function New-Password {
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    $password = ""
    for ($i = 0; $i -lt 25; $i++) {
        $password += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $password
}

# Function to generate JWT secret
function New-JWTSecret {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    return [System.Convert]::ToBase64String($bytes)
}

Write-Status "🚀 Starting Mental Health Agent Setup..."

# Check prerequisites
if (-not $SkipChecks) {
    Write-Status "Checking prerequisites..."

    if (-not (Test-Command "docker")) {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }

    if (-not (Test-Command "docker-compose")) {
        Write-Error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }

    Write-Success "Prerequisites check passed"
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Warning ".env file not found. Creating from template..."
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Success "Created .env file from template"
        
        # Generate secure passwords and secrets
        Write-Status "Generating secure passwords and secrets..."
        
        $postgresPassword = New-Password
        $redisPassword = New-Password
        $jwtSecret = New-JWTSecret
        $encryptionKey = New-JWTSecret
        
        # Update .env file with generated secrets
        try {
            $envContent = Get-Content ".env" -Raw
            $envContent = $envContent -replace "secure_postgres_password_change_me", $postgresPassword
            $envContent = $envContent -replace "secure_redis_password_change_me", $redisPassword
            $envContent = $envContent -replace "your_jwt_secret_key_change_me_in_production", $jwtSecret
            $envContent = $envContent -replace "your_encryption_key_change_me_in_production", $encryptionKey
            Set-Content ".env" $envContent
            Write-Success "Generated secure passwords and secrets"
        }
        catch {
            Write-Warning "Failed to update passwords automatically. Please manually update passwords in .env file"
        }
        
        Write-Warning "⚠️  IMPORTANT: Please update the OPENAI_API_KEY in .env file before continuing"
        Write-Warning "⚠️  IMPORTANT: Review and update other settings in .env file as needed"
        
        Read-Host "Press Enter to continue after updating .env file"
    }
    else {
        Write-Error ".env.example file not found. Cannot create .env file."
        exit 1
    }
}
else {
    Write-Success ".env file found"
}

# Check if OpenAI API key is set
$envContent = Get-Content ".env" -Raw
if ($envContent -match "your_openai_api_key_here") {
    Write-Error "OpenAI API key not set in .env file. Please update OPENAI_API_KEY before continuing."
    exit 1
}

# Check port availability
if (-not $SkipChecks) {
    Write-Status "Checking port availability..."

    $ports = @(3000, 8000, 5432, 6379, 8001)
    foreach ($port in $ports) {
        if (-not (Test-Port $port)) {
            Write-Warning "Port $port is already in use. Please stop the service using this port or change the configuration."
        }
    }
}

# Create necessary directories
Write-Status "Creating necessary directories..."
$directories = @(
    "data\postgres",
    "data\redis", 
    "data\chromadb",
    "backend\logs",
    "frontend\data",
    "frontend\static\images"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Success "Directories created"

# Pull latest images
Write-Status "Pulling latest Docker images..."
try {
    & docker-compose pull
    if ($LASTEXITCODE -ne 0) { throw "Docker compose pull failed" }
}
catch {
    Write-Error "Failed to pull Docker images: $_"
    exit 1
}

# Build custom images
Write-Status "Building custom images..."
try {
    & docker-compose build
    if ($LASTEXITCODE -ne 0) { throw "Docker compose build failed" }
}
catch {
    Write-Error "Failed to build custom images: $_"
    exit 1
}

# Start the system
Write-Status "Starting Mental Health Agent system..."

# Start databases first
Write-Status "Starting database services..."
try {
    & docker-compose up -d postgres redis chromadb
    if ($LASTEXITCODE -ne 0) { throw "Failed to start database services" }
}
catch {
    Write-Error "Failed to start database services: $_"
    exit 1
}

# Wait for databases to be ready
Write-Status "Waiting for databases to be ready..."
Start-Sleep -Seconds 10

# Check database health
Write-Status "Checking database health..."
$maxAttempts = 30
for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        & docker-compose exec -T postgres pg_isready -U mental_health_user -d mental_health_db 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "PostgreSQL is ready"
            break
        }
    }
    catch { }
    
    if ($i -eq $maxAttempts) {
        Write-Error "PostgreSQL failed to start"
        exit 1
    }
    Start-Sleep -Seconds 2
}

# Start backend
Write-Status "Starting backend service..."
try {
    & docker-compose up -d backend
    if ($LASTEXITCODE -ne 0) { throw "Failed to start backend service" }
}
catch {
    Write-Error "Failed to start backend service: $_"
    exit 1
}

# Wait for backend to be ready
Write-Status "Waiting for backend to be ready..."
$maxAttempts = 60
for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Backend is ready"
            break
        }
    }
    catch { }
    
    if ($i -eq $maxAttempts) {
        Write-Error "Backend failed to start"
        & docker-compose logs backend
        exit 1
    }
    Start-Sleep -Seconds 2
}

# Start frontend
Write-Status "Starting frontend service..."
try {
    & docker-compose up -d frontend
    if ($LASTEXITCODE -ne 0) { throw "Failed to start frontend service" }
}
catch {
    Write-Error "Failed to start frontend service: $_"
    exit 1
}

# Wait for frontend to be ready
Write-Status "Waiting for frontend to be ready..."
$maxAttempts = 60
for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success "Frontend is ready"
            break
        }
    }
    catch { }
    
    if ($i -eq $maxAttempts) {
        Write-Error "Frontend failed to start"
        & docker-compose logs frontend
        exit 1
    }
    Start-Sleep -Seconds 2
}

# Final status check
Write-Status "Performing final system health check..."

$services = @("postgres", "redis", "chromadb", "backend", "frontend")
$allHealthy = $true

foreach ($service in $services) {
    try {
        $status = & docker-compose ps $service
        if ($status -match "Up") {
            Write-Success "$service is running"
        }
        else {
            Write-Error "$service is not running"
            $allHealthy = $false
        }
    }
    catch {
        Write-Error "$service status check failed"
        $allHealthy = $false
    }
}

if ($allHealthy) {
    Write-Success "🎉 Mental Health Agent is now running!"
    Write-Host ""
    Write-Host "📱 Frontend (Open WebUI): http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📊 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "🗄️  Database: localhost:5432" -ForegroundColor Cyan
    Write-Host "🔍 ChromaDB: http://localhost:8001" -ForegroundColor Cyan
    Write-Host ""
    Write-Status "To stop the system, run: docker-compose down"
    Write-Status "To view logs, run: docker-compose logs -f [service_name]"
    Write-Status "To restart a service, run: docker-compose restart [service_name]"
    Write-Host ""
    Write-Warning "⚠️  Remember to:"
    Write-Warning "   - Keep your .env file secure and never commit it to version control"
    Write-Warning "   - Regularly backup your data"
    Write-Warning "   - Monitor the system logs for any issues"
    Write-Warning "   - Update passwords and secrets regularly in production"
}
else {
    Write-Error "Some services failed to start. Please check the logs:"
    Write-Host "docker-compose logs" -ForegroundColor Yellow
    exit 1
}
