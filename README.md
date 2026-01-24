# NL2SQL Pipeline

This is a modular implementation of a Natural Language to SQL pipeline based on the provided High-Level Design.

## Architecture

- **Framework**: FastAPI
- **Orchestration**: LangGraph
- **Modules**:
  - Schema Understanding
  - Preprocessing
  - Intent Classification
  - SQL Generation
  - Validation & Repair

## Setup

1. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python -m uvicorn app.main:app --reload --port 8080
   ```

3. Access the API documentation at `http://localhost:8080/docs`.
4. 

## Usage

Send a POST request to `/api/v1/query`:

```json
{
  "query": "Show me all users"
}
```

## Configuration

Configure the application using environment variables or a `.env` file. See `app/core/config.py` for available settings.
