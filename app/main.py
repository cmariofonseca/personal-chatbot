from app.api.endpoints import router as api_router
from app.config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    description="API para el chatbot personalizado de Carlos Fonseca",
    title="personal-chatbot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://carlosfonseca.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Chatbot API está funcionando"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}