# Poker SaaS - Hand Analyzer & Scenario Simulator

A comprehensive poker analysis platform featuring GTO-based hand analysis and scenario simulation.

## Project Structure

```
Poker_analysis/
├── backend/           # FastAPI Python backend
├── frontend/          # React + Tailwind (future)
└── README.md
```

## Quick Start

### Backend Setup

```bash
cd backend
source venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### API Documentation

Once running, visit: http://localhost:8000/docs

## Features

- **Pre-flop Equity Calculator**: Calculate winning percentages between hands
- **Scenario Simulator** (coming soon): Visual poker table interface
- **Hand Analyzer** (coming soon): AI-powered hand history analysis"
