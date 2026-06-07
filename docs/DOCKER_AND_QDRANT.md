# Docker Desktop + Qdrant for RAG

This project uses **Qdrant** (vector database) for RAG. Qdrant runs in Docker.

## 1. Install Docker Desktop

1. **Download** Docker Desktop for Windows:
   - https://www.docker.com/products/docker-desktop/
   - Or direct: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe

2. **Run the installer** and follow the steps (use WSL 2 if prompted).

3. **Restart** your PC if asked, then **open Docker Desktop** and wait until it says "Docker Desktop is running".

## 2. Start Qdrant

From the **project root** (`D:\Multi_med_agent`), in PowerShell or Command Prompt:

```powershell
docker compose up -d
```

This starts Qdrant in the background on port **6333**. Your `backend/.env` already has `QDRANT_URL=http://localhost:6333`.

## 3. Ingest your PDFs into Qdrant

```powershell
.\.venv\Scripts\python.exe scripts/ingest_pdfs.py
```

When it finishes, the Medical Assistant can answer from your PDFs (RAG).

## 4. Optional: stop Qdrant

```powershell
docker compose down
```

Data is kept in a Docker volume (`qdrant_storage`) so it persists when you start again with `docker compose up -d`.
