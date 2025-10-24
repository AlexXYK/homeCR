#!/bin/bash
# Setup script for Universal OCR System

echo "=========================================="
echo "Universal OCR System - Setup"
echo "=========================================="
echo

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if Tesseract is installed
echo
echo "Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n1)
    echo "✓ $tesseract_version"
else
    echo "✗ Tesseract not found"
    echo "  Install with: sudo apt install tesseract-ocr (Linux)"
    echo "  Or: brew install tesseract (Mac)"
fi

# Create virtual environment
echo
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo
echo "Creating directories..."
mkdir -p data/test_datasets/{handwriting,print,tables,mixed,screenshots,edge_cases}/{images,ground_truth}
mkdir -p dashboard/static dashboard/templates
echo "✓ Directories created"

# Check if .env exists
echo
if [ -f ".env" ]; then
    echo "✓ .env file exists"
else
    echo "Creating .env file from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ .env file created"
        echo "  Please edit .env and add your Gemini API key"
    else
        echo "✗ .env.example not found"
    fi
fi

# Check Ollama connection
echo
echo "Checking Ollama connection..."
ollama_host=$(grep OLLAMA_HOST .env 2>/dev/null | cut -d'=' -f2 || echo "http://192.168.0.153:11434")
if curl -s "$ollama_host/api/tags" > /dev/null 2>&1; then
    echo "✓ Ollama server is reachable at $ollama_host"
    
    # Check for required models
    echo
    echo "Checking Ollama models..."
    if curl -s "$ollama_host/api/tags" | grep -q "llava"; then
        echo "✓ LLaVA vision model found"
    else
        echo "✗ LLaVA model not found"
        echo "  Run on Ollama server: ollama pull llava:13b"
    fi
    
    if curl -s "$ollama_host/api/tags" | grep -q "gemma"; then
        echo "✓ Gemma model found"
    else
        echo "✗ Gemma model not found"
        echo "  Run on Ollama server: ollama pull gemma2:12b"
    fi
else
    echo "✗ Cannot reach Ollama server at $ollama_host"
    echo "  Please check the OLLAMA_HOST in .env"
fi

echo
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "1. Edit .env and add your Gemini API key (optional, for AI agents)"
echo "2. Ensure required Ollama models are pulled:"
echo "   - ollama pull llava:13b"
echo "   - ollama pull gemma2:12b"
echo "3. Run the system:"
echo "   python main.py"
echo
echo "The system will be available at:"
echo "  - API: http://localhost:5000"
echo "  - Dashboard: http://localhost:8080"
echo

