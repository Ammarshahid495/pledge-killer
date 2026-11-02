# PLEDGE FIGHTER

> **Check code similarity. Protect your privacy.**  
> A privacy-first, peer-to-peer code similarity detection platform with Stanford MOSS-grade algorithmic comparison.

---

## 1. Overview & Core Philosophy

**Pledge Fighter** is built on the radical premise that students should be able to collaboratively verify their academic integrity without sacrificing code privacy or granting authority to a privileged administrator:

- **Strict Equal Permissions**: There are NO teachers, NO classroom owners with extra privileges, and NO moderators. The creator of a classroom is simply `Peer A`—the first participant. Every member has identical rights.
- **Source Code Privacy**: Users can **never** view or download another participant's raw source code or private report.
- **Automated Threshold**: Similarity analysis begins automatically once **at least 5 distinct students** have submitted valid assignments.
- **Incremental Analysis**: When additional students submit or replace their code, the system calculates incremental comparisons without recalculating unchanged pairs.
- **Honest Reporting**: Similarity metrics represent structural code overlap and token sequence alignment. Results are framed objectively, never as accusations or cheating probabilities.

---

## 2. Stanford MOSS-Grade Similarity Engine

The similarity engine (`similarity-engine/`) implements the Stanford MOSS Winnowing algorithm (Schleimer, Wilkerson, Aiken, SIGMOD 2003):

```
[Raw C++ Code]
      │
      ▼
[Lexical Tokenizer] ──────► [Exact line, column & offset tracking]
      │
      ▼
[Comment & Whitespace Stripper]
      │
      ▼
[Identifier Normalizer] ───► [Keywords & control flow preserved; variables -> ID]
      │
      ▼
[K-Gram Generation] ──────► [Sliding window of k=8..10 tokens]
      │
      ▼
[Karp-Rabin Rolling Hash] ─► [O(1) rolling polynomial hash]
      │
      ▼
[Winnowing Filter (w=4..5)] ► [Deterministic rightmost minimum tie-break]
      │
      ▼
[Fingerprint Set] ─────────► [Inverted index hash lookup]
      │
      ▼
[Matcher & Coalescer] ─────► [Merge contiguous intervals into line-bounded regions]
      │
      ▼
[Honest Metrics] ──────────► [Directional coverage & symmetric similarity %]
```

---

## 3. Tech Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy, Alembic, Argon2id (`argon2-cffi`), PyJWT, Celery, Redis.
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, React Router v6.
- **Database**: PostgreSQL (Docker / production) with transparent SQLite fallback for immediate local testing.
- **Storage**: Pluggable storage driver (Local encrypted/UUID storage driver + S3/MinIO driver).

---

## 4. Quickstart Guide (Local Development)

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm

### 1. Setup Backend
```bash
# In project root
python -m venv .venv

# Activate venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt
```

### 2. Run Backend Tests
```bash
# Run both similarity engine tests and full backend test suite
pytest "similarity-engine/tests" "backend/tests" -v
```

### 3. Start Backend Server
```bash
# Start FastAPI backend on http://127.0.0.1:8000
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be available at:
`http://127.0.0.1:8000/docs`

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 5. Deployment with Docker Compose

To deploy the entire production stack (PostgreSQL, Redis, Celery Worker, FastAPI backend, and Nginx serving the React frontend):

```bash
docker compose up -d --build
```

Services started:
- `frontend`: Port 80 (React + Nginx)
- `backend`: Port 8000 (FastAPI)
- `celery_worker`: Background similarity comparison worker
- `postgres`: Port 5432 (PostgreSQL)
- `redis`: Port 6379 (Redis Broker)

---

## 6. API Reference (`/api/v1`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register student account |
| `POST` | `/api/v1/auth/login` | Login (returns JWT and sets HttpOnly cookie) |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token |
| `POST` | `/api/v1/auth/logout` | Revoke session |
| `GET` | `/api/v1/auth/me` | Current user profile |
| `POST` | `/api/v1/classrooms` | Create classroom (creator becomes Peer A) |
| `GET` | `/api/v1/classrooms` | List classrooms user has joined |
| `GET` | `/api/v1/classrooms/{id}` | Classroom details & submission status |
| `POST` | `/api/v1/classrooms/join/{token}` | Join via link token |
| `GET` | `/api/v1/classrooms/{id}/members` | Anonymous members list (`Peer A`, `Peer B`) |
| `POST` | `/api/v1/classrooms/{id}/submissions` | Upload `.cpp` file (triggers analysis if $\ge 5$) |
| `GET` | `/api/v1/classrooms/{id}/submissions/me` | View user's own submission & code |
| `POST` | `/api/v1/classrooms/{id}/submissions/me/resubmit` | Replace assignment with new version |
| `GET` | `/api/v1/reports/me` | List user's private similarity reports |
| `GET` | `/api/v1/reports/me/{id}` | Detailed private report with highlighted code |
| `GET` | `/api/v1/reports/me/{id}/download` | Download private report as JSON |

---

## 7. Security & Privacy Audit Verification

1. **Zero Raw Code Leakage**: No route exists in the API that accepts an arbitrary submission ID to return peer source code. All submission endpoints are strictly relative to `/me`.
2. **Anonymous Labels**: Students are labeled deterministically as `Peer A`, `Peer B`, `Peer C` within the classroom report. Names, emails, and database UUIDs are never returned to peers.
3. **Argon2id Password Security**: Passwords are saved using Argon2id with memory cost 64MB and parallelism 4.
4. **File Safety**: Rejects executables (ELF, PE, Mach-O), archives (ZIP, 7z, GZIP), empty files, null bytes, and non-`.cpp` files. Code is **never executed or compiled**.
