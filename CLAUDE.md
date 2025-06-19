# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Virtual Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Deactivate virtual environment
deactivate
```

### Running the Application
```bash
# Run both servers simultaneously (recommended)
sh run_servers.sh

# Run individual servers
python src/user_interface/app.py   # API Server (port 5001)
python main.py                     # Main Application (port 5002)
```

### Testing
```bash
# Run all unit tests
python -m unittest discover -s tests

# Run specific test files
python -m unittest tests/test_content_analyzer.py
python -m unittest tests/test_document_processor.py
python -m unittest tests/test_storage_manager.py
python -m unittest tests/test_report_generator.py
python -m unittest tests/test_batch_processor.py

# Run docling integration tests
python -m unittest tests/test_docling_integration.py

# Individual test scripts for development
python test_docling.py
python test_processor.py
python test_batch.py
```

### Debugging Common Issues
- **ImportError for 'url_quote' from 'werkzeug.urls'**: Resolved by upgrading Flask to 3.1.1 and Jinja2 to 3.1.6
- **Port conflicts**: Flask apps configured to use ports 5001-5003 to avoid conflicts with macOS AirPlay (port 5000)

## Architecture Overview

This is a multi-component document processing and analysis system with the following architecture:

### Core Components
1. **DocumentProcessor** (`src/document_processor/processor.py`): Handles document parsing and content extraction using docling library
2. **StorageManager** (`src/storage_manager/manager.py`): Manages document storage, indexing, and file system monitoring
3. **ContentAnalyzer** (`src/content_analyzer/analyzer.py`): Provides search functionality with pattern matching and formula recognition
4. **ReportGenerator** (`src/report_generator/generator.py`): Generates HTML and JSON reports from search results
5. **BatchProcessor** (`src/storage_manager/batch_processor.py`): Handles bulk document processing operations

### Document Processing Pipeline
- **Input**: Documents placed in `input/` directory are automatically monitored
- **Processing**: Documents are processed through docling for content extraction
- **Storage**: Processed documents are stored in `output/documents/` with metadata
- **Indexing**: Document index maintained in `output/document_index.json`
- **Search**: ContentAnalyzer provides real-time search across indexed documents

### Web Interface Architecture
- **Main Application** (`main.py`): Initializes all components and runs on port 5002
- **API Server** (`src/user_interface/app.py`): Flask REST API on port 5001/5003
- **Frontend**: HTML templates with JavaScript for document upload, search, and reporting

### Key Data Structures
- **Document Model**: Standardized format with id, filename, format, content, metadata
- **Search Query**: Pattern-based queries with options (caseSensitive, wholeWord, regex, formulaMatch)
- **Search Results**: Grouped by document with match details and context

## Development Patterns

### Component Initialization
All components are initialized in `main.py` and injected into the Flask app:
```python
# Components are attached to Flask app instance
app.document_processor = document_processor
app.storage_manager = storage_manager
app.content_analyzer = content_analyzer
app.report_generator = report_generator
```

### Error Handling
- Graceful degradation when docling is unavailable
- Comprehensive error logging throughout the application
- API endpoints return structured JSON error responses

### File Monitoring
- Uses watchdog library for real-time file system monitoring
- Automatically processes new documents added to input directory
- Supports common document formats: PDF, DOCX, TXT, DOC

### Search Implementation
- Frontend search requests are processed by ContentAnalyzer
- Results are grouped by document for display
- StorageManager provides document metadata enrichment
- ReportGenerator creates persistent reports of search results

## Configuration

### Environment Variables
API keys are configured via `.env` file (see `.env.example`):
- ANTHROPIC_API_KEY: Required for AI features
- Other optional API keys for various providers

### Port Configuration
- API Server: 5001 (app.py standalone) / 5003 (app.py via main.py)
- Main Application: 5002
- Configurable via config.json or hardcoded defaults

### Directory Structure
```
input/          # Source documents (monitored)
output/         # Processed documents and reports
  documents/    # Individual document JSON files
  reports/      # Generated HTML/JSON reports
tests/          # Unit tests and test data
src/            # Source code modules
```