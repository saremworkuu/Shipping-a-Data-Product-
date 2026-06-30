from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .schemas import HealthResponse

app = FastAPI(title="Medical Telegram Warehouse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="healthy", message="Medical Telegram Warehouse API")


@app.get("/health")
async def health():
    return {"status": "ok"}
