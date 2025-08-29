from app.core.agent import Me
from app.core.models import ChatRequest, ChatResponse
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
agent = Me()
class UserDetailsRequest(BaseModel):
    email: str
    name: Optional[str] = "Nombre no indicado"
    notes: Optional[str] = "no proporcionadas"

class UnknownQuestionRequest(BaseModel):
    question: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response_text = agent.chat(
            message=request.message,
            history=request.history or []
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en el chatbot: {str(e)}"
        )

@router.post("/record_user_details")
async def record_user_details_endpoint(request: UserDetailsRequest):
    try:
        result = agent._record_user_details(
            email=request.email,
            name=request.name,
            notes=request.notes
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error registrando usuario: {str(e)}"
        )

@router.post("/record_unknown_question")
async def record_unknown_question_endpoint(request: UnknownQuestionRequest):
    try:
        result = agent._record_unknown_question(
            question=request.question
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error registrando pregunta: {str(e)}"
        )
