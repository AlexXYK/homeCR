# 🐳 Portainer Setup - Simple & Clean

## What You're Deploying

**ONE container** with:
- ✅ API on port 5000
- ✅ Dashboard on port 5000/dashboard
- ✅ Everything unified

---

## Step-by-Step Setup

### 1. Open Portainer
- Go to `http://your-server:9000`
- Login

### 2. Add Stack
- Click **"Stacks"** (left sidebar)
- Click **"+ Add stack"** (top right)

### 3. Configure Stack
- **Stack name**: `surya-ocr`
- **Build method**: Select **"Web editor"**

### 4. Paste This YAML

Copy and paste this into the editor:

```yaml
version: '3.8'

services:
  ocr:
    image: alexxyk/surya-ocr:latest
    container_name: surya-ocr
    ports:
      - "5000:5000"
    environment:
      # Simple config - just 2 settings!
      - VISION_PROVIDER=ollama
      - VISION_MODEL=qwen2.5vl:7b
      
      # Your Ollama server
      - OLLAMA_HOST=http://192.168.0.153:11434
      
      # OCR behavior
      - USE_HYBRID_OCR=true
      - PERFECT_TABLES=false
      
      # API keys (add if using cloud providers)
      - GEMINI_API_KEY=
    
    volumes:
      - surya-data:/app/data
      - surya-logs:/app/logs
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
    
    networks:
      - surya-network

networks:
  surya-network:

volumes:
  surya-data:
  surya-logs:
```

### 5. Deploy
- Click **"Deploy the stack"** (bottom of page)
- Wait 30-60 seconds

### 6. Verify
- **Containers** tab → Look for green circle on `surya-ocr`
- Click container → **Logs** → Should see "Uvicorn running"

---

## Access Your System

### API Endpoints
```
http://YOUR_SERVER:5000/docs          # API documentation
http://YOUR_SERVER:5000/health        # Health check
http://YOUR_SERVER:5000/ocr_universal # OCR endpoint
```

### Dashboard
```
http://YOUR_SERVER:5000/dashboard        # Homepage
http://YOUR_SERVER:5000/dashboard/test   # Test interface
http://YOUR_SERVER:5000/dashboard/config # Settings
```

---

## Test It Works

```bash
# Health check
curl http://YOUR_SERVER:5000/health

# OCR test
curl -X POST http://YOUR_SERVER:5000/ocr_universal \
  -F "image=@document.jpg" \
  -F "format=markdown"
```

---

## Configuration Options

### Local Only (Free)
```yaml
- VISION_PROVIDER=ollama
- VISION_MODEL=qwen2.5vl:7b
- PERFECT_TABLES=false
```

### Perfect Tables ($0.005/doc)
```yaml
- VISION_PROVIDER=ollama
- VISION_MODEL=qwen2.5vl:7b
- PERFECT_TABLES=true
- GEMINI_API_KEY=your_actual_key_here
```

### Full Gemini
```yaml
- VISION_PROVIDER=gemini
- VISION_MODEL=gemini-2.0-flash-exp
- GEMINI_API_KEY=your_actual_key_here
```

---

## Updating Settings

**No rebuild needed!** Just:

1. Portainer → Stacks → `surya-ocr` → **Editor**
2. Change environment variables
3. Click **"Update the stack"**
4. Done!

---

## Troubleshooting

### Container won't start
- Check logs: Containers → surya-ocr → Logs
- Common issues:
  - Port 5000 already in use
  - Can't reach Ollama server
  - Missing API key (if using cloud)

### Can't access API
- Check container is running (green circle)
- Check port mapping: Containers → surya-ocr → Port 5000:5000
- Try from server: `curl http://localhost:5000/health`

### Ollama connection failed
- Verify Ollama is running: `curl http://192.168.0.153:11434/api/tags`
- Check network: Container can reach host network
- Update `OLLAMA_HOST` if different

---

## That's It!

Simple, clean, ONE container. 

**After deployment:**
- API: `http://your-server:5000`
- Dashboard: `http://your-server:5000/dashboard`
- Docs: `http://your-server:5000/docs`

🚀 **You're live!**

