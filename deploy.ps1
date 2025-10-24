# Production Deployment Script for Windows
# Run this to build, push to DockerHub, and prepare for Portainer

param(
    [Parameter(Mandatory=$false)]
    [string]$DockerHubUsername = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "1.0.0",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipGit = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDockerPush = $false
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "🚀 Universal OCR - Production Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get Docker Hub username if not provided
if ([string]::IsNullOrEmpty($DockerHubUsername)) {
    $DockerHubUsername = Read-Host "Enter your Docker Hub username"
}

$ImageName = "$DockerHubUsername/surya-ocr"

# Step 1: Git
if (-not $SkipGit) {
    Write-Host "📝 Step 1: Git Commit & Push" -ForegroundColor Yellow
    Write-Host "-------------------------------------------" -ForegroundColor Yellow
    
    # Check if git repo exists
    if (-not (Test-Path ".git")) {
        Write-Host "  Initializing git repository..." -ForegroundColor Gray
        git init
        git branch -M main
    }
    
    # Add all files
    Write-Host "  Adding files..." -ForegroundColor Gray
    git add .
    
    # Commit
    $commitMsg = Read-Host "  Commit message (default: 'Production deployment v$Version')"
    if ([string]::IsNullOrEmpty($commitMsg)) {
        $commitMsg = "Production deployment v$Version"
    }
    
    git commit -m $commitMsg
    
    # Tag release
    Write-Host "  Creating tag v$Version..." -ForegroundColor Gray
    git tag -a "v$Version" -m "Release v$Version"
    
    # Push (if remote exists)
    $hasRemote = git remote -v | Select-String "origin"
    if ($hasRemote) {
        Write-Host "  Pushing to GitHub..." -ForegroundColor Gray
        git push origin main
        git push origin "v$Version"
        Write-Host "  ✅ Pushed to GitHub" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  No remote configured. Add with:" -ForegroundColor Yellow
        Write-Host "     git remote add origin https://github.com/YOUR_USERNAME/surya-ocr.git" -ForegroundColor Gray
        Write-Host "     git push -u origin main" -ForegroundColor Gray
    }
}

# Step 2: Build Docker Image
Write-Host ""
Write-Host "🐳 Step 2: Building Docker Image" -ForegroundColor Yellow
Write-Host "-------------------------------------------" -ForegroundColor Yellow

Write-Host "  Building production image..." -ForegroundColor Gray
docker build -f Dockerfile.production -t "surya-ocr:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  Tagging images..." -ForegroundColor Gray
docker tag "surya-ocr:latest" "surya-ocr:v$Version"
docker tag "surya-ocr:latest" "${ImageName}:latest"
docker tag "surya-ocr:latest" "${ImageName}:v$Version"

Write-Host "  ✅ Docker image built successfully" -ForegroundColor Green

# Step 3: Push to Docker Hub
if (-not $SkipDockerPush) {
    Write-Host ""
    Write-Host "📤 Step 3: Pushing to Docker Hub" -ForegroundColor Yellow
    Write-Host "-------------------------------------------" -ForegroundColor Yellow
    
    Write-Host "  Logging in to Docker Hub..." -ForegroundColor Gray
    docker login
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Pushing ${ImageName}:latest..." -ForegroundColor Gray
        docker push "${ImageName}:latest"
        
        Write-Host "  Pushing ${ImageName}:v$Version..." -ForegroundColor Gray
        docker push "${ImageName}:v$Version"
        
        Write-Host "  ✅ Images pushed to Docker Hub" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Docker login failed!" -ForegroundColor Red
        exit 1
    }
}

# Step 4: Generate Portainer Stack File
Write-Host ""
Write-Host "📋 Step 4: Generating Portainer Stack" -ForegroundColor Yellow
Write-Host "-------------------------------------------" -ForegroundColor Yellow

$portainerYaml = @"
version: '3.8'

services:
  api:
    image: ${ImageName}:latest
    container_name: surya-ocr-api
    ports:
      - "5000:5000"
    environment:
      - OLLAMA_HOST=http://192.168.0.153:11434
      - OLLAMA_VISION_MODEL=qwen2.5vl:7b
      - OLLAMA_TEXT_MODEL=gemma3:12b-it-qat
      - VISION_PROVIDER=ollama
      - GEMINI_API_KEY=
      - USE_HYBRID_OCR=true
      - PERFECT_TABLES=false
      - LOG_LEVEL=INFO
    volumes:
      - surya-ocr-data:/app/data
      - surya-ocr-logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - surya-network

  dashboard:
    image: ${ImageName}:latest
    container_name: surya-ocr-dashboard
    command: ["python", "run_dashboard.py"]
    ports:
      - "8080:8080"
    environment:
      - OLLAMA_HOST=http://192.168.0.153:11434
      - VISION_PROVIDER=ollama
    volumes:
      - surya-ocr-data:/app/data
    restart: unless-stopped
    depends_on:
      - api
    networks:
      - surya-network

networks:
  surya-network:
    driver: bridge

volumes:
  surya-ocr-data:
  surya-ocr-logs:
"@

$portainerYaml | Out-File -FilePath "portainer-stack.yml" -Encoding UTF8

Write-Host "  ✅ Created portainer-stack.yml" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "✅ DEPLOYMENT READY!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 Docker Images:" -ForegroundColor White
Write-Host "  - ${ImageName}:latest" -ForegroundColor Gray
Write-Host "  - ${ImageName}:v$Version" -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 Docker Hub:" -ForegroundColor White
Write-Host "  https://hub.docker.com/r/${ImageName}" -ForegroundColor Gray
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor White
Write-Host "  1. Open Portainer UI" -ForegroundColor Gray
Write-Host "  2. Stacks → Add Stack" -ForegroundColor Gray
Write-Host "  3. Upload: portainer-stack.yml" -ForegroundColor Gray
Write-Host "  4. Add your GEMINI_API_KEY (if using cloud)" -ForegroundColor Gray
Write-Host "  5. Deploy!" -ForegroundColor Gray
Write-Host ""
Write-Host "🌐 After Deployment:" -ForegroundColor White
Write-Host "  API:       http://your-server:5000" -ForegroundColor Gray
Write-Host "  Dashboard: http://your-server:8080" -ForegroundColor Gray
Write-Host "  Docs:      http://your-server:5000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "🎉 You're ready to go!" -ForegroundColor Green
Write-Host ""

