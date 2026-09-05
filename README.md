<<<<<<< HEAD
# NEXUS

> Engineering intelligence for software teams.

NEXUS is an AI-powered engineering intelligence platform that turns software development activity into a continuously updated view of engineering health, risk, and operational signals.

It connects to GitHub, ingests engineering activity, computes meaningful metrics, detects anomalies, predicts engineering risks, and provides an evidence-backed AI analyst that can explain what is happening inside a software project.

NEXUS is being built as a production-oriented system from the beginning, with a focus on correctness, explainability, security, and maintainability.

---

## Why NEXUS?

Modern engineering teams generate enormous amounts of data:

- Commits
- Pull requests
- Reviews
- Issues
- CI/CD runs
- Deployments
- Documentation
- Incidents
- Engineering metrics

Most of this information is scattered across different tools.

NEXUS brings these signals together and answers questions such as:

- How healthy is this repository?
- Is engineering velocity improving or degrading?
- Which repositories are showing unusual behavior?
- Which pull requests are likely to become risky?
- Is CI reliability getting worse?
- Are deployments becoming more failure-prone?
- Why did the engineering risk score change?
- What evidence supports this conclusion?
- What should the engineering team investigate next?

The goal is not to create another dashboard full of charts. The goal is to create an engineering intelligence layer.

---

## Core Capabilities

### GitHub Integration
Connect a GitHub organization or account and allow NEXUS to access selected repositories through a GitHub App. NEXUS ingests engineering activity such as repositories, commits, pull requests, reviews, issues, workflow runs, and deployments. GitHub webhooks keep repository data continuously synchronized.

### Engineering Metrics
NEXUS calculates engineering metrics across configurable time windows, stored as historical snapshots to reason about trends over time:
- Pull request cycle time & throughput
- Review latency & PR size
- Commit frequency
- CI success and failure rates
- Deployment frequency & failure rates
- Issue resolution time

### Anomaly Detection
NEXUS identifies unusual engineering behavior using statistical and machine-learning techniques (e.g., sudden drop in deployment frequency, abnormal review latency, spike in CI failures).

```text
normal variation ──> statistical anomaly ──> engineering signal ──> potential risk
```

*An anomaly will never automatically be treated as a failure—context and evidence matter.*

### Engineering Risk Engine
NEXUS produces deterministic engineering risk scores based on measurable signals. The LLM does not invent the risk score:

```text
raw engineering data ──> metrics ──> anomaly detection ──> ML predictions ──> risk engine ──> risk score + factors ──> AI explanation
```

### AI Analyst
An evidence-backed engineering assistant answering key operational questions. It uses controlled tools (e.g., `get_repository_health`, `get_ci_status`, `search_evidence`) to retrieve structured info without executing arbitrary SQL or raw database writes. Responses always feature supporting evidence and uncertainty metrics.

### Engineering Knowledge (RAG)
Supports retrieval-augmented generation over unstructured documentation like READMEs, runbooks, and architecture docs via vector search (`pgvector`), keeping structured metric queries separate from vector context retrieval.

---

## Architecture

NEXUS is built as a production-shaped modular application:

```text
┌───────────────┐
│    Browser    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Frontend    │
│  HTML/CSS/JS  │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    FastAPI    │
│      API      │
└───────┬───────┘
        │
  ┌─────┼─────────────┐
  │     │             │
  ▼     ▼             ▼
PostgreSQL   Redis    GitHub API
  │     │
  │     ▼
  │   Worker
  │     │
  └─────┴──> Analytics/ML ──> Risk Engine ──> AI Analyst ──> RAG
```

---

## Technology Stack

- **Frontend:** HTML5, CSS3, JavaScript (Minimal, data-dense engineering instrument)
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- **Database:** PostgreSQL (Primary source of truth), `pgvector`
- **Background Tasks:** Redis, Celery/Background workers
- **Machine Learning:** Statistical baselines, Isolation Forest, Logistic Regression, Random Forest
- **AI Engine:** Tool-calling LLM integration
- **Infrastructure:** Docker, AWS ECS, RDS, Redis, S3, CloudWatch, GitHub Actions

---

## Repository Structure

```text
NEXUS/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── models/
│       ├── services/
│       ├── workers/
│       ├── ml/
│       ├── analyst/
│       └── main.py
│
├── frontend/
│   └── public/
│       ├── index.html
│       ├── styles.css
│       └── app.js
│
├── docs/
│   └── NEXUS.md
│
├── tests/
├── infra/
├── .env.example
├── .gitignore
├── AGENTS.md
└── README.md
```

---

## Data Model & Authentication

Engineering activity operates strictly under tenant-isolated workspaces:

```text
User ──> WorkspaceMember ──> Workspace ──> GitHubInstallation ──> Repository
```

**Authentication Flow:**
`Landing Page` ──> `Continue with GitHub` ──> `Create Workspace` ──> `Install GitHub App` ──> `Sync & Analyze` ──> `Dashboard`

---

## Development Roadmap & Status

### Phase Progress
- [x] **Phase 1: Foundation** (Repository structure, FastAPI, DB foundation)
- [/] **Phase 2: Identity & Workspace** (In Progress)
- [ ] **Phase 3: GitHub Integration**
- [ ] **Phase 4: Engineering Intelligence**
- [ ] **Phase 5: Machine Learning Pipeline**
- [ ] **Phase 6: AI Analyst Integration**
- [ ] **Phase 7: Knowledge Layer (RAG)**
- [ ] **Phase 8: Production Deployment (Docker, AWS)**
- [ ] **Phase 9: Product Launch**

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL & Redis
- Git

### Quickstart

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd NEXUS
   ```

2. **Create and activate virtual environment:**
   - **Linux/macOS:**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows:**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Setup environment variables:**
   ```bash
   cp .env.example .env
   # On Windows: Copy-Item .env.example .env
   ```

5. **Run the local development server:**
   ```bash
   uvicorn backend.app.main:app --reload
   ```

---

## Security & Testing

- **Testing:** Uses multi-layered testing strategies including unit tests (metrics, transformations), integration tests (API, Redis, DB), and end-to-end flow validation.
- **Security:** Enforces workspace tenant isolation, strict GitHub App token handling, HMAC webhook signature verification, SQL injection/XSS mitigations, and prompt injection resistance for AI analyst tools.

---

## Contributing & License

NEXUS is currently a personal development project. Changes should follow existing architectural domain constraints. License information will be added prior to public release.
=======
# NEXUS

> Engineering intelligence for software teams.

NEXUS is an AI-powered engineering intelligence platform that turns software development activity into a continuously updated view of engineering health, risk, and operational signals.

It connects to GitHub, ingests engineering activity, computes meaningful metrics, detects anomalies, predicts engineering risks, and provides an evidence-backed AI analyst that can explain what is happening inside a software project.

NEXUS is being built as a production-oriented system from the beginning, with a focus on correctness, explainability, security, and maintainability.

---

## Why NEXUS?

Modern engineering teams generate enormous amounts of data:

- Commits
- Pull requests
- Reviews
- Issues
- CI/CD runs
- Deployments
- Documentation
- Incidents
- Engineering metrics

Most of this information is scattered across different tools.

NEXUS brings these signals together and answers questions such as:

- How healthy is this repository?
- Is engineering velocity improving or degrading?
- Which repositories are showing unusual behavior?
- Which pull requests are likely to become risky?
- Is CI reliability getting worse?
- Are deployments becoming more failure-prone?
- Why did the engineering risk score change?
- What evidence supports this conclusion?
- What should the engineering team investigate next?

The goal is not to create another dashboard full of charts. The goal is to create an engineering intelligence layer.

---

## Core Capabilities

### GitHub Integration
Connect a GitHub organization or account and allow NEXUS to access selected repositories through a GitHub App. NEXUS ingests engineering activity such as repositories, commits, pull requests, reviews, issues, workflow runs, and deployments. GitHub webhooks keep repository data continuously synchronized.

### Engineering Metrics
NEXUS calculates engineering metrics across configurable time windows, stored as historical snapshots to reason about trends over time:
- Pull request cycle time & throughput
- Review latency & PR size
- Commit frequency
- CI success and failure rates
- Deployment frequency & failure rates
- Issue resolution time

### Anomaly Detection
NEXUS identifies unusual engineering behavior using statistical and machine-learning techniques (e.g., sudden drop in deployment frequency, abnormal review latency, spike in CI failures).

```text
normal variation ──> statistical anomaly ──> engineering signal ──> potential risk
```

*An anomaly will never automatically be treated as a failure—context and evidence matter.*

### Engineering Risk Engine
NEXUS produces deterministic engineering risk scores based on measurable signals. The LLM does not invent the risk score:

```text
raw engineering data ──> metrics ──> anomaly detection ──> ML predictions ──> risk engine ──> risk score + factors ──> AI explanation
```

### AI Analyst
An evidence-backed engineering assistant answering key operational questions. It uses controlled tools (e.g., `get_repository_health`, `get_ci_status`, `search_evidence`) to retrieve structured info without executing arbitrary SQL or raw database writes. Responses always feature supporting evidence and uncertainty metrics.

### Engineering Knowledge (RAG)
Supports retrieval-augmented generation over unstructured documentation like READMEs, runbooks, and architecture docs via vector search (`pgvector`), keeping structured metric queries separate from vector context retrieval.

---

## Architecture

NEXUS is built as a production-shaped modular application:

```text
┌───────────────┐
│    Browser    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Frontend    │
│  HTML/CSS/JS  │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│    FastAPI    │
│      API      │
└───────┬───────┘
        │
  ┌─────┼─────────────┐
  │     │             │
  ▼     ▼             ▼
PostgreSQL   Redis    GitHub API
  │     │
  │     ▼
  │   Worker
  │     │
  └─────┴──> Analytics/ML ──> Risk Engine ──> AI Analyst ──> RAG
```

---

## Technology Stack

- **Frontend:** HTML5, CSS3, JavaScript (Minimal, data-dense engineering instrument)
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- **Database:** PostgreSQL (Primary source of truth), `pgvector`
- **Background Tasks:** Redis, Celery/Background workers
- **Machine Learning:** Statistical baselines, Isolation Forest, Logistic Regression, Random Forest
- **AI Engine:** Tool-calling LLM integration
- **Infrastructure:** Docker, AWS ECS, RDS, Redis, S3, CloudWatch, GitHub Actions

---

## Repository Structure

```text
NEXUS/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── models/
│       ├── services/
│       ├── workers/
│       ├── ml/
│       ├── analyst/
│       └── main.py
│
├── frontend/
│   └── public/
│       ├── index.html
│       ├── styles.css
│       └── app.js
│
├── docs/
│   └── NEXUS.md
│
├── tests/
├── infra/
├── .env.example
├── .gitignore
├── AGENTS.md
└── README.md
```

---

## Data Model & Authentication

Engineering activity operates strictly under tenant-isolated workspaces:

```text
User ──> WorkspaceMember ──> Workspace ──> GitHubInstallation ──> Repository
```

**Authentication Flow:**
`Landing Page` ──> `Continue with GitHub` ──> `Create Workspace` ──> `Install GitHub App` ──> `Sync & Analyze` ──> `Dashboard`

---

## Development Roadmap & Status

### Phase Progress
- [x] **Phase 1: Foundation** (Repository structure, FastAPI, DB foundation)
- [/] **Phase 2: Identity & Workspace** (In Progress)
- [ ] **Phase 3: GitHub Integration**
- [ ] **Phase 4: Engineering Intelligence**
- [ ] **Phase 5: Machine Learning Pipeline**
- [ ] **Phase 6: AI Analyst Integration**
- [ ] **Phase 7: Knowledge Layer (RAG)**
- [ ] **Phase 8: Production Deployment (Docker, AWS)**
- [ ] **Phase 9: Product Launch**

---

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL & Redis
- Git

### Quickstart

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd NEXUS
   ```

2. **Create and activate virtual environment:**
   - **Linux/macOS:**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows:**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Setup environment variables:**
   ```bash
   cp .env.example .env
   # On Windows: Copy-Item .env.example .env
   ```

5. **Run the local development server:**
   ```bash
   uvicorn backend.app.main:app --reload
   ```

---

## Security & Testing

- **Testing:** Uses multi-layered testing strategies including unit tests (metrics, transformations), integration tests (API, Redis, DB), and end-to-end flow validation.
- **Security:** Enforces workspace tenant isolation, strict GitHub App token handling, HMAC webhook signature verification, SQL injection/XSS mitigations, and prompt injection resistance for AI analyst tools.

---

## Contributing & License

NEXUS is currently a personal development project. Changes should follow existing architectural domain constraints. License information will be added prior to public release.
>>>>>>> 2ba0931b82d1f4baee0e1a0b1eef4c452b689be0
