import os
os.environ['MOCK_LLM'] = '1'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine
from app.models.database import Base
from app.api import documents
from app.api import relationships
from app.api import facts

from sqlalchemy import text

# Create tables
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fact Knowledge Layer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(relationships.router, prefix="/api/relationships", tags=["relationships"])
app.include_router(facts.router, prefix="/api/facts", tags=["facts"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Fact Knowledge Layer API"}
