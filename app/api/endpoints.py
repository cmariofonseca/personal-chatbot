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
    logger.info("🔥 FULL REQUEST RECEIVED: %s", json.dumps(request, indent=2, default=str))
    
    try:
        parsed_args = extract_arguments_from_request(request)
        logger.info("📦 PARSED ARGS: %s", json.dumps(parsed_args, indent=2))
        result = validate_required_field(parsed_args, "email")
        logger.warning("logger warning de result en record_user_details_endpoint: %s", result)
        logger.info("logger info de result en record_user_details_endpoint: %s", result)
        
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
    logger.info("🔥 FULL REQUEST RECEIVED: %s", json.dumps(request, indent=2, default=str))
    
    try:
        parsed_args = extract_arguments_from_request(request)
        logger.info("📦 PARSED ARGS: %s", json.dumps(parsed_args, indent=2))
        result = validate_required_field(parsed_args, "question")
        logger.warning("logger warning de result en record_unknown_question_endpoint: %s", result)
        logger.info("logger info de result en record_unknown_question_endpoint: %s", result)
        
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
    logger.warning("Se llama la funcion: extract_arguments_from_request")
    logger.info("🔄 EXTRACTING FROM REQUEST STRUCTURE")
    
    if not isinstance(request, dict):
        logger.warning("❌ Request is not a dict: %s", type(request))
        return {}
    
    # 1. Mostrar TODAS las keys del request principal
    logger.info("📋 TOP-LEVEL KEYS AND VALUES:")
    for key, value in request.items():
        logger.info("   %s: %s", key, type(value))
        if isinstance(value, (list, dict)) and value:
            logger.info("   %s content: %s", key, json.dumps(value, indent=2, default=str)[:200] + "...")
    
    # 5. Estructura con message
    if "message" in request:
        return extract_from_message(request["message"])
    
    return {}

def extract_from_message(message_data) -> dict:
    """Extrae arguments del campo message"""
    logger.warning("Se llama la funcion: extract_from_message")
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

def validate_required_field(data: dict, field_name: str):
    """Valida que el campo requerido esté presente"""
    logger.warning("Se llama la funcion: validate_required_field")
    if not data or field_name not in data:
        available_keys = list(data.keys()) if isinstance(data, dict) else []
        # log 1
        logger.warning("Field %s required. Available keys: %s", field_name, available_keys)
        
        # DETECTAMOS SI ES UN REQUEST DE VAPI
        vapi_keys = ['timestamp', 'type', 'toolCalls', 'toolCallList', 'toolWithToolCallList', 'artifact', 'call', 'assistant']
        if any(key in available_keys for key in vapi_keys):
            # ¡ES UN REQUEST DE VAPI! Extraemos los arguments
            extracted_args = extract_from_vapi_request(data)
            # log 3
            logger.warning("Extracted arguments from Vapi request: %s", extracted_args)
            logger.warning("Extracted arguments from Vapi es de tipo: %s", type(extracted_args))
            
            if field_name in extracted_args:
                # Devolvemos los arguments extraídos para que el caller los use
                return extracted_args[field_name]
        
        raise HTTPException(
            status_code=400, 
            detail=f"{field_name.capitalize()} field is required. Available keys: {available_keys}"
        )
    
    # Si el campo está presente, devolver su valor
    return data[field_name]

def extract_from_vapi_request(vapi_request: dict) -> dict:
    """Extrae arguments directamente del request completo de Vapi"""
    try:
        tool_calls = vapi_request["toolCalls"]
        function_data = tool_calls[0]["function"]
        arguments_str = function_data["arguments"]
        # log 2
        logger.warning("Failed to parse arguments: %s", arguments_str)
        logger.warning("Failed to parse arguments es de tipo: %s", type(arguments_str))
        return arguments_str
    except (json.JSONDecodeError, TypeError):
        return {}
