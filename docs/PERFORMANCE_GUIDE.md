# Performance Guide - OCR API

## ⚡ Speed Optimization

### Performance Overview

| Endpoint | Speed | Quality | Use Case |
|----------|-------|---------|----------|
| `/ocr_text` | **Fast** (2-5s) | Good | Quick text extraction |
| `/ocr_universal` (fast mode) | Medium (5-15s) | Better | Automatic routing |
| `/ocr_universal` (default) | **Slow** (60-120s) | Best | High-quality formatted output |

---

## 🚀 Fast Mode Configuration

### For Tasker / Mobile Apps (Recommended)

Use these parameters for **5-10 second** responses:

```
/ocr_universal?format=text&use_llm_formatter=false&force_engine=tesseract
```

**Parameters:**
- `format=text` - Skip markdown formatting
- `use_llm_formatter=false` - **CRITICAL**: Skips LLM call (saves 30-60s)
- `force_engine=tesseract` - Skip classification (saves 20-40s)

---

## 🎯 Endpoint Comparison

### 1. Fastest: `/ocr_text` with Tesseract
```bash
curl -X POST "http://localhost:5000/ocr_text?engine=tesseract&clean=1" \
  -F "image=@screenshot.png"
```
- **Time:** 2-5 seconds
- **Best for:** Screenshots, printed documents
- **Skips:** Classification, multiple engines, LLM formatting

### 2. Balanced: `/ocr_universal` Fast Mode
```bash
curl -X POST "http://localhost:5000/ocr_universal?format=text&use_llm_formatter=false" \
  -F "image=@document.jpg"
```
- **Time:** 5-15 seconds
- **Best for:** General documents
- **Includes:** Smart routing, best engine selection
- **Skips:** LLM formatting

### 3. Best Quality: `/ocr_universal` Full Pipeline
```bash
curl -X POST "http://localhost:5000/ocr_universal?format=markdown&use_llm_formatter=true" \
  -F "image=@complex_doc.jpg"
```
- **Time:** 60-120 seconds
- **Best for:** Important documents
- **Includes:** Classification, multi-engine, LLM formatting

### 4. Maximum Quality: Intelligent Pipeline
```bash
curl -X POST "http://localhost:5000/ocr_universal?use_intelligent_pipeline=true" \
  -F "image=@invoice.pdf"
```
- **Time:** 90-180 seconds
- **Best for:** Critical documents, tables
- **Includes:** 3-pass analysis with vision correction

---

## 🔧 Performance Bottlenecks

### What Slows Down OCR?

1. **Vision Model Classification** (~20-40 seconds)
   - Location: `classifier.py`
   - Fix: Use `force_engine` parameter to skip
   - Example: `?force_engine=tesseract`

2. **Multiple OCR Engines** (~10-30 seconds each)
   - Router runs up to 2 engines in sequence
   - Fix: Force single engine
   - Example: `?force_engine=tesseract`

3. **LLM Markdown Formatting** (~30-60 seconds) ⚠️ **BIGGEST BOTTLENECK**
   - Location: `postprocessor.py`
   - Fix: Set `use_llm_formatter=false`
   - Alternative: Use `format=text` instead of `markdown`

4. **Large Images** (~5-15 seconds extra)
   - Processing 4K+ images is slow
   - Fix: Resize images to 2000px max dimension before sending

---

## 💡 Optimization Strategies

### For Mobile Apps (Tasker, etc.)

**Priority: Speed**

```
Endpoint: /ocr_text
Parameters: engine=tesseract&clean=1
Expected: 2-5 seconds
```

### For Web Dashboard

**Priority: Balance**

```
Endpoint: /ocr_universal
Parameters: format=text&use_llm_formatter=false
Expected: 5-15 seconds
```

### For Document Archive

**Priority: Quality**

```
Endpoint: /ocr_universal
Parameters: format=markdown&use_llm_formatter=true
Expected: 60-120 seconds
```

---

## 🏃 Speed Tips

### 1. Skip Classification
```
?force_engine=tesseract
```
Saves 20-40 seconds

### 2. Disable LLM Formatting
```
?use_llm_formatter=false
```
Saves 30-60 seconds

### 3. Use Text Format
```
?format=text
```
Skips all formatting (fastest)

### 4. Resize Images Client-Side
```python
# Example: Resize before sending
from PIL import Image
img = Image.open("large.jpg")
img.thumbnail((2000, 2000))
img.save("resized.jpg")
```

### 5. Use Tesseract for Print
```
?engine=tesseract  # For clean printed text
```

### 6. Use Surya for Handwriting
```
?engine=surya  # For handwritten text
```

---

## 📊 Performance Metrics

### Typical Response Times (by configuration)

| Configuration | Classification | OCR | Formatting | Total |
|---------------|----------------|-----|------------|-------|
| Fast Mode | 0s (skipped) | 3s | 0s (skipped) | **3-5s** |
| Balanced | 25s | 10s | 0s (skipped) | **35s** |
| Default | 25s | 10s | 45s | **80s** |
| High Quality | 30s | 60s | 50s | **140s** |

*Times measured on system with:*
- Ollama: qwen2.5vl:7b (vision)
- Ollama: gemma3:12b (formatter)
- Hardware: Mid-range CPU/GPU

---

## 🎛️ Model Selection

### Switching Ollama Models

Edit `portainer-stack.yml` or set environment variables:

```yaml
environment:
  - OLLAMA_VISION_MODEL=qwen2.5vl:7b     # For image analysis/classification
  - OLLAMA_TEXT_MODEL=gemma3:12b         # For all text tasks (formatting, analysis)
```

**Faster models:**
- `llava:7b` - Faster vision (less accurate)
- `gemma2:7b` - Faster formatting
- `phi3:mini` - Minimal model (fast but lower quality)

**Better models:**
- `qwen2.5vl:14b` - Better vision (slower)
- `gemma3:27b` - Better formatting (much slower)

---

## 🚨 Common Issues

### "Taking over 2 minutes"

**Cause:** You're using default parameters with `use_llm_formatter=true`

**Fix:** Add `?use_llm_formatter=false`

### "Ollama timeout"

**Cause:** Vision model is too large or slow

**Fix:** 
1. Use smaller model: `OLLAMA_VISION_MODEL=llava:7b`
2. Increase timeout in `postprocessor.py` line 79

### "Classification errors"

**Cause:** Vision model struggling

**Fix:** Use `?force_engine=tesseract` to skip classification

---

## 📝 Recommended Configurations

### Development/Testing
```bash
/ocr_text?engine=tesseract&clean=1
```

### Production Mobile App
```bash
/ocr_universal?format=text&use_llm_formatter=false&force_engine=tesseract
```

### Production Document Processing
```bash
/ocr_universal?format=markdown&use_llm_formatter=false
```

### Archive Quality
```bash
/ocr_universal?format=markdown&use_llm_formatter=true&use_intelligent_pipeline=true
```

---

## 🔍 Monitoring Performance

Check API status:
```bash
GET /ocr_status
```

Returns:
```json
{
  "status": "healthy",
  "engines": {
    "tesseract": {"available": true},
    "surya": {"available": true},
    "vision": {"available": true}
  },
  "ollama": {
    "status": "connected",
    "host": "http://localhost:11434"
  }
}
```

