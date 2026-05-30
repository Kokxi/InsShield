# InsShield

**Insurance Document Sensitive Information Shield**

InsShield is a document scanning and analysis tool that automatically detects, identifies, and masks sensitive personally identifiable information (PII) in insurance policy documents. Supports PDF and Word formats with OCR capabilities.

## Features

- **Multi-format Support** — Parse PDF and Word (`.docx`) documents
- **OCR Engine** — Built-in rapid OCR for scanned images in PDFs (powered by RapidOCR)
- **PII Detection** — Automatically identify Chinese ID numbers, phone numbers, bank cards, addresses, names, and more across the document
- **Document Classification** — Classify documents as ID card, insurance policy, bank statement, etc.
- **Visual Preview** — Web interface to upload, preview, and highlight sensitive regions
- **Data Export** — Export masked/cleaned results for safe sharing
- **Statistics Dashboard** — Summary of document counts, PII types, and detection distribution

## Quick Start

### Prerequisites

- Python 3.10+
- pip / uv

### Install

```bash
# Clone
git clone https://github.com/your-org/ins-shield.git
cd ins-shield

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# Start the web server
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

### Run Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
ins-shield/
├── app/                    # Application core
│   ├── main.py             # FastAPI entry point
│   ├── router.py           # API routes
│   ├── config.py           # Configuration
│   ├── models.py           # Pydantic models
│   ├── classifier.py       # Document classification
│   ├── exporter.py         # Data export
│   ├── pdf_processor.py    # PDF processing + OCR
│   ├── word_processor.py   # Word document processing
│   ├── doc_classifier.py   # Document type classifier
│   ├── pii_extractor.py    # PII detection engine
│   └── logger.py           # Logging setup
├── static/                 # Frontend assets
│   ├── index.html          # Main page
│   ├── style.css           # Styles
│   └── script.js           # Frontend logic
├── tests/                  # Test suite
├── docs/                   # Documentation
└── requirements.txt        # Python dependencies
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/upload/` | Upload documents |
| POST | `/api/scan/` | Trigger OCR + PII scan |
| GET | `/api/results/{task_id}` | Get scan results |
| GET | `/api/statistics/` | Dashboard statistics |
| GET | `/api/export/{task_id}` | Export masked results |
| POST | `/api/classify/` | Classify document type |

## Tech Stack

- **Backend** — Python, FastAPI, RapidOCR, pdfplumber, python-docx
- **Frontend** — HTML, CSS, JavaScript (vanilla)
- **PII Engine** — Rule-based + pattern matching (regex + phone/ID/bank card validation)

## License

MIT
