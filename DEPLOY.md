# 🚀 Complete Deployment Guide

Step-by-step guide to build, push, and deploy your Universal OCR System.

---

## 📋 Prerequisites

- ✅ Docker installed
- ✅ Docker Hub account: https://hub.docker.com
- ✅ GitHub account
- ✅ Portainer running on your server
- ✅ Git configured locally

---

## Step 1: Initialize Git Repository

```powershell
# Initialize git (if not done)
git init

# Add all files
git add .

# Initial commit
git commit -m "Production-ready Universal OCR System"

# Create GitHub repo (replace YOUR_USERNAME)
# Go to https://github.com/new
# Name: surya-ocr
# Description: Universal OCR system with multi-provider AI vision
# Public/Private: Your choice
# Don't initialize with README (we have one)

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/surya-ocr.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 2: Build Docker Image

```powershell
# Build production image
docker build -f Dockerfile.production -t surya-ocr:latest .

# Tag with version
docker tag surya-ocr:latest surya-ocr:v1.0.0

# Tag for Docker Hub (replace YOUR_USERNAME)
docker tag surya-ocr:latest YOUR_USERNAME/surya-ocr:latest
docker tag surya-ocr:latest YOUR_USERNAME/surya-ocr:v1.0.0

# Verify images
docker images | Select-String "surya-ocr"
```

**Expected output:**
```
YOUR_USERNAME/surya-ocr   latest    abc123...   2 minutes ago   1.2GB
YOUR_USERNAME/surya-ocr   v1.0.0    abc123...   2 minutes ago   1.2GB
surya-ocr                 latest    abc123...   2 minutes ago   1.2GB
surya-ocr                 v1.0.0    abc123...   2 minutes ago   1.2GB
```

---

## Step 3: Push to Docker Hub

```powershell
# Login to Docker Hub
docker login
# Enter your Docker Hub username and password

# Push images
docker push YOUR_USERNAME/surya-ocr:latest
docker push YOUR_USERNAME/surya-ocr:v1.0.0
```

**This will take 5-10 minutes depending on your upload speed.**

---

## Step 4: Create Portainer Stack

### Option A: Via Portainer UI (Recommended)

1. **Open Portainer**: `http://your-server:9000`

2. **Navigate to Stacks**: 
   - Click "Stacks" in left menu
   - Click "+ Add stack"

3. **Configure Stack**:
   - **Name**: `surya-ocr`
   - **Build method**: "Web editor"
   
4. **Paste this docker-compose**:

```yaml
version: '3.8'

services:
  api:
    image: YOUR_USERNAME/surya-ocr:latest
    container_name: surya-ocr-api
    ports:
      - "5000:5000"
    environment:
      # Ollama (adjust to your Ollama server)
      - OLLAMA_HOST=http://192.168.0.153:11434
      - OLLAMA_VISION_MODEL=qwen2.5vl:7b
      - OLLAMA_TEXT_MODEL=gemma3:12b-it-qat
      
      # Vision Provider
      - VISION_PROVIDER=ollama
      
      # API Keys (add your keys below)
      - GEMINI_API_KEY=
      - OPENAI_API_KEY=
      - ANTHROPIC_API_KEY=
      
      # Models
      - GEMINI_MODEL=gemini-2.0-flash-exp
      
      # OCR Settings
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
    image: YOUR_USERNAME/surya-ocr:latest
    container_name: surya-ocr-dashboard
    command: ["python", "run_dashboard.py"]
    ports:
      - "8080:8080"
    environment:
      - OLLAMA_HOST=http://192.168.0.153:11434
      - VISION_PROVIDER=ollama
      - GEMINI_API_KEY=
    
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
```

5. **Environment Variables** (scroll down):
   - Click "+ Add environment variable"
   - Add your `GEMINI_API_KEY` if using cloud providers
   - Or leave empty for local-only mode

6. **Deploy**: Click "Deploy the stack"

7. **Wait**: Initial deployment takes 1-2 minutes

### Option B: Via Portainer CLI

```bash
# SSH to your server
ssh user@your-server

# Create stack directory
mkdir -p ~/portainer/surya-ocr
cd ~/portainer/surya-ocr

# Create docker-compose.yml (paste content from above)
nano docker-compose.yml

# Deploy via Portainer API
curl -X POST http://localhost:9000/api/stacks \
  -H "X-API-Key: YOUR_PORTAINER_API_KEY" \
  -F "Name=surya-ocr" \
  -F "StackFileContent=@docker-compose.yml"
```

---

## Step 5: Verify Deployment

### Check Portainer

1. **Stacks** → `surya-ocr` → Should be "running"
2. **Containers**: Both `surya-ocr-api` and `surya-ocr-dashboard` should be green
3. **Logs**: Click on container → View logs for any errors

### Test API

```powershell
# Health check
curl http://YOUR_SERVER:5000/health

# Test OCR (replace with your server IP)
curl -X POST http://YOUR_SERVER:5000/ocr_universal \
  -F "image=@test.jpg" \
  -F "format=markdown"
```

### Access Dashboard

Open browser: `http://YOUR_SERVER:8080`

---

## Step 6: Update .env for Production

On your Portainer server, you can update environment variables without rebuilding:

1. **Portainer** → **Stacks** → `surya-ocr`
2. **Editor** tab
3. Update environment variables
4. Click "Update the stack"
5. Select "Re-pull image and redeploy" if you pushed a new image

---

## 🔄 Updating the System

### When You Make Code Changes

```powershell
# 1. Commit to git
git add .
git commit -m "Feature: your changes"
git push origin main

# 2. Build new Docker image
docker build -f Dockerfile.production -t YOUR_USERNAME/surya-ocr:latest .

# 3. Push to Docker Hub
docker push YOUR_USERNAME/surya-ocr:latest

# 4. Update in Portainer
#    → Stacks → surya-ocr → Re-pull and redeploy
```

### Quick Update Without Rebuild

If you only changed environment variables:

1. Portainer → Stacks → surya-ocr → Editor
2. Change env vars
3. Update stack (no rebuild needed!)

---

## 📊 Monitoring

### View Logs in Portainer

- **API Logs**: Containers → surya-ocr-api → Logs
- **Dashboard Logs**: Containers → surya-ocr-dashboard → Logs
- **Follow live**: Enable "Auto-refresh logs"

### Check Resource Usage

- Containers → surya-ocr-api → Stats
- View CPU, RAM, Network usage

### Health Status

```bash
# API health endpoint
curl http://YOUR_SERVER:5000/health

# Returns:
{
  "status": "healthy",
  "vision_provider": "ollama",
  "ocr_engines": {
    "tesseract": true,
    "surya": true
  }
}
```

---

## 🎯 Recommended Settings for Production

### Conservative (Free, Local)
```yaml
environment:
  - VISION_PROVIDER=ollama
  - PERFECT_TABLES=false
```
**Result**: $0 cost, 90% quality

### Balanced (Best Value)
```yaml
environment:
  - VISION_PROVIDER=ollama
  - PERFECT_TABLES=true
  - GEMINI_API_KEY=your_key
  - GEMINI_MODEL=gemini-2.0-flash-exp
```
**Result**: ~$5/1000 docs, 98% quality

### Premium (Maximum Quality)
```yaml
environment:
  - VISION_PROVIDER=gemini
  - GEMINI_MODEL=gemini-1.5-pro
  - GEMINI_API_KEY=your_key
```
**Result**: ~$100/1000 docs, 98%+ quality

---

## 🔧 Troubleshooting

### Build Fails

```powershell
# Check Docker is running
docker info

# Build with no cache
docker build --no-cache -f Dockerfile.production -t surya-ocr:latest .
```

### Push Fails

```powershell
# Re-login
docker logout
docker login

# Check image name matches your username
docker tag surya-ocr:latest YOUR_USERNAME/surya-ocr:latest
```

### Portainer Can't Pull

- Ensure image is public on Docker Hub
- Or add Docker Hub credentials in Portainer:
  - Settings → Registries → Add registry

### Container Won't Start

Check logs in Portainer for errors. Common issues:
- Missing `OLLAMA_HOST`
- Port already in use
- API key formatting error

---

## ✅ Deployment Checklist

- [ ] Code committed to git
- [ ] Pushed to GitHub
- [ ] Docker image built locally
- [ ] Tested locally with `docker-compose up`
- [ ] Pushed to Docker Hub
- [ ] Created Portainer stack
- [ ] Verified API accessible
- [ ] Verified dashboard accessible
- [ ] Tested OCR endpoint
- [ ] Monitored logs for errors

---

## 🎉 You're Live!

Once deployed:
- **API**: `http://your-server:5000/ocr_universal`
- **Dashboard**: `http://your-server:8080`
- **Docs**: `http://your-server:5000/docs` (FastAPI auto-docs)

**Ready to process thousands of documents!** 🚀

