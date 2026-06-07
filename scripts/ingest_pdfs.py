#!/usr/bin/env python3
"""
Ingest PDFs into Qdrant: split with RecursiveCharacterTextSplitter (500/50),
embed with all-MiniLM-L6-v2, upsert to medical_docs.
Each run replaces the RAG corpus (clears collection then upserts).

Usage:
  python scripts/ingest_pdfs.py                    # ingest all PDFs in docs/
  python scripts/ingest_pdfs.py docs/              # same
  python scripts/ingest_pdfs.py path/to/file.pdf   # specific file(s) or dir(s)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend to path
backend = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct

from app.services.rag.embedder import embed
from app.services.rag.qdrant_client import (
    COLLECTION_NAME,
    delete_collection,
    ensure_collection,
    get_client,
)


def load_pdf(path: Path) -> list[dict]:
    """Load PDF into list of {text, metadata}."""
    loader = PyPDFLoader(str(path))
    docs = loader.load()
    return [
        {
            "text": getattr(d, "page_content", ""),
            "metadata": getattr(d, "metadata", {}),
        }
        for d in docs
    ]


def split_chunks(docs: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """Split into chunks with overlap."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
    )
    out = []
    for d in docs:
        chunks = splitter.split_text(d["text"])
        for c in chunks:
            if c.strip():
                out.append({
                    "text": c,
                    "source": d["metadata"].get(
                        "source", str(d["metadata"].get("file_path", ""))
                    ),
                    "page": d["metadata"].get("page"),
                })
    return out


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    default_docs = project_root / "docs"

    if len(sys.argv) < 2:
        paths_to_scan = [default_docs]
        if not default_docs.exists():
            print(f"Usage: python scripts/ingest_pdfs.py <pdf_or_dir> ...")
            print(f"Default docs folder not found: {default_docs}")
            return 1
        print(f"Ingesting all PDFs from: {default_docs}", flush=True)
    else:
        paths_to_scan = [Path(a) for a in sys.argv[1:]]

    all_chunks: list[dict] = []
    for p in paths_to_scan:
        if not p.exists():
            print(f"Skip (not found): {p}")
            continue
        if p.is_file() and p.suffix.lower() == ".pdf":
            try:
                raw = load_pdf(p)
            except Exception as e:
                print(f"Error loading {p}: {e}")
                continue
            docs = [
                {"text": d["text"], "metadata": {**d["metadata"], "source": str(p)}}
                for d in raw
            ]
            chunks = split_chunks(docs)
            for c in chunks:
                c["source"] = str(p)
            all_chunks.extend(chunks)
            print(f"Loaded {p.name}: {len(chunks)} chunks", flush=True)
        elif p.is_dir():
            for pdf in sorted(p.rglob("*.pdf")):
                try:
                    raw = load_pdf(pdf)
                except Exception as e:
                    print(f"Error loading {pdf}: {e}")
                    continue
                docs = [
                    {"text": d["text"], "metadata": {**d["metadata"], "source": str(pdf)}}
                    for d in raw
                ]
                chunks = split_chunks(docs)
                for c in chunks:
                    c["source"] = str(pdf)
                all_chunks.extend(chunks)
                print(f"Loaded {pdf.name}: {len(chunks)} chunks", flush=True)

    if not all_chunks:
        print("No chunks to ingest. Add PDFs to docs/ or pass paths.")
        return 0

    try:
        get_client()
    except Exception as e:
        print(f"Qdrant not reachable. Start with: docker compose up -d")
        print(f"Error: {e}")
        return 1

    BATCH = 256
    texts = [c["text"] for c in all_chunks]
    vectors: list[list[float]] = []
    try:
        for start in range(0, len(texts), BATCH):
            end = min(start + BATCH, len(texts))
            batch_vecs = embed(texts[start:end])
            vectors.extend(batch_vecs)
            print(f"Embedding {end}/{len(texts)} chunks...", flush=True)
    except Exception as e:
        print(f"Embedding failed: {e}", flush=True)
        return 1

    print("Replacing RAG corpus (clear + upsert)...", flush=True)
    try:
        delete_collection()
        ensure_collection()
        client = get_client()
        # Upsert in batches to stay under Qdrant 32MB payload limit
        UPSERT_BATCH = 400
        total = len(vectors)
        for start in range(0, total, UPSERT_BATCH):
            end = min(start + UPSERT_BATCH, total)
            batch_points = [
                PointStruct(
                    id=start + i,
                    vector=vectors[start + i],
                    payload={
                        "text": all_chunks[start + i]["text"],
                        "source": all_chunks[start + i]["source"],
                        "page": all_chunks[start + i].get("page"),
                    },
                )
                for i in range(end - start)
            ]
            client.upsert(collection_name=COLLECTION_NAME, points=batch_points)
            print(f"Upserted {end}/{total} chunks...", flush=True)
    except Exception as e:
        print(f"Qdrant upsert failed: {e}", flush=True)
        return 1

    print(f"Ingested {total} chunks into {COLLECTION_NAME}.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
