# 🤖 Model Selection Guide

## Understanding Model Capabilities

### ❌ **Gemma 3 CANNOT Process Images**

Despite being a powerful text model, **Gemma 3 (including the `gemma3:12b-it-qat` variant) is TEXT-ONLY**.

```bash
# Checking model families on Ollama:
gemma3:12b-it-qat → families: {gemma3}         # NO vision
llava:13b         → families: {llama, clip}    # HAS vision (CLIP)
```

The presence of **CLIP** in the families list indicates vision capability.

---

## Current Model Configuration

Our system uses **two different models** for different tasks:

### 🔍 **Vision Tasks** (Classification, Analysis, Correction)
- **Model**: `llava:13b`
- **Purpose**: 
  - Document type classification
  - Structure analysis (tables, handwriting, etc.)
  - Vision-guided OCR correction
  - Visual comparison for error detection
- **Why**: LLaVA has a CLIP vision encoder that processes images

### ✍️ **Text Tasks** (Formatting, Generation)
- **Model**: `gemma3:12b-it-qat`
- **Purpose**:
  - Markdown formatting
  - Text cleanup
  - Text-based analysis
  - Faster than vision models for text-only tasks
- **Why**: Quantization-aware training makes it fast and efficient

---

## Image Size Requirements

### 📏 **Recommended Sizes for LLaVA**

- **Maximum**: 1024x1024 pixels
- **Optimal**: 336x336 to 1024x1024 pixels
- **File size**: Under 20MB

### ⚠️ **What Happens with Large Images?**

Your vet invoice was **2060x2676 pixels** - this causes:
- ❌ Timeouts (vision model takes too long)
- ❌ High memory usage (fills GPU VRAM)
- ❌ Slow processing (minutes instead of seconds)

### ✅ **Solution: Automatic Resizing**

We've updated the pipeline to automatically resize images to **1024px max** while maintaining aspect ratio. This:
- ✓ Prevents timeouts
- ✓ Reduces memory usage
- ✓ Speeds up processing 3-5x
- ✓ Maintains sufficient detail for OCR

---

## Ollama Models You Have

Based on your Ollama server:

| Model | Size | Has Vision? | Best For |
|-------|------|-------------|----------|
| `llava:13b` | 7.46 GB | ✅ Yes | OCR, document analysis |
| `gemma3:12b-it-qat` | 8.32 GB | ❌ No | Text formatting, cleanup |
| `gemma3:27b` | 16.2 GB | ❌ No | Complex text tasks |
| `qwen3:30b` | 17.28 GB | ❓ Unknown | Check with `ollama show` |
| `llama3.3:70b` | 39.6 GB | ❌ No | Large-scale text tasks |
| `deepseek-r1:32b` | 18.49 GB | ❌ No | Reasoning tasks |

---

## Checking Model Capabilities

### Method 1: Via API
```powershell
Invoke-WebRequest -Uri http://192.168.0.153:11434/api/show `
    -Method POST `
    -Body '{"name":"MODEL_NAME"}' `
    -ContentType 'application/json' | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json | 
    Select-Object -ExpandProperty details
```

Look for `families: {llama, clip}` - if CLIP is present, it has vision.

### Method 2: Test with Image
```bash
# This will fail if model doesn't support vision:
curl http://192.168.0.153:11434/api/generate -d '{
  "model": "gemma3:12b-it-qat",
  "prompt": "Describe this image",
  "images": ["base64_encoded_image"]
}'
```

---

## Our Intelligent Pipeline

### 3-Pass Architecture

```
┌─────────────────────────────────────────────────────┐
│ Pass 1: Vision Analysis (llava:13b)                │
│ - Classify document type                           │
│ - Detect tables, handwriting, structure            │
│ - Assess quality and complexity                    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Pass 2: Targeted OCR (tesseract or surya)          │
│ - Use best engine based on analysis                │
│ - Extract raw text efficiently                     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Pass 3: Vision-Guided Correction (llava:13b)       │
│ - Compare image to OCR output                      │
│ - Fix OCR errors by looking at original            │
│ - Format tables and structure beautifully          │
└─────────────────────────────────────────────────────┘
```

---

## Performance Tips

### 🚀 **Speed Optimization**

1. **Use smaller images**: Resize before upload
2. **Pre-load models**: Run `ollama run llava:13b` first
3. **Monitor GPU memory**: Use `nvidia-smi` to check VRAM
4. **Parallel requests**: Set `OLLAMA_MAX_PARALLEL_REQUESTS=2` (you have 2 GPUs!)

### 💾 **Memory Management**

Your system has:
- 2x 16GB 4070s (32GB total VRAM)
- 100GB RAM

Model memory usage:
- `llava:13b`: ~8GB VRAM + ~4GB RAM
- `gemma3:12b-it-qat`: ~9GB VRAM
- Both together: ~17GB VRAM (fits comfortably!)

---

## Testing Your Setup

### 1. Test Vision Model
```bash
python test_vision_model.py
```

This creates a simple test image and verifies LLaVA can read it.

### 2. Test Intelligent Pipeline
```bash
python test_intelligent_pipeline.py path/to/image.jpg
```

This runs all 3 passes on your image.

### 3. Check Ollama Health
```bash
curl http://192.168.0.153:11434/api/tags
```

---

## Common Errors & Fixes

### Error: `httpx.ReadTimeout`
**Cause**: Image too large or model not loaded  
**Fix**: 
- Resize image to 1024x1024
- Pre-load model: `ollama run llava:13b`
- Increase timeout (already done in code)

### Error: `model 'X' not found`
**Cause**: Model not installed  
**Fix**: `ollama pull MODEL_NAME`

### Error: `out of memory`
**Cause**: Too many models loaded or image too large  
**Fix**: 
- Stop other Ollama processes
- Reduce image size
- Use smaller models

---

## Configuration

Edit `.env` to change models:

```bash
# Vision model (must support images!)
OLLAMA_VISION_MODEL=llava:13b

# Text model (for formatting)
OLLAMA_TEXT_MODEL=gemma3:12b-it-qat
OLLAMA_FORMATTER_MODEL=gemma3:12b-it-qat

# Performance tuning
OLLAMA_MAX_PARALLEL_REQUESTS=2  # Match your GPU count
```

---

## Questions?

- "Can I use Gemma 3 for vision?" → **No, use LLaVA**
- "Why is OCR timing out?" → **Image too large, now auto-resized to 1024px**
- "Which model is faster?" → **Gemma 3 for text, LLaVA slower but sees images**
- "Can I use a different vision model?" → **Yes! Try `llava:34b`, `bakllava`, or `minicpm-v`**

