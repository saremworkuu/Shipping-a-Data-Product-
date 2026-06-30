# Medical Telegram Warehouse

A medical data warehouse system with Telegram bot integration, built with FastAPI, dbt, and PostgreSQL.

## Project Structure

```
medical-telegram-warehouse/
├── .vscode/                    # VS Code settings
├── .github/workflows/          # CI/CD workflows
├── data/                       # Data files
├── medical_warehouse/          # dbt project
│   ├── models/
│   │   ├── staging/           # Staging models
│   │   └── marts/             # Mart models
│   └── tests/                 # dbt tests
├── src/                        # Source code
├── api/                        # FastAPI application
│   ├── main.py                # FastAPI app
│   ├── database.py            # Database connection
│   └── schemas.py             # Pydantic models
├── notebooks/                  # Jupyter notebooks
├── tests/                      # Unit tests
└── scripts/                    # Utility scripts
```

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your secrets
3. Build and run with Docker:
   ```bash
   docker-compose up --build
   ```

## API

The API will be available at `http://localhost:8000`

## dbt

Run dbt transformations:
```bash
cd medical_warehouse
dbt run
dbt test
```

## Testing

Run unit tests:
```bash
pytest tests/
```
