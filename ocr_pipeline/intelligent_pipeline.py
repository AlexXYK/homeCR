"""
Intelligent Multi-Pass OCR Pipeline

Pass 1: Vision Analysis - Understand the document (Gemini 2.5 Pro)
Pass 2: Dual OCR - Run BOTH Tesseract AND Surya in parallel
Pass 3: Vision-Guided Fusion - Gemini picks best from each (Gemini 2.5 Pro)
"""
import io
import base64
import httpx
import asyncio
from typing import Dict, Any, Tuple, Optional
from PIL import Image
from config import settings
from .engines.base_engine import OCRResult
from .engines.tesseract_engine import TesseractEngine
from .engines.surya_engine import SuryaEngine
from .engines.vision_providers import get_vision_provider


class DocumentAnalysis:
    """Results from vision analysis of document."""
    
    def __init__(self, data: Dict[str, Any]):
        self.document_type = data.get('document_type', 'unknown')  # print, handwriting, mixed
        self.complexity = data.get('complexity', 'medium')  # low, medium, high
        self.has_tables = data.get('has_tables', False)
        self.has_handwriting = data.get('has_handwriting', False)
        self.has_signatures = data.get('has_signatures', False)
        self.language = data.get('language', 'english')
        self.structure = data.get('structure', {})  # headers, sections, etc.
        self.quality_issues = data.get('quality_issues', [])
        self.recommended_engine = data.get('recommended_engine', 'auto')
        self.raw_analysis = data.get('raw_analysis', '')


class IntelligentOCRPipeline:
    """
    Intelligent multi-pass OCR pipeline that uses vision understanding
    to guide extraction, correction, and formatting.
    """
    
    def __init__(
        self, 
        vision_provider: str = None, 
        vision_model: str = None,
        use_hybrid_ocr: bool = None,
        perfect_tables: bool = None
    ):
        """
        Initialize the intelligent pipeline.
        
        Args:
            vision_provider: Vision provider (ollama/gemini/openai/anthropic/openrouter). None = use settings.
            vision_model: Model to use for vision provider. None = use settings default for that provider.
            use_hybrid_ocr: Run both Tesseract + Surya in parallel. None = use settings default.
            perfect_tables: Use vision provider only for perfect table formatting. None = use settings default.
        """
        # Use settings defaults if not specified
        self.vision_provider = vision_provider or settings.vision_provider
        self.vision_model = vision_model
        self.use_hybrid_ocr = use_hybrid_ocr if use_hybrid_ocr is not None else settings.use_hybrid_ocr
        self.perfect_tables = perfect_tables if perfect_tables is not None else settings.perfect_tables
        
        # Initialize vision provider
        self.vision = get_vision_provider(self.vision_provider, self.vision_model)
        
        if not self.vision.is_available():
            print(f"⚠️  {self.vision_provider} not available, falling back to Ollama")
            self.vision_provider = "ollama"
            self.vision = get_vision_provider("ollama")
        
        # Initialize OCR engines
        self.tesseract = TesseractEngine()
        self.surya = SuryaEngine()
    
    async def pass1_analyze_document(self, image: Image.Image) -> DocumentAnalysis:
        """
        Pass 1: Analyze document with vision model (Gemini 2.5 Pro or Ollama fallback).
        
        Understand structure, content type, and quality before OCR.
        """
        print(f"📊 Pass 1: Analyzing document with {self.vision_provider.upper()} ({self.vision.model_name})...")
        
        prompt = """Analyze this document image carefully. You must categorize the MAJORITY of the text.

CRITICAL: Count the text carefully!
- If 80%+ is PRINTED/TYPED text → TYPE: print
- If 80%+ is HANDWRITTEN text → TYPE: handwriting  
- Only use MIXED if truly 30-70% of each

Questions to answer:

1. **Document Type - WHAT IS THE MAJORITY?**
   - Count: What percentage is printed vs handwritten?
   - A few handwritten notes on a printed form = PRINT, not mixed!
   
2. **Complexity**: Evaluate layout complexity
   - LOW: Simple single-column text
   - MEDIUM: Multi-column or some structure
   - HIGH: Complex tables, mixed layouts, dense formatting
   
3. **Tables**: Are there structured tables with rows/columns?

4. **Handwriting Location**: Where is any handwriting? (signatures, notes, margins)

5. **Quality**: Is the printed text clear and readable?

6. **Recommended Engine**:
   - TESSERACT: Clean printed text, forms, invoices, even with a few handwritten notes
   - SURYA: Messy handwriting, hand-filled forms, or poor quality scans
   
FORMAT YOUR RESPONSE:
TYPE: [print/handwriting/mixed]
PRINT_PERCENTAGE: [0-100%]
HANDWRITING_PERCENTAGE: [0-100%]
COMPLEXITY: [low/medium/high]
TABLES: [yes/no - describe if yes]
HANDWRITING: [yes/no - where located]
QUALITY_ISSUES: [list any]
RECOMMENDED_ENGINE: [tesseract/surya]

Then explain your reasoning in 2-3 sentences."""
        
        # Use configured vision provider
        response = await self.vision.analyze(image, prompt)
        
        # Parse response
        analysis_data = self._parse_analysis(response)
        analysis_data['raw_analysis'] = response
        
        analysis = DocumentAnalysis(analysis_data)
        
        print(f"  ✓ Type: {analysis.document_type}")
        print(f"  ✓ Complexity: {analysis.complexity}")
        print(f"  ✓ Has tables: {analysis.has_tables}")
        print(f"  ✓ Has handwriting: {analysis.has_handwriting}")
        print(f"  ✓ Recommended: {analysis.recommended_engine}")
        
        return analysis
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse vision model's analysis response."""
        data = {}
        
        response_lower = response.lower()
        
        # Document type
        if 'type:' in response_lower:
            if 'handwrit' in response_lower.split('type:')[1].split('\n')[0]:
                data['document_type'] = 'handwriting'
            elif 'mixed' in response_lower.split('type:')[1].split('\n')[0]:
                data['document_type'] = 'mixed'
            else:
                data['document_type'] = 'print'
        
        # Complexity
        if 'complexity:' in response_lower:
            comp_line = response_lower.split('complexity:')[1].split('\n')[0]
            if 'high' in comp_line:
                data['complexity'] = 'high'
            elif 'low' in comp_line:
                data['complexity'] = 'low'
            else:
                data['complexity'] = 'medium'
        
        # Tables
        if 'tables:' in response_lower:
            tables_line = response_lower.split('tables:')[1].split('\n')[0]
            data['has_tables'] = 'yes' in tables_line
        
        # Handwriting
        if 'handwriting:' in response_lower:
            hw_line = response_lower.split('handwriting:')[1].split('\n')[0]
            data['has_handwriting'] = 'yes' in hw_line
        
        # Signatures
        if 'signatures:' in response_lower:
            sig_line = response_lower.split('signatures:')[1].split('\n')[0]
            data['has_signatures'] = 'yes' in sig_line
        
        # Language
        if 'language:' in response_lower:
            lang_line = response_lower.split('language:')[1].split('\n')[0].strip()
            data['language'] = lang_line
        
        # Recommended engine
        if 'recommended_engine:' in response_lower:
            rec_line = response_lower.split('recommended_engine:')[1].split('\n')[0]
            if 'tesseract' in rec_line:
                data['recommended_engine'] = 'tesseract'
            elif 'surya' in rec_line:
                data['recommended_engine'] = 'surya'
            elif 'vision' in rec_line:
                data['recommended_engine'] = 'vision'
        
        return data
    
    async def pass2_extract_text(
        self,
        image: Image.Image,
        analysis: DocumentAnalysis
    ) -> Tuple[str, str]:
        """
        Pass 2: Extract text using best engine based on analysis.
        
        Returns: (text, engine_used)
        """
        print(f"🔤 Pass 2: Extracting text with recommended engine...")
        
        engine_name = analysis.recommended_engine
        
        # Smart engine selection based on document analysis
        # Priority: Printed text → Tesseract (fast)
        #          Handwriting/messy → Surya (accurate for messy docs)
        
        if analysis.document_type == 'print':
            engine_name = 'tesseract'
            reason = "clean printed text"
        elif analysis.document_type == 'handwriting':
            engine_name = 'surya'
            reason = "handwritten text"
        elif analysis.document_type == 'mixed':
            # For mixed, use Tesseract if mostly print (>70%)
            # Use Surya if mostly handwriting
            engine_name = 'surya'  # Default to Surya for mixed
            reason = "mixed content"
        else:
            # Fallback
            engine_name = analysis.recommended_engine or 'surya'
            reason = "vision model recommendation"
        
        # Execute OCR
        if engine_name == 'tesseract' and self.tesseract.is_available():
            print(f"  ✓ Using Tesseract ({reason})")
            result = await self.tesseract.process(image)
            return result.text, 'tesseract'
        elif engine_name == 'tesseract' and not self.tesseract.is_available():
            # Tesseract wanted but not available
            print(f"  ⚠️  Tesseract recommended but not installed!")
            print(f"  ℹ️  Install from: https://github.com/UB-Mannheim/tesseract/wiki")
            print(f"  ⏳ Falling back to Surya (slower but works)")
            result = await self.surya.process(image)
            return result.text, 'surya_fallback'
        else:
            # Use Surya
            print(f"  ✓ Using Surya ({reason})")
            result = await self.surya.process(image)
            return result.text, 'surya'
    
    async def pass2_dual_extract(
        self,
        image: Image.Image,
        analysis: DocumentAnalysis
    ) -> Tuple[Optional[str], str, str]:
        """
        Pass 2 (Hybrid): Run BOTH Tesseract and Surya in parallel.
        
        This maximizes accuracy by giving Gemini both outputs to compare.
        - Tesseract: Fast, excellent for printed text
        - Surya: Slower, excellent for handwriting and messy docs
        
        Returns: (tesseract_text, surya_text, engines_used)
        """
        print(f"🔤 Pass 2: Running BOTH engines in parallel for maximum accuracy...")
        
        # Run both engines in parallel
        tasks = []
        engines_used = []
        
        # Add Tesseract task if available
        if self.tesseract.is_available():
            print(f"  ⚡ Starting Tesseract (fast, for printed text)...")
            tasks.append(self.tesseract.process(image))
            engines_used.append('tesseract')
        else:
            print(f"  ⚠️  Tesseract not available, skipping")
            tasks.append(None)
        
        # Always add Surya task
        print(f"  🐢 Starting Surya (thorough, for handwriting)...")
        tasks.append(self.surya.process(image))
        engines_used.append('surya')
        
        # Run in parallel and wait for both
        print(f"  ⏳ Running both engines simultaneously...")
        results = await asyncio.gather(*[t for t in tasks if t is not None], return_exceptions=True)
        
        # Extract results
        tesseract_text = None
        surya_text = None
        
        result_idx = 0
        if self.tesseract.is_available():
            if isinstance(results[result_idx], Exception):
                print(f"  ⚠️  Tesseract failed: {results[result_idx]}")
            else:
                tesseract_text = results[result_idx].text
                print(f"  ✓ Tesseract complete ({len(tesseract_text)} chars)")
            result_idx += 1
        
        if isinstance(results[result_idx], Exception):
            print(f"  ⚠️  Surya failed: {results[result_idx]}")
        else:
            surya_text = results[result_idx].text
            print(f"  ✓ Surya complete ({len(surya_text)} chars)")
        
        engines_str = "+".join(engines_used)
        return tesseract_text, surya_text, engines_str
    
    async def pass3_vision_guided_fusion(
        self,
        image: Image.Image,
        tesseract_text: Optional[str],
        surya_text: str,
        analysis: DocumentAnalysis,
        engines_used: str
    ) -> str:
        """
        Pass 3 (Hybrid): Use Gemini to intelligently fuse BOTH OCR outputs.
        
        Gemini sees:
        1. The original image
        2. Tesseract output (excellent for printed text)
        3. Surya output (excellent for handwriting)
        
        It then creates the best possible output by:
        - Using Tesseract for printed sections
        - Using Surya for handwritten sections
        - Correcting errors in both by comparing to image
        """
        print(f"✨ Pass 3: Gemini fusion of both OCR outputs...")
        
        # Build the fusion prompt
        if tesseract_text:
            ocr_comparison = f"""**Tesseract Output** (fast, good for printed text):
```
{tesseract_text[:2000]}{"..." if len(tesseract_text) > 2000 else ""}
```

**Surya Output** (thorough, good for handwriting):
```
{surya_text[:2000]}{"..." if len(surya_text) > 2000 else ""}
```"""
        else:
            ocr_comparison = f"""**Surya Output** (only engine available):
```
{surya_text[:2000]}{"..." if len(surya_text) > 2000 else ""}
```"""
        
        prompt = f"""You are an expert OCR correction specialist with perfect vision. You have the ORIGINAL IMAGE and TWO OCR outputs.

**CRITICAL: The IMAGE is your ground truth - not the OCR outputs!**

**Document Type:** {analysis.document_type} | **Complexity:** {analysis.complexity} | **Has Tables:** {analysis.has_tables} | **Has Handwriting:** {analysis.has_handwriting}

{ocr_comparison}

**STEP-BY-STEP PROCESS:**

**Step 1: IDENTIFY DISAGREEMENTS**
- Compare Tesseract and Surya line by line
- Mark every word/number where they differ
- Common disagreements: addresses, dates, numbers, similar-looking characters

**Step 2: RESOLVE USING THE IMAGE**
When OCR outputs disagree, look VERY CAREFULLY at the image:

**Common OCR Errors to Watch For:**
- **"1" vs "4" vs "l"**: Look at shape - is it straight (1) or open (4)?
- **"0" vs "O"**: Numbers have more consistent size, letters vary
- **"5" vs "S"**: Look at context - is it in a number or word?
- **"8" vs "B"**: Numbers in addresses/dates, letters in words
- **"6" vs "G"**: Check context and font
- **"2" vs "Z"**: Numbers are rounded, Z is angular

**Example:** If Tesseract says "4961" and Surya says "1961":
1. Look at the first digit in the IMAGE
2. Is it straight like "1" or does it have an open side like "4"?
3. Context: Street addresses 1000-2999 are more common than 4000-9999
4. Choose the one that matches the IMAGE

**Step 3: USE CORRECT ENGINE PER SECTION**
- **PRINTED text** (receipts, forms, typed text): Prefer Tesseract
- **HANDWRITTEN** (signatures, notes, filled forms): Prefer Surya
- **TABLES**: Compare both carefully, use whichever preserves structure
- **NUMBERS**: Double-check against image if they disagree

**Step 4: FORMAT AS CLEAN MARKDOWN**
- Use proper heading levels (# ## ###)
- {"CRITICAL: Tables MUST use markdown | separators and be properly aligned" if analysis.has_tables else "Use proper lists and structure"}
- Preserve document hierarchy and layout
- Don't add or remove information

**REMEMBER:**
✓ The IMAGE shows the truth - trust what you SEE
✓ When unsure, look closer at the image
✓ OCR makes predictable mistakes with similar characters
✓ Context matters: numbers in addresses, dates in forms

Output ONLY the corrected markdown. No commentary, no explanations, just the final text."""
        
        # Check if we need to upgrade to cloud provider for perfect tables
        if self.perfect_tables and analysis.has_tables and self.vision_provider == "ollama":
            print(f"  ℹ️  Upgrading to Gemini for perfect table formatting (perfect_tables=True)")
            # Temporarily use Gemini for this document
            temp_vision = get_vision_provider("gemini")
            if temp_vision.is_available():
                fused = await temp_vision.analyze(image, prompt)
            else:
                print(f"  ⚠️  Gemini not available, using {self.vision_provider}")
                fused = await self.vision.analyze(image, prompt)
        else:
            # Use configured provider
            fused = await self.vision.analyze(image, prompt)
        
        print(f"  ✓ Fusion complete - best of both engines!")
        
        return fused
    
    async def pass3_vision_guided_correction(
        self,
        image: Image.Image,
        ocr_text: str,
        analysis: DocumentAnalysis,
        engine_used: str
    ) -> str:
        """
        Pass 3: Use vision model (Gemini 2.5 Pro) to correct and format OCR output.
        
        Vision model sees both the image AND the OCR text to:
        - Correct OCR errors by comparing to image
        - Structure markdown properly
        - Format tables correctly
        - Fix alignment issues
        """
        print(f"✨ Pass 3: Vision-guided fusion with {self.vision_provider.upper()} ({self.vision.model_name})...")
        
        # Build context-aware prompt
        prompt = f"""You are an expert OCR correction specialist. You can see both the original document image and the raw OCR text.

**Document Analysis:**
- Type: {analysis.document_type}
- Complexity: {analysis.complexity}
- Has tables: {analysis.has_tables}
- Has handwriting: {analysis.has_handwriting}
- OCR Engine used: {engine_used}

**Raw OCR Output:**
```
{ocr_text}
```

**Your Task:**
1. **Look carefully at the image** and compare it to the OCR text character by character
2. **Correct OCR errors**:
   - Fix misread characters (e.g., "4961" might be "1961")
   - Correct garbled words
   - Fix number transpositions
   - Correct punctuation
3. **Structure the content** into clean, beautiful markdown:
   - Use proper headings (# ## ###) for sections
   - Format lists with proper bullets or numbers
   - **IMPORTANT**: If there are tables, create perfectly formatted markdown tables
   - Preserve the document's logical structure and hierarchy
4. **Fix formatting**:
   - Proper spacing and alignment
   - Organize sections logically
   - Maintain visual hierarchy

**Special Instructions:**
{"- CRITICAL: This document has TABLES. Examine each table cell carefully in the image and create accurate markdown tables with | separators. Double-check all values." if analysis.has_tables else ""}
{"- This document has handwriting. Use the image to correct OCR mistakes in handwritten portions." if analysis.has_handwriting else ""}
{"- This is a COMPLEX document. Pay extra attention to layout, structure, and preserving all information accurately." if analysis.complexity == 'high' or analysis.complexity == 'medium' else ""}

Output ONLY the corrected, formatted markdown. No explanations or commentary."""
        
        # Use configured vision provider
        corrected = await self.vision.analyze(image, prompt)
        
        print(f"  ✓ Correction and formatting complete")
        
        return corrected
    
    async def process(self, image: Image.Image) -> OCRResult:
        """
        Execute complete intelligent OCR pipeline.
        
        Returns final OCR result with all passes complete.
        """
        print("\n" + "="*70)
        if self.use_hybrid_ocr:
            print("🧠 INTELLIGENT HYBRID OCR PIPELINE (Dual Engine)")
        else:
            print("🧠 INTELLIGENT MULTI-PASS OCR PIPELINE")
        print("="*70 + "\n")
        
        # Pass 1: Analyze
        analysis = await self.pass1_analyze_document(image)
        
        # Pass 2: Extract (Hybrid or Single)
        if self.use_hybrid_ocr:
            # HYBRID MODE: Run both engines in parallel
            tesseract_text, surya_text, engines_used = await self.pass2_dual_extract(image, analysis)
            
            # Pass 3: Fusion
            final_text = await self.pass3_vision_guided_fusion(
                image, tesseract_text, surya_text, analysis, engines_used
            )
            
            raw_text_length = len(tesseract_text or "") + len(surya_text or "")
        else:
            # SINGLE ENGINE MODE: Pick best engine
            raw_text, engines_used = await self.pass2_extract_text(image, analysis)
            
            # Pass 3: Correction
            final_text = await self.pass3_vision_guided_correction(
                image, raw_text, analysis, engines_used
            )
            
            raw_text_length = len(raw_text)
        
        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETE")
        print("="*70 + "\n")
        
        # Create result
        result = OCRResult(
            text=final_text,
            confidence=0.98 if self.use_hybrid_ocr else 0.95,  # Higher confidence with hybrid
            engine_name=f"intelligent_pipeline({engines_used}+gemini_fusion)" if self.use_hybrid_ocr else f"intelligent_pipeline({engines_used}+vision)",
            metadata={
                'pipeline': 'intelligent_hybrid' if self.use_hybrid_ocr else 'intelligent_multi_pass',
                'analysis': analysis.__dict__,
                'ocr_engines': engines_used,
                'hybrid_mode': self.use_hybrid_ocr,
                'raw_text_length': raw_text_length,
                'final_text_length': len(final_text),
                'passes_completed': 3
            }
        )
        
        return result

