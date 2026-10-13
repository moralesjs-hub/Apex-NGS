# Apex-NGS

NFL Next Gen Stats (NGS) Scouting & Efficiency Intelligence Engine. Analyzes tracking metrics, computes custom efficiency scores, and generates automated scouting dossiers powered by Gemini fallback inference.

## Tech Stack
- **Language:** Python 3.11
- **Database:** PostgreSQL 16 with `pgvector`
- **Containerization:** Docker & Docker Compose
- **Core Libraries:** SQLAlchemy, Pandas

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### 1. Environment Setup
Copy the example environment file and fill in your keys:
```bash
cp .env.example .env
```

### 2. Run Database & Services
```bash
docker compose up -d
```

### 3. Seed Data
```bash
python seed_index.py
```

### 4. Run Application
```bash
python app.py
```
