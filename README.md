# InsureSight

An educational Singapore insurance gap analysis tool. Upload your policy PDFs to check for coverage gaps, over-insurance, and claim risks — benchmarked against MAS, LIA, MediShield, and MOH guidelines.

**Contact:** insuresight@gmail.com

> **Not financial advice.** This is an educational tool. Take your results to a MAS-licensed, fee-only financial adviser for personalised product recommendations.

---

## What it does

1. **Coverage gap analysis** — compares your policies against age-banded Singapore benchmarks (MAS 9–10× income for life, LIA 3.9–5× for CI, etc.)
2. **Over-insurance detection** — flags where your coverage materially exceeds what you need
3. **Claim risk review** — identifies fine-print clauses that may affect your claims given your profile
4. **Personalised recommendations** — suggests generic coverage structures and riders to close gaps

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Uvicorn |
| PDF parsing | PyMuPDF + pdfplumber fallback |
| LLM | GPT-4o (OpenAI) |
| Embeddings | text-embedding-3-small |
| Vector store | ChromaDB (auto-ingested on startup) |
| Gap calculator | Deterministic Python |
| Session store | In-memory (30-min TTL) |

---

## Local development

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key

### 1. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate    # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
# Edit .env — set OPENAI_API_KEY, leave ENVIRONMENT=development

# (Optional) Pre-ingest benchmark knowledge base
# The server auto-ingests on first startup, but you can do it manually:
python -m ingest.ingest_benchmarks

# Start the API server
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend

npm install

copy .env.local.example .env.local    # Windows
# cp .env.local.example .env.local    # macOS / Linux
# NEXT_PUBLIC_API_URL is already set to http://localhost:8000/api

npm run dev
```

### 3. Open the app

Visit [http://localhost:3000](http://localhost:3000)

---

## Production deployment

InsureSight uses a two-service architecture in production:

| Service | Platform | What it hosts |
|---|---|---|
| Frontend | **Vercel** | Next.js app |
| Backend | **Railway** | FastAPI + ChromaDB |

No other services are required. ChromaDB is auto-ingested from the benchmark data bundled in the repo on every cold start, so no separate vector-database service is needed.

---

### Deploy the backend to Railway

1. Create a free account at [railway.app](https://railway.app) and start a new project.
2. Connect your GitHub repository.
3. In the Railway project settings, set **Root Directory** to `backend`.
4. Railway will detect the `Procfile` and `requirements.txt` automatically.
5. Add the following **environment variables** in the Railway dashboard:

   | Variable | Value |
   |---|---|
   | `OPENAI_API_KEY` | `sk-…` |
   | `ENVIRONMENT` | `production` |
   | `ALLOWED_ORIGINS` | `https://<your-vercel-app>.vercel.app` |
   | `OPENAI_MODEL` | `gpt-4o` *(optional)* |
   | `EMBEDDING_MODEL` | `text-embedding-3-small` *(optional)* |

6. Deploy. Railway will assign a public URL like `https://insuresight-api-production.up.railway.app`.

   > **Benchmark auto-ingest:** On first startup the app will automatically ingest the benchmark knowledge base into ChromaDB. This takes ~15 seconds and makes a small number of OpenAI embedding API calls. Subsequent restarts skip the ingest if data already exists on disk.

---

### Deploy the frontend to Vercel

1. Create a free account at [vercel.com](https://vercel.com) and import your GitHub repository.
2. In the Vercel project settings, set **Root Directory** to `frontend`.
3. Add the following **environment variable**:

   | Variable | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<your-railway-url>/api` |

4. Deploy. Vercel will build and publish the Next.js app automatically.

5. Copy the Vercel deployment URL (e.g. `https://insuresight.vercel.app`) and add it to your Railway `ALLOWED_ORIGINS` environment variable, then redeploy the backend.

---

### Post-deployment checklist

- [ ] Backend `/api/health` returns `{"status": "ok"}`
- [ ] Frontend loads at the Vercel URL
- [ ] Upload a test policy PDF — extraction should succeed
- [ ] Full analysis run completes (may take 30–60 s depending on policy count)
- [ ] Privacy notice shows `insuresight@gmail.com`

---

## Architecture

```
[Upload PDFs] → [Extract with GPT-4o (1 call/policy)] → [In-memory session]
     ↓
[Profile form + Guidance questions]
     ↓
[Sequential benchmark retrieval from ChromaDB]
     ↓
[Deterministic Python gap calculator]
     ↓
[Claim risk analysis (1 GPT-4o call)]
     ↓
[Recommendation (deterministic logic + 1 GPT-4o for prose)]
     ↓
[Summary (1 GPT-4o call)] → [Report dashboard]
```

**AI call budget:** N policies = N + 3 GPT-4o calls (+ 1 if guidance answers provided)

---

## Supported policy types

- Term life / Whole life
- Critical Illness (late stage)
- Early Critical Illness
- Hospitalisation / Integrated Shield Plans
- Disability Income
- CareShield Life supplement
- Personal Accident
- Total Permanent Disability (TPD)

---

## Limitations (MVP)

- Digital PDFs only — scanned/image PDFs are not supported
- No user accounts or saved history
- No specific product recommendations (no product catalogue)
- No live insurer API integration
- Max 10 policies, 20 MB each, 100 pages each

---

## PDPA compliance

- All policy data processed in-memory only — never written to disk or database
- Uploaded PDFs deleted from memory immediately after text extraction
- Sessions expire automatically after 30 minutes
- No third-party analytics on sensitive pages
- Privacy notice with PDPA disclosure shown before first upload
