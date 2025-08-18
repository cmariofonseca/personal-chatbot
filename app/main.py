from .api.endpoints import router as api_router
from .config.settings import settings
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="personal-chatbot",
    description="API para el chatbot personalizado de Carlos Fonseca",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Chatbot API está funcionando"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}