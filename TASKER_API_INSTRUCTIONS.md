# OCR API Instructions for Tasker Integration

## API Base URL
```
http://YOUR_SERVER_IP:YOUR_PORT
```

Replace `YOUR_SERVER_IP` with your server's IP address and `YOUR_PORT` with the port you configured (default: 5000)

## Available Endpoints

### 1. Simple OCR (Text Only) - `/ocr_text`
**Best for:** Quick text extraction from images

**Method:** POST  
**Endpoint:** `http://YOUR_SERVER_IP:YOUR_PORT/ocr_text`

**Parameters (Query String):**
- `engine` - Choose OCR engine:
  - `auto` (default) - Automatically selects best engine
  - `tesseract` - Fast, best for clean printed text
  - `surya` - Better for handwriting and messy text
- `clean` - Text cleanup level:
  - `0` - No cleaning (raw OCR output)
  - `1` - Standard cleaning (default, recommended)
  - `2` - Aggressive cleaning (removes more noise)
- `handwriting` - Optimize for handwriting:
  - `0` - Standard mode (default)
  - `1` - Handwriting mode

**Body:** 
- Form-data with key `image` containing the image file

**Response:** Plain text (the extracted text)

**Example Tasker HTTP Request:**
```
URL: http://YOUR_SERVER_IP:YOUR_PORT/ocr_text?engine=auto&clean=1
Method: POST
Content Type: multipart/form-data
Body: image=%photo_path
```

---

### 2. OCR with Markdown Formatting - `/ocr_text_md`
**Best for:** Creating formatted documents from images

**Method:** POST  
**Endpoint:** `http://YOUR_SERVER_IP:YOUR_PORT/ocr_text_md`

**Parameters (Query String):**
- `engine` - Same as above (`auto`, `tesseract`, `surya`)
- `clean` - Same as above (0, 1, 2)
- `handwriting` - Same as above (0, 1)
- `md_engine` - Markdown formatting method:
  - `regex` - Fast, simple formatting
  - `ollama` - AI-powered formatting (slower, better quality)
- `md_model` - LLM model to use (optional, only if `md_engine=ollama`)
  - Default: `gemma3:12b-it-q8_0`

**Body:** 
- Form-data with key `image` containing the image file

**Response:** Plain text (formatted markdown)

**Example Tasker HTTP Request:**
```
URL: http://YOUR_SERVER_IP:YOUR_PORT/ocr_text_md?engine=auto&clean=1&md_engine=regex
Method: POST
Content Type: multipart/form-data
Body: image=%photo_path
```

---

### 3. Universal OCR (Automatic) - `/ocr_universal` ⭐ RECOMMENDED
**Best for:** Automatic handling of any document type

**Method:** POST  
**Endpoint:** `http://YOUR_SERVER_IP:YOUR_PORT/ocr_universal`

**Parameters (Query String):**
- `format` - Output format:
  - `text` - Plain text
  - `markdown` - Formatted markdown (default)
  - `json` - JSON with metadata
- `force_engine` - Force specific engine (optional):
  - `tesseract` - Clean print
  - `surya` - Handwriting
  - `vision` - AI vision models
- `clean` - Apply text cleaning:
  - `true` (default)
  - `false`
- `use_llm_formatter` - Use AI for markdown:
  - `true` (default) - Better formatting
  - `false` - Faster, basic formatting
- `use_intelligent_pipeline` - Multi-pass intelligent pipeline:
  - `false` (default) - Fast
  - `true` - Slower but highest quality (3-pass: analyze → extract → correct)

**Body:** 
- Form-data with key `image` containing the image file

**Response:** 
- If `format=text` or `format=markdown`: Plain text
- If `format=json`: JSON object with:
  ```json
  {
    "text": "extracted text",
    "confidence": 95.5,
    "engine": "tesseract",
    "metadata": {...}
  }
  ```

**Example Tasker HTTP Request (Simple):**
```
URL: http://YOUR_SERVER_IP:YOUR_PORT/ocr_universal?format=text&clean=true
Method: POST
Content Type: multipart/form-data
Body: image=%photo_path
```

**Example Tasker HTTP Request (High Quality):**
```
URL: http://YOUR_SERVER_IP:YOUR_PORT/ocr_universal?format=markdown&use_intelligent_pipeline=true
Method: POST
Content Type: multipart/form-data
Body: image=%photo_path
```

---

## Common Tasker Use Cases

### Use Case 1: Quick Screenshot OCR
**Goal:** Take screenshot, extract text, copy to clipboard

**Endpoint:** `/ocr_text`
**URL:** `http://YOUR_SERVER_IP:YOUR_PORT/ocr_text?engine=auto&clean=1`
**Method:** POST
**Image:** Take screenshot, pass file path

---

### Use Case 2: Photo Document to Note
**Goal:** Take photo of document, create formatted note

**Endpoint:** `/ocr_universal`
**URL:** `http://YOUR_SERVER_IP:YOUR_PORT/ocr_universal?format=markdown&clean=true`
**Method:** POST
**Image:** Camera photo file path
**Action:** Save response text to note app

---

### Use Case 3: Receipt Scanner
**Goal:** Scan receipt, extract structured data

**Endpoint:** `/ocr_universal`
**URL:** `http://YOUR_SERVER_IP:YOUR_PORT/ocr_universal?format=json&clean=true`
**Method:** POST
**Image:** Receipt photo
**Action:** Parse JSON response, extract relevant fields

---

### Use Case 4: Handwriting Recognition
**Goal:** Convert handwritten notes to text

**Endpoint:** `/ocr_text`
**URL:** `http://YOUR_SERVER_IP:YOUR_PORT/ocr_text?engine=surya&handwriting=1&clean=1`
**Method:** POST
**Image:** Photo of handwritten notes

---

## Tasker HTTP Request Configuration

### Basic Setup
1. **Action:** HTTP Request (or Net → HTTP Post)
2. **Method:** POST
3. **URL:** See endpoints above
4. **Headers:** 
   - `Content-Type: multipart/form-data`
5. **File/Data:** 
   - Field name: `image`
   - File path: `%photo_path` (or your variable)
6. **Output:** Store response in variable (e.g., `%ocr_result`)

### File Upload in Tasker
- Use multipart/form-data
- Field name MUST be `image`
- File path examples:
  - Screenshot: `/sdcard/Pictures/Screenshots/screenshot.png`
  - Camera: `/sdcard/DCIM/Camera/IMG_001.jpg`
  - Variable: `%last_photo`

### Error Handling
Check HTTP response code:
- `200` = Success, text in response body
- `422` = Invalid parameters
- `500` = Server error

---

## Quick Reference

| Need | Endpoint | Key Parameters |
|------|----------|----------------|
| Fast text extraction | `/ocr_text` | `engine=auto&clean=1` |
| Handwriting | `/ocr_text` | `engine=surya&handwriting=1` |
| Formatted document | `/ocr_universal` | `format=markdown` |
| Best quality | `/ocr_universal` | `use_intelligent_pipeline=true` |
| JSON with metadata | `/ocr_universal` | `format=json` |

---

## Tips for Best Results

1. **Image Quality:** Higher resolution = better results
2. **Lighting:** Good lighting improves accuracy
3. **Angle:** Straight-on photos work best
4. **Format:** PNG or JPEG are both fine
5. **Speed vs Quality:**
   - Fast: `/ocr_text` with `engine=tesseract`
   - Best: `/ocr_universal` with `use_intelligent_pipeline=true`

---

## Testing the API

### Simple Test (Browser)
Go to: `http://YOUR_SERVER_IP:YOUR_PORT/docs`
- Interactive API documentation
- Test endpoints directly in browser

### Health Check
URL: `http://YOUR_SERVER_IP:YOUR_PORT/health`
Response: `{"status": "healthy", "ok": true}`

---

## Example Tasker Profile

**Trigger:** Screenshot taken  
**Action 1:** Get latest screenshot path → `%screenshot`  
**Action 2:** HTTP POST to `http://YOUR_SERVER_IP:YOUR_PORT/ocr_text?clean=1`  
           - Body: `image=%screenshot`  
**Action 3:** Set clipboard to `%http_data`  
**Action 4:** Show toast: "Text copied to clipboard"

