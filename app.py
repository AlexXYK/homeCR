import io, os, re, threading
from functools import lru_cache
from typing import Tuple, Optional
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps
import numpy as np
import pytesseract
import cv2
import httpx

# New OCR Pipeline
from ocr_pipeline.router import OCRRouter
from ocr_pipeline.postprocessor import OCRPostProcessor
from config import settings

# --- Surya (handwriting/messy) ---
from surya.detection import DetectionPredictor
from surya.recognition import RecognitionPredictor
from surya.foundation import FoundationPredictor

app = FastAPI(title="Universal OCR API", version="2.0.0")

# Add CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize new OCR components
ocr_router = None
ocr_postprocessor = None

def get_ocr_router():
    """Lazy initialization of OCR router."""
    global ocr_router
    if ocr_router is None:
        ocr_router = OCRRouter()
    return ocr_router

def get_postprocessor():
    """Lazy initialization of post-processor."""
    global ocr_postprocessor
    if ocr_postprocessor is None:
        ocr_postprocessor = OCRPostProcessor()
    return ocr_postprocessor

# ---------------- Surya lazy-singletons ----------------
@lru_cache(maxsize=1)
def get_foundation():
    return FoundationPredictor()

@lru_cache(maxsize=1)
def get_det():
    return DetectionPredictor()

@lru_cache(maxsize=1)
def get_rec():
    return RecognitionPredictor(get_foundation())

def _extract_surya(preds_obj) -> Tuple[str, list]:
    # preds_obj has .text_lines with .text for each line
    if hasattr(preds_obj, "text_lines"):
      lines = []
      for ln in getattr(preds_obj, "text_lines", []):
        text = getattr(ln, "text", "") or ""
        lines.append(text)
      return "\n".join([t for t in lines if t]), []
    return str(preds_obj), []

def run_surya_bytes(image_bytes: bytes) -> Tuple[str, list]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    rec = get_rec(); det = get_det()
    preds = rec([img], det_predictor=det)[0]
    return _extract_surya(preds)

# ---------------- OpenCV preprocess for Tesseract (print) ----------------
def _prep_cv(img: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(img)
    w, h = img.size
    long_side = max(w, h)
    if long_side > 2200:
        scale = 2200 / long_side
        img = img.resize((int(w*scale), int(h*scale)))
    arr = np.array(img)
    gray = arr if arr.ndim == 2 else cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    gray = cv2.bilateralFilter(gray, d=7, sigmaColor=40, sigmaSpace=40)
    std = float(gray.std())
    if std >= 32.0:
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 35, 15)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((2,2), np.uint8))
    return Image.fromarray(th)

def _tess_text(img: Image.Image, psm: str) -> str:
    cfg = f"--oem 1 --psm {psm} -l eng --dpi 300 -c preserve_interword_spaces=1"
    return pytesseract.image_to_string(img, config=cfg)

def _tess_conf(img: Image.Image, psm: str) -> float:
    cfg = f"--oem 1 --psm {psm} -l eng --dpi 300"
    data = pytesseract.image_to_data(img, config=cfg, output_type=pytesseract.Output.DICT)
    confs = [int(c) for c in data.get("conf", []) if c not in ("-1", -1)]
    return float(sum(confs) / len(confs)) if confs else 0.0

def run_tesseract_bytes(image_bytes: bytes) -> Tuple[str, float]:
    pil = Image.open(io.BytesIO(image_bytes))
    proc = _prep_cv(pil)
    best_text, best_conf = "", 0.0
    for psm in ("6", "4", "11"):
        txt = _tess_text(proc, psm=psm).strip()
        conf = _tess_conf(proc, psm=psm)
        if conf > best_conf and txt:
            best_text, best_conf = txt, conf
    return best_text, best_conf

# ---------------- Cleanup helpers ----------------
MULTI_PUNCT   = re.compile(r'([.,;:!?])\1{1,}')
MULTI_SPACE   = re.compile(r'[ \t]{2,}')
SPACE_BEFORE  = re.compile(r'\s+([.,;:!?])')
WHITELIST_RE  = re.compile(r'^\s*(x\.?|note)\s*$', re.I)

def _normalize_symbols(line: str) -> str:
    return (line.replace('·', '.').replace('•', '.')
                .replace('×', 'x').replace('–', '-').replace('—', '-'))

def _has_word_3plus(line: str) -> bool:
    return any(len(tok) >= 3 for tok in re.findall(r"[A-Za-z]+", line))

def _ratio_non_alnum(line: str) -> float:
    if not line: return 1.0
    total = len(line)
    non_alnum = sum(0 if (ch.isalnum() or ch.isspace()) else 1 for ch in line)
    return non_alnum / max(total, 1)

def _is_mostly_punct_or_symbols(line: str, thresh: float = 0.55) -> bool:
    if not line.strip(): return True
    return _ratio_non_alnum(line) >= thresh

def _is_numbery(line: str, thresh_digits: float = 0.6) -> bool:
    s = line.strip()
    if not s: return True
    if WHITELIST_RE.match(s): return False
    digits = sum(ch.isdigit() for ch in s)
    return (digits / len(s)) >= thresh_digits

def _few_letters(line: str, min_letters: int = 3) -> bool:
    s = line.strip()
    if WHITELIST_RE.match(s): return False
    letters = sum(ch.isalpha() for ch in line)
    return letters < min_letters

def clean_text(raw: str, aggressive: bool = False, handwriting: bool = False) -> str:
    lines = raw.splitlines()
    out = []
    for ln in lines:
        ln = _normalize_symbols(ln)
        s = ln.strip()
        if WHITELIST_RE.match(s):  # keep "x" / "note"
            out.append(s); continue
        if handwriting:
            # gentler filtering for short/loose lines
            if _is_mostly_punct_or_symbols(ln, 0.65):
                continue
        else:
            if aggressive:
                if not _has_word_3plus(s): continue
            else:
                if _is_mostly_punct_or_symbols(ln) or _is_numbery(ln) or _few_letters(ln):
                    continue
        ln = MULTI_PUNCT.sub(r'\1', ln)
        ln = SPACE_BEFORE.sub(r'\1', ln)
        ln = MULTI_SPACE.sub(' ', ln).strip()
        if ln: out.append(ln)
    text = "\n".join(out)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

def looks_bad(t: str, avg_conf: float, min_words: int, min_clean_ratio: float, min_avg_conf: float) -> bool:
    if not t or not t.strip(): return True
    total = len(t)
    clean = sum(ch.isalnum() or ch.isspace() or ch in ".,;:!?()[]{}-_/\\'\"" for ch in t)
    ratio = clean / max(total, 1)
    words = len(t.split())
    return (words < min_words) or (ratio < min_clean_ratio) or (avg_conf < min_avg_conf)

# ---------------- Markdown formatting ----------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MD_MODEL = os.getenv("DEFAULT_MD_MODEL", "gemma3:12b-it-q8_0")
MD_SYSTEM_PROMPT = os.getenv("MD_SYSTEM_PROMPT",
    "You convert raw OCR text into clean, faithful Markdown. Preserve meaning. "
    "Prefer accuracy over creativity. Use lists and tables only when obvious. Output Markdown only."
)

def _build_md_prompt(text: str) -> str:
    return (
        f"{MD_SYSTEM_PROMPT}\n\n"
        "OCR text:\n"
        "```\n" + text + "\n```"
    )

async def md_regex(text: str) -> str:
    import re
    t = re.sub(r'[ \t]+', ' ', text)
    t = re.sub(r'(\. ?){3,}', '…', t)
    t = re.sub(r'\n{2,}', '\n\n', t)
    t = re.sub(r'^[*-]\s+', '- ', t, flags=re.MULTILINE)
    return t.strip()

async def md_ollama(text: str, model: str) -> str:
    payload = {
        "model": model,
        "prompt": _build_md_prompt(text),
        "stream": False,
        "options": {
            "temperature": 0.1,
            "repeat_penalty": 1.05,
            "num_ctx": 4096
        }
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
    return (data.get("response") or "").strip()

@app.get("/healthz")
def healthz():
    return {"ok": True, "ollama": OLLAMA_HOST, "default_md_model": DEFAULT_MD_MODEL}

@app.post("/ocr_text")
async def ocr_text(
    image: UploadFile = File(...),
    engine: str = Query("auto", enum=["auto","tesseract","surya"]),
    min_words: int = Query(10, ge=0),
    min_clean_ratio: float = Query(0.65, ge=0.0, le=1.0),
    min_avg_conf: float = Query(60.0, ge=0.0, le=100.0),
    clean: int = Query(1, ge=0, le=2),
    handwriting: int = Query(0, ge=0, le=1)
):
    data = await image.read()
    if engine == "surya" or handwriting == 1:
        txt, _ = run_surya_bytes(data)
        return PlainTextResponse(clean_text(txt, aggressive=(clean==2), handwriting=bool(handwriting)) if clean else txt)
    if engine == "tesseract":
        txt, _conf = run_tesseract_bytes(data)
        return PlainTextResponse(clean_text(txt, aggressive=(clean==2), handwriting=False) if clean else txt)
    ttxt, conf = run_tesseract_bytes(data)
    if looks_bad(ttxt, conf, min_words, min_clean_ratio, min_avg_conf) or handwriting == 1:
        txt, _ = run_surya_bytes(data)
    else:
        txt = ttxt
    return PlainTextResponse(clean_text(txt, aggressive=(clean==2), handwriting=bool(handwriting)) if clean else txt)

@app.post("/ocr_text_md")
async def ocr_text_md(
    image: UploadFile = File(...),
    engine: str = Query("auto", enum=["auto","tesseract","surya"]),
    min_words: int = Query(10, ge=0),
    min_clean_ratio: float = Query(0.65, ge=0.0, le=1.0),
    min_avg_conf: float = Query(60.0, ge=0.0, le=100.0),
    clean: int = Query(1, ge=0, le=2),
    handwriting: int = Query(0, ge=0, le=1),
    md_engine: str = Query("ollama", enum=["regex","ollama"]),
    md_model: str = Query(None)
):
    data = await image.read()
    if engine == "surya" or handwriting == 1:
        txt, _ = run_surya_bytes(data)
    elif engine == "tesseract":
        txt, _ = run_tesseract_bytes(data)
    else:
        ttxt, conf = run_tesseract_bytes(data)
        if looks_bad(ttxt, conf, min_words, min_clean_ratio, min_avg_conf) or handwriting == 1:
            txt, _ = run_surya_bytes(data)
        else:
            txt = ttxt
    txt = clean_text(txt, aggressive=(clean==2), handwriting=bool(handwriting)) if clean else txt

    if md_engine == "regex":
        md = await md_regex(txt)
    else:
        model = md_model or DEFAULT_MD_MODEL
        md = await md_ollama(txt, model)
    return PlainTextResponse(md)

# ============================================================================
# NEW UNIVERSAL OCR ENDPOINT - Automatic document handling
# ============================================================================

@app.post("/ocr_universal")
async def ocr_universal(
    image: UploadFile = File(...),
    format: str = Query("markdown", enum=["text", "markdown", "json"]),
    force_engine: Optional[str] = Query(None, enum=["tesseract", "surya", "vision"]),
    clean: bool = Query(True, description="Apply text cleaning"),
    use_llm_formatter: bool = Query(True, description="Use LLM for markdown formatting"),
    use_intelligent_pipeline: bool = Query(False, description="Use multi-pass intelligent pipeline (slower but better)")
):
    """
    Universal OCR endpoint - automatically handles any document type.
    
    This endpoint:
    1. Classifies the document type (printed, handwriting, mixed, table, etc.)
    2. Routes to the best OCR engine(s)
    3. Post-processes and formats the output beautifully
    
    No configuration needed - just upload your image!
    
    Args:
        image: Image file to process
        format: Output format (text, markdown, json)
        force_engine: Force use of specific engine (optional)
        clean: Apply text cleaning
        use_llm_formatter: Use LLM for markdown formatting (slower but better)
        use_intelligent_pipeline: Use 3-pass intelligent pipeline (analyzes, extracts, corrects with vision)
    
    Returns:
        Formatted OCR result
    """
    try:
        # Use intelligent pipeline if requested
        if use_intelligent_pipeline:
            from ocr_pipeline.intelligent_pipeline import IntelligentOCRPipeline
            
            image_bytes = await image.read()
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            pipeline = IntelligentOCRPipeline()
            result = await pipeline.process(pil_image)
            
            if format == "json":
                return JSONResponse({
                    "text": result.text,
                    "confidence": result.confidence,
                    "engine": result.engine_name,
                    "metadata": result.metadata
                })
            elif format == "markdown":
                return PlainTextResponse(result.text)
            else:  # text
                return PlainTextResponse(result.text)
        
        # Original pipeline

        # Read image
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes))
        
        # Get router and processor
        router = get_ocr_router()
        processor = get_postprocessor()
        
        # Route and process
        result = await router.route_and_process(pil_image, force_engine=force_engine)
        
        # Clean text if requested
        text = result.text
        if clean:
            text = processor.clean_text(text, aggressive=False)
        
        # Format based on request
        if format == "json":
            return JSONResponse({
                "text": text,
                "confidence": result.confidence,
                "engine": result.engine_name,
                "metadata": result.metadata
            })
        elif format == "markdown":
            # Format as markdown
            markdown = await processor.format_as_markdown(text, use_llm=use_llm_formatter)
            return PlainTextResponse(markdown)
        else:  # text
            return PlainTextResponse(text)
    
    except Exception as e:
        return JSONResponse(
            {"error": str(e), "details": "OCR processing failed"},
            status_code=500
        )

@app.get("/ocr_status")
async def ocr_status():
    """Get status of OCR engines and system health."""
    try:
        router = get_ocr_router()
        
        # Check engine availability
        engines_status = {}
        for name, engine in router.available_engines.items():
            engines_status[name] = {
                "available": engine.is_available(),
                "name": engine.name
            }
        
        # Check Ollama connection
        ollama_status = "unknown"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.ollama_host}/api/tags")
                if response.status_code == 200:
                    ollama_status = "connected"
                    models = response.json().get("models", [])
                    engines_status["ollama_models"] = [m.get("name") for m in models]
        except Exception:
            ollama_status = "disconnected"
        
        return JSONResponse({
            "status": "healthy",
            "engines": engines_status,
            "ollama": {
                "host": settings.ollama_host,
                "status": ollama_status
            },
            "settings": {
                "vision_model": settings.ollama_vision_model,
                "text_model": settings.ollama_text_model,
                "formatter_model": settings.ollama_formatter_model
            }
        })
    except Exception as e:
        return JSONResponse(
            {"status": "error", "error": str(e)},
            status_code=500
        )

