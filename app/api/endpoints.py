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
    logger.info("🔥 FULL REQUEST RECEIVED: %s", json.dumps(request, indent=2, default=str))
    
    try:
        parsed_args = extract_arguments_from_request(request)
        logger.info("📦 PARSED ARGS: %s", json.dumps(parsed_args, indent=2))
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
    
    # 2. Buscar en toolCalls
    if "toolCalls" in request:
        logger.info("🔍 Found toolCalls: %s", request["toolCalls"])
        result = extract_from_tool_calls(request["toolCalls"])
        logger.info("📦 Extracted from toolCalls: %s", result)
        return result
    
    # 3. Buscar en toolCallList  
    if "toolCallList" in request:
        logger.info("🔍 Found toolCallList: %s", request["toolCallList"])
        result = extract_from_tool_calls(request["toolCallList"])
        logger.info("📦 Extracted from toolCallList: %s", result)
        return result
    
    # 4. Estructura con arguments directos
    if "arguments" in request:
        return extract_from_arguments(request["arguments"])
    
    # 5. Estructura con message
    if "message" in request:
        return extract_from_message(request["message"])
    
    # 6. Ya viene con los campos necesarios
    if "question" in request:
        return request
    
    return {}

def extract_from_tool_calls(tool_calls: list) -> dict:
    """Extrae arguments de toolCalls"""
    if not tool_calls or not isinstance(tool_calls, list):
        return {}
    
    tool_call = tool_calls[0]
    if isinstance(tool_call, dict) and "function" in tool_call:
        function_data = tool_call["function"]
        if isinstance(function_data, dict) and "arguments" in function_data:
            return parse_json_arguments(function_data["arguments"])
    
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
        
        # DETECTAMOS SI ES UN REQUEST DE VAPI
        vapi_keys = ['timestamp', 'type', 'toolCalls', 'toolCallList', 'toolWithToolCallList', 'artifact', 'call', 'assistant']
        if any(key in available_keys for key in vapi_keys):
            # ¡ES UN REQUEST DE VAPI! Extraemos los arguments
            extracted_args = extract_from_vapi_request(data)
            logger.warning("Extracted arguments from Vapi request: %s", extracted_args)
            
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
    # Intentar extraer de toolCalls primero
    result = extract_from_tool_calls_field(vapi_request, "toolCalls")
    if result:
        return result
    
    # Intentar de toolCallList si toolCalls no funcionó
    result = extract_from_tool_calls_field(vapi_request, "toolCallList")
    if result:
        return result
    
    # Si no encontramos nada, devolver vacío
    return {}

def extract_from_tool_calls_field(vapi_request: dict, field_name: str) -> dict:
    """Extrae arguments de un campo específico de tool calls"""
    if field_name not in vapi_request or not vapi_request[field_name]:
        return {}
    
    tool_calls = vapi_request[field_name]
    if not isinstance(tool_calls, list) or not tool_calls:
        return {}
    
    return extract_from_single_tool_call(tool_calls[0])

def extract_from_single_tool_call(tool_call: dict) -> dict:
    """Extrae arguments de un solo tool call"""
    if not isinstance(tool_call, dict) or "function" not in tool_call:
        return {}
    
    function_data = tool_call["function"]
    if not isinstance(function_data, dict) or "arguments" not in function_data:
        return {}
    
    arguments_data = function_data["arguments"]
    logger.info("Arguments data type: %s, value: %s", type(arguments_data), arguments_data)
    
    return parse_arguments_string(arguments_data)

def parse_arguments_string(arguments_data) -> dict:
    """Parse arguments que pueden ser string JSON o ya un dict"""
    try:
        if isinstance(arguments_data, str):
            # Es un string JSON: '{"email": "test@example.com"}'
            return json.loads(arguments_data)
        elif isinstance(arguments_data, dict):
            # Ya es un diccionario: {'email': 'test@example.com'}
            return arguments_data
        else:
            logger.warning("Unknown arguments type: %s - %s", type(arguments_data), arguments_data)
            return {}
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse arguments: %s - Error: %s", arguments_data, str(e))
        return {}
