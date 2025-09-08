# Surya OCR (Tesseract + Surya) API

Docker container sources for a powerful OCR API that combines Tesseract and Surya OCR capabilities for high-accuracy text extraction from images.

## Features

- **Dual OCR Engines**: Uses both Tesseract and Surya OCR for maximum accuracy
- **RESTful API**: Simple HTTP endpoints for OCR processing
- **Docker Ready**: Containerized for easy deployment
- **Unraid Compatible**: Includes docker-compose for Unraid Docker UI
- **Text Cleanup Tools**: Advanced OCR text processing and cleanup scripts
- **Flexible Input**: Supports file upload and base64 image input

## Quick Start

### Using Docker Compose (Recommended for Unraid)

```bash
# Clone the repository
git clone https://github.com/AlexXYK/homeCR.git
cd homeCR

# Start the service
docker-compose up -d
```

The API will be available at `http://localhost:5000`

### Using Docker Build

```bash
# Build the container
docker build -t surya-ocr .

# Run the container
docker run -d -p 5000:5000 --name surya-ocr-api surya-ocr
```

## API Endpoints

### Health Check
- **GET** `/` - Returns API status

### OCR Processing
- **POST** `/ocr` - Process image with both OCR engines
  - Form data: `image` (file upload)
  - JSON: `{"image_base64": "..."}` 
  - Optional: `method` parameter (`tesseract`, `surya`, or `both`)

- **POST** `/ocr/tesseract` - Process with Tesseract only
  - Form data: `image` (file upload)
  - Optional: `include_boxes=true` for bounding box data

### Example Usage

```bash
# Upload an image file
curl -X POST -F "image=@document.jpg" http://localhost:5000/ocr

# Use specific OCR method
curl -X POST -F "image=@document.jpg" -F "method=surya" http://localhost:5000/ocr

# Get bounding box data (Tesseract only)
curl -X POST -F "image=@document.jpg" -F "include_boxes=true" http://localhost:5000/ocr/tesseract
```

## Development

### Branches
- `main` - Production ready code
- `dev` - Development branch for new features

### Local Development Setup

```bash
# Clone and switch to dev branch
git clone https://github.com/AlexXYK/homeCR.git
cd homeCR
git checkout dev

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

### Docker Development

```bash
# Build and test locally
docker-compose up --build

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose down
docker-compose up --build
```

## Unraid Setup

1. **Install from Docker Hub**: Use `alexxyk/homeocr` (if published)
2. **Build from Source**: 
   - Set Repository to: `https://github.com/AlexXYK/homeCR`
   - Set Branch to: `main`
   - Port mapping: `5000:5000`
   - Optional volumes:
     - `/mnt/user/appdata/surya-ocr/data:/app/data` (for file processing)
     - `/mnt/user/appdata/surya-ocr/tmp:/tmp/ocr` (for temporary files)

## Text Cleanup Tools

The repository includes several OCR text cleanup utilities:

- `cleanup_fix.py` - Image preprocessing for better OCR
- `cleanup_patch.py` - Basic OCR text error correction
- `cleanup_patch2.py` - Advanced language-specific text cleanup  
- `cleanup_patch3.py` - Statistical analysis and batch processing

```bash
# Preprocess image for better OCR
python cleanup_fix.py input.jpg -o processed.jpg

# Clean OCR text output
python cleanup_patch.py ocr_output.txt -o cleaned.txt --fix-letters

# Advanced cleanup with language support
python cleanup_patch2.py document.txt -o clean_document.txt -l en

# Analyze OCR quality
python cleanup_patch3.py document.txt --analyze-only
```

## Configuration

### Environment Variables
- `PORT` - API port (default: 5000)
- `PYTHONUNBUFFERED` - Python output buffering (default: 1)

### Docker Compose Override
Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'
services:
  surya-ocr:
    ports:
      - "8000:5000"  # Use different port
    environment:
      - DEBUG=1
```

## Troubleshooting

### Common Issues
1. **Out of memory**: Reduce image size or increase Docker memory limit
2. **Slow processing**: Consider using GPU acceleration (modify Dockerfile)
3. **Missing text**: Try different OCR engines or preprocess with cleanup_fix.py

### Logs
```bash
# View container logs
docker-compose logs surya-ocr

# Follow real-time logs  
docker-compose logs -f surya-ocr
```

## Contributing

1. Fork the repository
2. Create feature branch from `dev`
3. Make changes and test
4. Submit pull request to `dev` branch

## License

See repository for license information.

