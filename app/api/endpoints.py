from app.core.agent import Me
from app.core.models import ChatRequest, ChatResponse
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)
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
async def record_user_details_endpoint(request: Request):
    try:
        raw_body = await request.json()
        logger.info("RAW BODY recibido: %s", raw_body)

        if "arguments" in raw_body and isinstance(raw_body["arguments"], str):
            parsed_args = json.loads(raw_body["arguments"])
        else:
            parsed_args = raw_body

        logger.info("Parsed arguments: %s", parsed_args)

        request_model = UserDetailsRequest(**parsed_args)

        result = agent._record_user_details(
            email=request_model.email,
            name=request_model.name,
            notes=request_model.notes
        )
        logger.info("record_user_details result: %s", result)
        return {"status": "ok", "data": result}

    except Exception as e:
        logger.exception("Error en record_user_details")
        raise HTTPException(
            status_code=500,
            detail=f"Error registrando usuario: {str(e)}"
        )


@router.post("/record_unknown_question")
async def record_unknown_question_endpoint(request: Request):
    try:
        raw_body = await request.json()
        logger.info("RAW BODY recibido: %s", raw_body)

        if "arguments" in raw_body and isinstance(raw_body["arguments"], str):
            parsed_args = json.loads(raw_body["arguments"])
        else:
            parsed_args = raw_body

        logger.info("Parsed arguments: %s", parsed_args)

        request_model = UnknownQuestionRequest(**parsed_args)

        result = agent._record_unknown_question(
            question=request_model.question
        )
        logger.info("record_unknown_question result: %s", result)
        return {"status": "ok", "data": result}

    except Exception as e:
        logger.exception("Error en record_unknown_question")
        raise HTTPException(
            status_code=500,
            detail=f"Error registrando pregunta: {str(e)}"
        )
