# Mistral-7B Medical LLM Setup

The backend uses an **OpenAI-compatible** API to talk to a **Mistral-7B model fine-tuned on medical data**. All LangGraph agents call a single client in `backend/app/agents/llm.py`.

## Environment variables

Set these in `backend/.env`:

```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=mistral-7b-medical
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024
```

| Variable | Description |
|----------|-------------|
| `LLM_BASE_URL` | OpenAI-compatible `/v1` endpoint |
| `LLM_API_KEY` | API key for hosted providers; any string for local Ollama |
| `LLM_MODEL` | Model name/tag on the server (your fine-tuned medical model) |
| `LLM_TEMPERATURE` | Lower = more deterministic (recommended 0.1–0.3) |
| `LLM_MAX_TOKENS` | Max completion length |

## Option A: Ollama (local, simplest)

1. Install [Ollama](https://ollama.com/).
2. Import or create your medical fine-tune (example tag `mistral-7b-medical`):

```bash
# If you have a GGUF or Modelfile from your fine-tune:
ollama create mistral-7b-medical -f Modelfile
```

3. Start Ollama (usually runs as a service on port **11434**).
4. Set `LLM_BASE_URL=http://localhost:11434/v1` and `LLM_MODEL=mistral-7b-medical`.

## Option B: vLLM (local GPU, higher throughput)

Run your fine-tuned weights with vLLM on a **separate port** (avoid clash with FastAPI on 8000):

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /path/to/mistral-7b-medical \
  --host 0.0.0.0 \
  --port 8001 \
  --max-model-len 4096
```

Then in `.env`:

```env
LLM_BASE_URL=http://localhost:8001/v1
LLM_API_KEY=local
LLM_MODEL=/path/to/mistral-7b-medical
```

## Option C: Hosted OpenAI-compatible API

Point `LLM_BASE_URL` and `LLM_API_KEY` at your provider (Together, Fireworks, custom deployment, etc.) and set `LLM_MODEL` to the deployed model id.

## Verify

1. Start your inference server.
2. Start the backend: `uvicorn app.main:app --reload --port 8000`
3. Send a chat message in the UI or:

```bash
curl http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d "{\"message\":\"What are common pneumonia symptoms?\"}"
```

## Hardware notes (GTX 1650 / 4GB VRAM)

Full Mistral-7B may not fit on 4GB VRAM at fp16. Options:

- Run LLM on **CPU** via Ollama with a quantized model (Q4_K_M).
- Use a **hosted** medical API and keep vision/RAG local.
- Use **vLLM** with `--quantization awq` or a 4-bit GGUF in Ollama.

Vision (MobileNet), embeddings (MiniLM), and Whisper STT are separate from the LLM and can stay on GPU/CPU as configured.
