# Medical PDFs for RAG

Drop PDF files here, then run the ingest script so the Medical Assistant can answer from them.

## Steps

1. **Start Qdrant** (from project root):
   ```bash
   docker compose up -d
   ```

2. **Put PDFs in this folder** (`docs/`). Examples:
   - NHLBI Pneumonia fact sheet
   - Chest X-ray / Brain MRI / Skin cancer patient info PDFs

3. **Ingest** (from project root):
   ```bash
   python scripts/ingest_pdfs.py
   ```
   With no arguments this ingests all PDFs in `docs/`.  
   To ingest specific paths:
   ```bash
   python scripts/ingest_pdfs.py docs/pneumonia.pdf docs/chest_xray.pdf
   ```

4. Each run **replaces** the RAG corpus: all PDFs you want in the assistant must be in `docs/` (or listed as arguments) when you run the script.

## Requirements

- Backend dependencies installed (`pip install -r backend/requirements.txt`)
- Qdrant running at `QDRANT_URL` (default `http://localhost:6333`)
