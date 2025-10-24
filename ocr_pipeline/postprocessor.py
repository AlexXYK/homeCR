"""Post-processing for OCR results - cleaning and formatting."""
import re
import httpx
from config import settings


class OCRPostProcessor:
    """Post-processes OCR results for better output quality."""
    
    def __init__(self):
        self.ollama_host = settings.ollama_host
        self.formatter_model = settings.ollama_formatter_model
    
    async def format_as_markdown(self, text: str, use_llm: bool = True) -> str:
        """
        Format OCR text as clean markdown.
        
        Args:
            text: Raw OCR text
            use_llm: Whether to use LLM for formatting (slower but better)
            
        Returns:
            Formatted markdown text
        """
        if not text or not text.strip():
            return ""
        
        if use_llm:
            return await self._format_with_llm(text)
        else:
            return self._format_with_regex(text)
    
    def _format_with_regex(self, text: str) -> str:
        """Basic regex-based formatting."""
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Fix ellipsis
        text = re.sub(r'(\. ?){3,}', '…', text)
        
        # Normalize newlines
        text = re.sub(r'\n{2,}', '\n\n', text)
        
        # Fix list markers
        text = re.sub(r'^[*-]\s+', '- ', text, flags=re.MULTILINE)
        
        return text.strip()
    
    async def _format_with_llm(self, text: str) -> str:
        """Use LLM for intelligent formatting."""
        prompt = f"""Convert this raw OCR text into clean, well-formatted Markdown.

Requirements:
- Preserve all information accurately
- Use proper headings (# ## ###) for titles
- Format lists with proper bullets (-)
- Convert table-like structures into markdown tables
- Fix obvious OCR errors
- Use proper punctuation and spacing

Raw OCR text:
```
{text}
```

Output ONLY the formatted markdown, no commentary:"""
        
        payload = {
            "model": self.formatter_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 4096
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            formatted = data.get("response", "").strip()
            return formatted if formatted else text
            
        except Exception as e:
            print(f"LLM formatting error: {e}, falling back to regex")
            return self._format_with_regex(text)
    
    def clean_text(self, text: str, aggressive: bool = False) -> str:
        """
        Clean OCR text by removing artifacts and noise.
        
        Args:
            text: Raw OCR text
            aggressive: If True, apply stricter filtering
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        lines = text.splitlines()
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Normalize symbols
            line = (line.replace('·', '.')
                       .replace('•', '.')
                       .replace('×', 'x')
                       .replace('–', '-')
                       .replace('—', '-'))
            
            # Skip lines with too many special characters
            if aggressive:
                alpha_count = sum(c.isalpha() for c in line)
                if alpha_count < 3 and len(line) > 1:
                    continue
            
            # Fix multiple punctuation
            line = re.sub(r'([.,;:!?])\1+', r'\1', line)
            
            # Fix spaces before punctuation
            line = re.sub(r'\s+([.,;:!?])', r'\1', line)
            
            # Normalize spaces
            line = re.sub(r'\s+', ' ', line)
            
            if line:
                cleaned_lines.append(line)
        
        # Join and normalize paragraph breaks
        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

