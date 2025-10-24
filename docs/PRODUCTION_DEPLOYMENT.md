# 🚀 Production Deployment Guide

Complete guide to deploying the Universal OCR System to production using Docker, Portainer, GitHub, and DockerHub.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Configuration](#configuration)
3. [Local Docker Deployment](#local-docker-deployment)
4. [Portainer Deployment](#portainer-deployment)
5. [GitHub & DockerHub](#github--dockerhub)
6. [Settings Dashboard](#settings-dashboard)
7. [Monitoring & Maintenance](#monitoring--maintenance)

---

## System Overview

### What You're Deploying:

```
┌─────────────────────────────────────────┐
│  FastAPI OCR API (Port 5000)           │
│  - /ocr_universal endpoint              │
│  - Gemini Flash / Local model support  │
│  - Hybrid dual-engine OCR               │
└─────────────────────────────────────────┘
              ↕️
┌─────────────────────────────────────────┐
│  Settings Dashboard (Port 8080)         │
│  - Control defaults (Gemini/Local)      │
│  - Toggle perfect_tables                │
│  - Monitor usage & costs                │
└─────────────────────────────────────────┘
              ↕️
┌─────────────────────────────────────────┐
│  External Services                       │
│  - Ollama (192.168.0.153:11434)        │
│  - Gemini API (cloud)                   │
└─────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Ollama Configuration (Local Models)
OLLAMA_HOST=http://192.168.0.153:11434
OLLAMA_VISION_MODEL=qwen2.5vl:7b
OLLAMA_TEXT_MODEL=gemma3:12b-it-qat

# Gemini Configuration (Cloud API)
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp  # Options: gemini-2.0-flash-exp (free), gemini-1.5-flash (cheap), gemini-1.5-pro (best)

# Default OCR Behavior
USE_GEMINI_VISION=false  # true = always use Gemini, false = local only
USE_HYBRID_OCR=true  # true = run Tesseract+Surya parallel
PERFECT_TABLES=false  # true = use Gemini for tables only

# API Ports
API_PORT=5000
DASHBOARD_PORT=8080

# Logging
LOG_LEVEL=INFO
```

### Model Cost Comparison

| Model | Speed | Quality | Cost/1K docs | Best For |
|-------|-------|---------|--------------|----------|
| **Local Only** | Fast | 90% | $0 | Default, privacy-critical |
| **Gemini Flash** | Fastest | 98% | $10 | Perfect tables, business docs |
| **Gemini Pro** | Fast | 98%+ | $100 | Maximum quality, legal/medical |

---

## Local Docker Deployment

### 1. Build Docker Image

```bash
cd surya-ocr

# Build
docker build -t surya-ocr:latest .

# Tag for versioning
docker tag surya-ocr:latest surya-ocr:v1.0
```

### 2. Run with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ocr-api:
    image: surya-ocr:latest
    container_name: surya-ocr-api
    ports:
      - "5000:5000"
    environment:
      - OLLAMA_HOST=http://192.168.0.153:11434
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL=gemini-2.0-flash-exp
      - USE_GEMINI_VISION=false
      - PERFECT_TABLES=false
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - ocr-network

  dashboard:
    image: surya-ocr:latest
    container_name: surya-ocr-dashboard
    command: python -m uvicorn dashboard.api:dashboard_app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    environment:
      - OLLAMA_HOST=http://192.168.0.153:11434
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    networks:
      - ocr-network

networks:
  ocr-network:
    driver: bridge

volumes:
  data:
  logs:
```

### 3. Deploy

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ocr-api
docker-compose logs -f dashboard

# Stop services
docker-compose down
```

---

## Portainer Deployment

### Method 1: Portainer Stacks (Recommended)

1. **Access Portainer**: `http://your-server:9000`
2. **Navigate**: Stacks → Add Stack
3. **Name**: `surya-ocr`
4. **Paste** the `docker-compose.yml` above
5. **Environment Variables**: Add your secrets
   - `GEMINI_API_KEY`: your_key_here
6. **Deploy**: Click "Deploy the stack"

### Method 2: Portainer App Templates

Create app template at `/portainer/templates.json`:

```json
{
  "version": "2",
  "templates": [
    {
      "type": 3,
      "title": "Universal OCR System",
      "description": "AI-powered OCR with local & cloud models",
      "note": "Requires Gemini API key for cloud features",
      "categories": ["AI", "OCR", "Productivity"],
      "platform": "linux",
      "logo": "https://raw.githubusercontent.com/yourusername/surya-ocr/main/logo.png",
      "repository": {
        "url": "https://github.com/yourusername/surya-ocr",
        "stackfile": "docker-compose.yml"
      },
      "env": [
        {
          "name": "GEMINI_API_KEY",
          "label": "Gemini API Key",
          "description": "Optional. Get from https://aistudio.google.com/apikey"
        },
        {
          "name": "PERFECT_TABLES",
          "label": "Perfect Tables Mode",
          "default": "false",
          "select": [
            {"text": "Disabled (Free)", "value": "false"},
            {"text": "Enabled ($0.005/doc)", "value": "true"}
          ]
        }
      ]
    }
  ]
}
```

### Accessing Services in Portainer

- **API**: `http://your-server:5000`
- **Dashboard**: `http://your-server:8080`
- **Logs**: Portainer → Containers → select → Logs
- **Stats**: Portainer → Containers → select → Stats

---

## GitHub & DockerHub

### GitHub Workflow

Create `.github/workflows/docker-publish.yml`:

```yaml
name: Docker Build & Publish

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
  IMAGE_NAME: surya-ocr

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to DockerHub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ secrets.DOCKERHUB_USERNAME }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### Publishing Steps

```bash
# 1. Create GitHub repo
gh repo create surya-ocr --public --description "Universal OCR with AI"

# 2. Push code
git add .
git commit -m "Production-ready OCR system"
git push origin main

# 3. Tag release
git tag -a v1.0.0 -m "First production release"
git push origin v1.0.0

# 4. DockerHub will auto-build via GitHub Actions
```

### DockerHub Setup

1. **Login**: https://hub.docker.com
2. **Create Repository**: `yourusername/surya-ocr`
3. **Add Secrets** in GitHub:
   - `DOCKERHUB_USERNAME`: your_username
   - `DOCKERHUB_TOKEN`: access_token
4. **Auto-build** triggers on push

### Pull & Deploy

```bash
# On any server
docker pull yourusername/surya-ocr:latest
docker run -p 5000:5000 --env-file .env yourusername/surya-ocr:latest
```

---

## Settings Dashboard

### Accessing the Dashboard

```
http://your-server:8080
```

### Features:

**1. Default Settings Control**
- Toggle `use_gemini_vision` (local vs cloud)
- Toggle `perfect_tables` (standard vs perfect)
- Select `gemini_model` (Flash vs Pro)
- Configure Ollama models

**2. Cost Monitoring**
- Track API usage
- Estimate costs
- Set budget limits

**3. Test Interface**
- Upload images
- Test different settings
- Compare results

**4. Metrics Dashboard**
- Documents processed
- Average cost/doc
- Success rate
- Processing time

### API Endpoints for Dashboard

```python
# Get current settings
GET /api/settings

# Update settings
POST /api/settings
{
  "use_gemini_vision": false,
  "perfect_tables": true,
  "gemini_model": "gemini-2.0-flash-exp"
}

# Get usage metrics
GET /api/metrics
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# API health
curl http://localhost:5000/health

# Ollama connection
curl http://192.168.0.153:11434/api/tags

# Check logs
docker logs surya-ocr-api --tail 100 -f
```

### Backup Strategy

```bash
# Backup data directory
tar -czf ocr-backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf ocr-backup-YYYYMMDD.tar.gz
```

### Updating

```bash
# Pull latest
docker pull yourusername/surya-ocr:latest

# Restart with new image
docker-compose down
docker-compose up -d

# Or in Portainer: Containers → select → Recreate
```

### Scaling

**Horizontal Scaling:**
```yaml
# docker-compose.yml
services:
  ocr-api:
    deploy:
      replicas: 3  # Run 3 instances
    
  nginx:  # Add load balancer
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
```

**Vertical Scaling:**
```yaml
# Increase resources
services:
  ocr-api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Test locally with `docker-compose up`
- [ ] Verify Ollama connection
- [ ] Test Gemini API key
- [ ] Set up monitoring
- [ ] Configure backups

### Deployment
- [ ] Push to GitHub
- [ ] Build Docker image
- [ ] Push to DockerHub
- [ ] Deploy in Portainer
- [ ] Test API endpoints
- [ ] Test dashboard access

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Test OCR with sample documents
- [ ] Verify cost tracking
- [ ] Set up alerts
- [ ] Document for team

---

## Troubleshooting

### Issue: API not responding
```bash
# Check if container is running
docker ps | grep surya-ocr

# Check logs
docker logs surya-ocr-api

# Restart
docker restart surya-ocr-api
```

### Issue: Ollama connection failed
```bash
# Test from container
docker exec surya-ocr-api curl http://192.168.0.153:11434/api/tags

# Check network
docker network inspect ocr-network
```

### Issue: Gemini API errors
```bash
# Verify API key
docker exec surya-ocr-api env | grep GEMINI

# Test API
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models
```

---

## Cost Optimization

### Strategy 1: Local-First with Gemini Fallback
```bash
USE_GEMINI_VISION=false
PERFECT_TABLES=true  # Only for documents with tables
```
**Result**: ~$0.005/doc average (95% savings)

### Strategy 2: Pure Local
```bash
USE_GEMINI_VISION=false
PERFECT_TABLES=false
```
**Result**: $0/doc (but 90% quality vs 98%)

### Strategy 3: Gemini Flash Always
```bash
USE_GEMINI_VISION=true
GEMINI_MODEL=gemini-2.0-flash-exp  # Free during preview!
```
**Result**: $0 (preview) → ~$0.01/doc (after preview ends)

---

## Next Steps

1. **Deploy to staging**: Test with real documents
2. **Monitor costs**: Track Gemini usage
3. **Gather feedback**: Iterate on settings
4. **Scale as needed**: Add more instances
5. **Optimize**: Fine-tune based on metrics

---

## Support

- **GitHub Issues**: https://github.com/yourusername/surya-ocr/issues
- **Documentation**: https://github.com/yourusername/surya-ocr
- **Docker Hub**: https://hub.docker.com/r/yourusername/surya-ocr

---

**You're ready for production!** 🚀

