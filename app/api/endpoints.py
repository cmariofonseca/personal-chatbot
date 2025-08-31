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
    logger.info("record_user_details raw payload: %s", json.dumps(request, indent=2))
    
    try:
        parsed_args = extract_arguments_from_request(request)
        validate_required_field(parsed_args, "email")
        
        request_model = UserDetailsRequest(**parsed_args)
        result = agent._record_user_details(
            email=request_model.email,
            name=request_model.name,
            notes=request_model.notes
        )
        logger.info("record_user_details result: %s", result)
        
        return {"status": "ok", "data": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en record_user_details")
        raise HTTPException(status_code=500, detail=f"Error registrando usuario: {str(e)}")

@router.post("/record_unknown_question")
async def record_unknown_question_endpoint(request: dict):
    logger.info("record_unknown_question raw payload: %s", json.dumps(request, indent=2))
    
    try:
        parsed_args = extract_arguments_from_request(request)
        validate_required_field(parsed_args, "question")
        
        request_model = UnknownQuestionRequest(**parsed_args)
        result = agent._record_unknown_question(question=request_model.question)
        logger.info("record_unknown_question result: %s", result)
        
        return {"status": "ok", "data": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en record_unknown_question")
        raise HTTPException(status_code=500, detail=f"Error registrando pregunta: {str(e)}")

def extract_arguments_from_request(request: dict) -> dict:
    """Extrae arguments de diferentes estructuras de Vapi"""
    if not isinstance(request, dict):
        return {}
    
    # 1. PRIORIDAD: Estructura REAL de Vapi (según logs)
    if "toolCalls" in request and request["toolCalls"]:
        return extract_from_tool_calls(request["toolCalls"])
    
    # 2. Alternativa: toolCallList (por si acaso)
    if "toolCallList" in request and request["toolCallList"]:
        return extract_from_tool_calls(request["toolCallList"])
    
    # 3. Estructura con arguments directos (backup)
    if "arguments" in request:
        return extract_from_arguments(request["arguments"])
    
    # 4. Ya viene con los campos necesarios
    if "question" in request or "email" in request:
        return request
    
    return {}

def extract_from_tool_calls(tool_calls: list) -> dict:
    """Extrae arguments de toolCalls de Vapi"""
    if not tool_calls or not isinstance(tool_calls, list):
        return {}
    
    # Tomar el primer tool call
    tool_call = tool_calls[0]
    
    # Estructura esperada de Vapi:
    # toolCall = {
    #     "function": {
    #         "name": "record_user_details", 
    #         "arguments": "{\"email\": \"test@example.com\"}"
    #     }
    # }
    
    if (isinstance(tool_call, dict) and 
        "function" in tool_call and 
        isinstance(tool_call["function"], dict) and
        "arguments" in tool_call["function"]):
        
        arguments_data = tool_call["function"]["arguments"]
        return parse_json_arguments(arguments_data)
    
    return {}

def extract_from_arguments(arguments_data) -> dict:
    """Extrae arguments del campo arguments"""
    if isinstance(arguments_data, str):
        return parse_json_arguments(arguments_data)
    elif isinstance(arguments_data, dict):
        return arguments_data
    return {}

def extract_from_message(message_data) -> dict:
    """Extrae arguments del campo message"""
    if not isinstance(message_data, dict):
        return {}
    
    if "content" in message_data:
        content = message_data["content"]
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"question": content}
    
    return message_data

def parse_json_arguments(arguments_str: str) -> dict:
    """Parse JSON arguments de forma segura"""
    try:
        return json.loads(arguments_str)
    except (json.JSONDecodeError, TypeError):
        return {}

def validate_required_field(data: dict, field_name: str):
    """Valida que el campo requerido esté presente"""
    if not data or field_name not in data:
        available_keys = list(data.keys()) if isinstance(data, dict) else []
        logger.warning("Field %s required. Available keys: %s", field_name, available_keys)
        raise HTTPException(
            status_code=400, 
            detail=f"{field_name.capitalize()} field is required. Available keys: {available_keys}"
        )
