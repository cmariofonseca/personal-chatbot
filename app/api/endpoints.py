from app.core.agent import Me
from app.core.models import ChatRequest, ChatResponse
from fastapi import APIRouter, HTTPException
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
async def record_user_details_endpoint(request: dict):
    # logger.warning("request received in record_user_details_endpoint: %s", json.dumps(request, indent=2, default=str))

    try:
        tool_calls = request.get("message", {}).get("toolCalls", [])
        
        if not tool_calls:
            raise HTTPException(status_code=400, detail="No toolCalls found in request")

        first_tool_call = tool_calls[0]
        arguments_data = first_tool_call.get("function", {}).get("arguments", {})
        
        if (isinstance(arguments_data, dict) and 
            "email" in arguments_data and 
            isinstance(arguments_data["email"], str)):
            
            email = arguments_data["email"]
            arguments_data["email"] = email.strip().lower().replace(" ", "")

        request_model = UserDetailsRequest(**arguments_data)
        
        email = request_model.email
        name = request_model.name
        notes = request_model.notes
        logger.warning("email: %s, name: %s, notes: %s", email, name, notes)

        agent._record_user_details(email, name, notes)
        return {"status": "ok"}

    except Exception as e:
        logger.exception("Error en record_user_details")
        raise HTTPException(
            status_code=500,
            detail=f"Error registrando usuario: {str(e)}"
        )
        
@router.post("/record_unknown_question")
async def record_unknown_question_endpoint(request: dict):
    # logger.warning("request received in record_unknown_question_endpoint: %s", json.dumps(request, indent=2, default=str))
    
    try:
        tool_calls = request.get("message", {}).get("toolCalls", [])
        
        if not tool_calls:
            raise HTTPException(status_code=400, detail="No toolCalls found in request")

        first_tool_call = tool_calls[0]
        arguments_data = first_tool_call.get("function", {}).get("arguments", {})

        request_model = UnknownQuestionRequest(**arguments_data)

        question = request_model.question
        logger.warning("record_unknown_question result: %s", question)
        agent._record_unknown_question(question)
        return {"status": "ok"}

    except Exception as e:
        logger.exception("Error en record_unknown_question")
        raise HTTPException(
            status_code=500,
            detail=f"Error registrando pregunta: {str(e)}"
        )

# Diccionario recibido desde Vapi
""" {
  "message": {
    "timestamp": 1756661121974,
    "type": "tool-calls",
    "toolCalls": [
      {
        "id": "call_7SVi7lI1KRxWoQPLI9zs1klQ",
        "type": "function",
        "function": {
          "name": "record_user_details",
          "arguments": {
            "name": "Alberto Ruiz",
            "email": "AlbertoRuiz@gmail.com"
          }
        }
      }
    ],
  "toolCallList": [],
  "toolWithToolCallList": [],
  "artifact": {},
  "call": {},
  "assistant": {}
  }
} """
