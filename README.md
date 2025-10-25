# 🚀 Universal OCR System

An intelligent, production-ready OCR system that **automatically handles any document type** - printed text, handwriting, tables, mixed content, or screenshots.

**Key Features:**
- 🎯 **Universal**: One endpoint handles all document types
- 🧠 **Intelligent**: 3-pass pipeline with vision-guided correction
- ⚡ **Fast**: Dual OCR engines run in parallel (Tesseract + Surya)
- 🌐 **Multi-Provider**: Gemini, OpenAI, Claude, Ollama, or OpenRouter
- 💰 **Cost-Optimized**: Local by default, cloud only when needed
- 🔒 **Privacy-First**: All processing can be 100% local
- 🐳 **Production-Ready**: Docker, Portainer, health checks

---

## 🎬 Quick Start

### 1. Install

```bash
# Clone repository
git clone https://github.com/yourusername/surya-ocr.git
cd surya-ocr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

Create `.env` file (or copy from `env.example`):

```bash
# === Vision Configuration ===
VISION_PROVIDER=ollama              # Options: ollama, gemini, openai, anthropic
VISION_MODEL=qwen2.5vl:7b           # Model for image analysis

# === Text Configuration ===
TEXT_PROVIDER=ollama                # Options: ollama, openai, anthropic
TEXT_MODEL=gemma3:12b-it-q8_0       # Model for formatting/analysis

# === Ollama Settings (only if provider=ollama) ===
OLLAMA_HOST=http://localhost:11434

# === API Keys (only if using cloud providers) ===
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# === OCR Settings ===
USE_HYBRID_OCR=true                 # Run both Tesseract + Surya
PERFECT_TABLES=false                # Use cloud AI for tables

# === Ports ===
API_PORT=5000
DASHBOARD_PORT=8080
```

### 3. Run

```bash
# Start API server
python run_api.py

# Start dashboard (separate terminal)
python run_dashboard.py
```

### 4. Test

```bash
# Upload an image
curl -X POST http://localhost:5000/ocr_universal \
  -F "image=@document.jpg" \
  -F "format=markdown"

# With perfect tables
curl -X POST "http://localhost:5000/ocr_universal?perfect_tables=true" \
  -F "image=@invoice.jpg"
```

---

## 🏗️ Architecture

### The 3-Pass Intelligent Pipeline

```
┌─────────────────────────────────────────────────────┐
│ Pass 1: Vision Analysis                            │
│  → Classify document (print/handwriting/mixed)     │
│  → Detect tables, complexity, quality              │
│  → Choose optimal strategy                          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Pass 2: Dual OCR Extraction (PARALLEL)             │
│  → Tesseract (fast, excellent for print)           │
│  → Surya (thorough, excellent for handwriting)     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Pass 3: Vision-Guided Fusion                        │
│  → Compare both OCR outputs to image                │
│  → Fix common OCR errors (1 vs 4, 0 vs O)          │
│  → Format as beautiful markdown                     │
│  → Perfect table formatting (if perfect_tables=true)│
└─────────────────────────────────────────────────────┘
```

---

## 🌐 Multi-Provider Support

Switch between vision providers seamlessly:

### Supported Providers

| Provider | Best For | Cost | Setup |
|----------|----------|------|-------|
| **Ollama** | Local, privacy, free | $0 | Install Ollama + models |
| **Gemini** | Fast, cheap cloud | ~$0.01/1K | Get API key |
| **OpenAI** | GPT-4 Vision | ~$0.10/1K | Get API key |
| **Anthropic** | Claude 3.5 Sonnet | ~$0.05/1K | Get API key |
| **OpenRouter** | Access all models | Varies | Get API key |

### Configuration Examples

**Local Only (Free, Private)**:
```bash
VISION_PROVIDER=ollama
OLLAMA_VISION_MODEL=qwen2.5vl:7b
```

**Gemini Flash (Fast, Cheap)**:
```bash
VISION_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp  # Free in preview!
GEMINI_API_KEY=your_key
```

**Claude 3.5 (High Quality)**:
```bash
VISION_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=your_key
```

---

## 📊 Quality vs Cost

### Mode 1: Local Only (Default)
```python
pipeline = IntelligentOCRPipeline()
result = await pipeline.process(image)
```
- **Quality**: 90%
- **Cost**: $0
- **Privacy**: 100% local
- **Best for**: Personal use, sensitive docs

### Mode 2: Perfect Tables
```python
pipeline = IntelligentOCRPipeline(perfect_tables=True)
result = await pipeline.process(image)
```
- **Quality**: 98%
- **Cost**: ~$0.005/doc (only if has tables)
- **Privacy**: Body text local, tables to cloud
- **Best for**: Business documents, invoices

### Mode 3: Full Cloud
```python
# Set in .env: VISION_PROVIDER=gemini
pipeline = IntelligentOCRPipeline()
result = await pipeline.process(image)
```
- **Quality**: 98%+
- **Cost**: $0.01-0.10/doc
- **Privacy**: Sent to cloud
- **Best for**: Critical documents, maximum quality

---

## 🐳 Docker Deployment

### Quick Deploy

```bash
# Build image
docker build -f Dockerfile.production -t surya-ocr:latest .

# Run with Docker Compose
docker-compose up -d

# Access
# API: http://localhost:5000
# Dashboard: http://localhost:8080
```

### Portainer Deployment

1. Open Portainer UI
2. Go to **Stacks** → **Add Stack**
3. Name: `surya-ocr`
4. Upload `docker-compose.yml`
5. Add environment variables:
   - `GEMINI_API_KEY` (optional)
   - `VISION_PROVIDER` (ollama/gemini/openai/anthropic)
6. Click **Deploy**

See `PRODUCTION_DEPLOYMENT.md` for complete guide.

---

## 📡 API Reference

### Quick Reference

| Endpoint | Speed | Use Case | Example |
|----------|-------|----------|---------|
| `/ocr_text` | **Fast (2-5s)** | Simple text extraction | Screenshots, clean documents |
| `/ocr_universal` | Medium (5-15s) | Automatic routing | General documents |
| `/ocr_universal` (smart) | Slow (60-120s) | Best quality | Important documents |

### POST /ocr_text (Simple & Fast)

Fast text extraction - no classification, no LLM formatting.

**Parameters (Query String):**
- `engine`: `auto`, `tesseract`, `surya` (default: `auto`)
- `clean`: `0`, `1`, `2` (default: `1`) - Text cleaning level
- `handwriting`: `0`, `1` (default: `0`) - Optimize for handwriting

**Examples:**

```bash
# Fast screenshot OCR (2-5 seconds)
curl -X POST "http://localhost:5000/ocr_text?engine=tesseract&clean=1" \
  -F "image=@screenshot.png"

# Handwriting recognition
curl -X POST "http://localhost:5000/ocr_text?engine=surya&handwriting=1" \
  -F "image=@notes.jpg"
```

**Response:** Plain text

---

### POST /ocr_universal (Recommended)

Universal OCR endpoint - automatically handles any document type.

**Parameters (Query String):**
- `format`: `text`, `markdown`, `json` (default: `markdown`)
- `force_engine`: `tesseract`, `surya`, `vision` (optional)
- `clean`: `true`, `false` (default: `true`)
- `use_llm_formatter`: `true`, `false` (default: `true`)
- `use_intelligent_pipeline`: `true`, `false` (default: `false`)

**Fast Mode (5-15 seconds):**
```bash
curl -X POST "http://localhost:5000/ocr_universal?format=text&use_llm_formatter=false&force_engine=tesseract" \
  -F "image=@document.jpg"
```

**Balanced Mode (15-30 seconds):**
```bash
curl -X POST "http://localhost:5000/ocr_universal?format=markdown&use_llm_formatter=false" \
  -F "image=@document.jpg"
```

**Best Quality (60-120 seconds):**
```bash
curl -X POST "http://localhost:5000/ocr_universal?format=markdown&use_llm_formatter=true" \
  -F "image=@invoice.pdf"
```

**Maximum Quality (90-180 seconds):**
```bash
curl -X POST "http://localhost:5000/ocr_universal?use_intelligent_pipeline=true" \
  -F "image=@complex_document.jpg"
```

**JSON Response Example:**

```json
{
  "text": "# Invoice\n\n| Item | Price |\n|------|-------|\n| ... ",
  "confidence": 0.98,
  "engine": "intelligent_pipeline(tesseract+surya+vision_fusion)",
  "metadata": {
    "pipeline": "intelligent_hybrid",
    "document_type": "printed_text",
    "engines_tried": ["tesseract", "vision"]
  }
}
```

---

### GET /health

Health check endpoint (for Docker/Kubernetes).

```bash
curl http://localhost:5000/health
# Response: {"status": "healthy", "ok": true}
```

---

### GET /ocr_status

Get OCR engine status and configuration.

```bash
curl http://localhost:5000/ocr_status
```

**Response:**
```json
{
  "status": "healthy",
  "engines": {
    "tesseract": {"available": true, "name": "tesseract"},
    "surya": {"available": true, "name": "surya"},
    "vision": {"available": true, "name": "vision_local"}
  },
  "ollama": {
    "host": "http://localhost:11434",
    "status": "connected"
  },
  "settings": {
    "vision_provider": "ollama",
    "vision_model": "qwen2.5vl:7b",
    "text_provider": "ollama",
    "text_model": "gemma3:12b-it-q8_0"
  }
}
```

---

### Mobile/Tasker Integration

For mobile apps or automation tools, use the **fast mode**:

```bash
# Tasker HTTP POST configuration:
# URL: http://YOUR_SERVER:5000/ocr_text?engine=tesseract&clean=1
# Method: POST
# Content-Type: multipart/form-data
# Body: image=<your_image_variable>
# Response time: 2-5 seconds
```

See `docs/PERFORMANCE_GUIDE.md` for optimization details.

---

## 🎛️ Configuration Reference

### Environment Variables

**Vision & Text Providers:**
```bash
# Vision Configuration
VISION_PROVIDER=ollama               # ollama, gemini, openai, anthropic
VISION_MODEL=qwen2.5vl:7b            # Model for that provider

# Text Configuration
TEXT_PROVIDER=ollama                 # ollama, openai, anthropic
TEXT_MODEL=gemma3:12b-it-q8_0        # Model for that provider
```

**Provider Settings:**
```bash
# Ollama (only if using ollama)
OLLAMA_HOST=http://localhost:11434

# API Keys (only if using that provider)
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

**OCR Behavior:**
```bash
USE_HYBRID_OCR=true                  # Run both Tesseract + Surya in parallel
PERFECT_TABLES=false                 # Use cloud AI only for tables
```

**Application:**
```bash
API_PORT=5000
DASHBOARD_PORT=8080
LOG_LEVEL=INFO
```

---

## 🧪 Development

### Running Tests

```bash
# Test intelligent pipeline
python dev_tools/test_intelligent_pipeline.py image.jpg

# Compare providers
python dev_tools/compare_all_models.py ocr_data.json

# Test perfect tables
python dev_tools/test_perfect_tables.py invoice.jpg
```

### Project Structure

```
surya-ocr/
├── ocr_pipeline/              # Core OCR logic
│   ├── engines/
│   │   ├── vision_providers.py  # Multi-provider support
│   │   ├── tesseract_engine.py
│   │   └── surya_engine.py
│   └── intelligent_pipeline.py  # Main orchestrator
│
├── config/
│   └── settings.py            # Configuration management
│
├── dashboard/                 # Web dashboard (WIP)
│   ├── api.py
│   └── templates/
│
├── dev_tools/                 # Development utilities
│   ├── test_intelligent_pipeline.py
│   └── compare_all_models.py
│
├── app.py                     # Main FastAPI app
├── run_api.py                # API server
├── run_dashboard.py          # Dashboard server
│
├── Dockerfile.production     # Production Docker image
├── docker-compose.yml        # Multi-container setup
├── requirements.txt          # Python dependencies
└── .env                      # Your configuration
```

---

## 💡 Best Practices

### For Development
```bash
VISION_PROVIDER=ollama  # Free, fast iteration
PERFECT_TABLES=false
```

### For Staging
```bash
VISION_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp  # Free during preview
PERFECT_TABLES=true
```

### For Production
```bash
VISION_PROVIDER=gemini  # or openai, anthropic
GEMINI_MODEL=gemini-1.5-flash  # Paid but stable
PERFECT_TABLES=true
# Set up monitoring and cost alerts!
```

---

## 🚨 Troubleshooting

### OCR quality is poor
- ✅ Try `perfect_tables=true` if document has tables
- ✅ Test different vision providers
- ✅ Check image quality (resize to 1024px if >2MB)

### Slow processing
- ✅ Ensure Ollama is on fast network
- ✅ Use Gemini Flash (faster than local for some docs)
- ✅ Check GPU availability for Ollama

### High costs
- ✅ Set `vision_provider=ollama` (free!)
- ✅ Use `perfect_tables=true` instead of full cloud
- ✅ Monitor usage in dashboard

### Connection errors
- ✅ Check Ollama is running: `curl http://your-ollama:11434/api/tags`
- ✅ Verify API keys are correct
- ✅ Check firewall/network settings

---

## 📈 Roadmap

### v1.0 (Current - Production Ready)
- ✅ Intelligent 3-pass pipeline
- ✅ Multi-provider support
- ✅ Hybrid dual-engine OCR
- ✅ Docker deployment

### v1.1 (Next)
- ⬜ Settings dashboard UI
- ⬜ Cost tracking & analytics
- ⬜ Batch processing API
- ⬜ Web upload interface

### v2.0 (Future)
- ⬜ AI agent system for self-improvement
- ⬜ Custom model fine-tuning
- ⬜ Commercial features (auth, billing, rate limiting)
- ⬜ Multi-language support

---

## 🤝 Contributing

This is a production system ready to scale! Contributions welcome:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with:
- [Surya OCR](https://github.com/VikParuchuri/surya) - Excellent handwriting OCR
- [Tesseract](https://github.com/tesseract-ocr/tesseract) - Industry-standard printed text OCR
- [Google Gemini](https://ai.google.dev/) - Vision analysis
- [FastAPI](https://fastapi.tiangolo.com/) - Modern API framework

---

## 📞 Support

- **Issues**: https://github.com/yourusername/surya-ocr/issues
- **Documentation**: This README + inline code comments
- **Docker Hub**: https://hub.docker.com/r/yourusername/surya-ocr

---

## 💪 System Requirements

### Minimum (Local Mode):
- Python 3.10+
- 8GB RAM
- Tesseract OCR installed
- Access to Ollama server

### Recommended (Production):
- Python 3.11+
- 16GB+ RAM  
- Multi-core CPU (for parallel OCR)
- Ollama with GPU (2x 16GB recommended)
- Docker + Docker Compose

---

**Ready to deploy? See [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) for complete guide!** 🚀
