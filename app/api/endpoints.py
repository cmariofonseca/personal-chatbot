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
    logger.warning("request received in record_user_details_endpoint: %s", json.dumps(request, indent=2, default=str))

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
    logger.warning("request received in record_unknown_question_endpoint: %s", json.dumps(request, indent=2, default=str))
    
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
        arguments_data = function_data["arguments"]
        
        if "email" in arguments_data and isinstance(arguments_data["email"], str):
            email = arguments_data["email"]
            email_clean = email.strip().lower().replace(" ", "")
            arguments_data["email"] = email_clean
            
        return arguments_data
        
    except (KeyError, IndexError, TypeError) as e:
        logger.warning("Error extracting from Vapi request: %s", str(e))
        return {}
