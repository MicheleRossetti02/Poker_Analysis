# Poker SaaS Backend

FastAPI backend for poker analysis.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

- `POST /api/equity/preflop` - Calculate pre-flop equity between two hands
- `GET /docs` - Swagger API documentation
