from app.config.settings import settings
from app.utils.push_notify import push_notification
from openai import OpenAI
from pathlib import Path
from pypdf import PdfReader
from typing import List, Dict
import httpx
import json

class Me:
    def __init__(self):
        # Obtener ruta base de manera más confiable
        base_dir = Path(__file__).resolve().parent.parent.parent
        cv_path = base_dir / "data" / "cvs" / "cv-carlos-fonseca-2025-es.pdf"
        summary_path = base_dir / "data" / "summaries" / "summary-es.txt"
        
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.name = "Carlos Fonseca"
        self.cv = self._load_cv(cv_path)
        self.summary = self._load_summary(summary_path)

    def _load_cv(self, path: Path) -> str:  # Cambiado a Path en el type hint
        if not path.exists():
            raise FileNotFoundError(f"Archivo CV no encontrado en: {path}")
        
        cv_text = []
        reader = PdfReader(path)
        for page in reader.pages:
            if text := page.extract_text():  # Usando walrus operator
                cv_text.append(text)
        return "\n".join(cv_text)  # Más eficiente que concatenar strings

    def _load_summary(self, path: Path) -> str:
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError("El archivo summary está vacío")
        return content


    def handle_tool_call(self, tool_calls: List) -> List[Dict]:
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if tool_name == "record_user_details":
                result = self._record_user_details(**arguments)
            elif tool_name == "record_unknown_question":
                result = self._record_unknown_question(**arguments)
            else:
                result = {}
                
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results

    def _record_user_details(self, email: str, name: str = "Nombre no indicado", notes: str = "no proporcionadas") -> Dict:
        push_notification(f"Registrando {name} con email {email} y notas {notes}")
        return {"recorded": "ok"}

    def _record_unknown_question(self, question: str) -> Dict:
        push_notification(f"Registrando pregunta no respondida: {question}")
        return {"recorded": "ok"}

    def system_prompt(self) -> str:
        system_prompt = f"""Actúa como {self.name}. Responde preguntas en el sitio web de {self.name}, en particular preguntas relacionadas con la trayectoria profesional, los antecedentes, las habilidades y la experiencia de {self.name}.
            Tu responsabilidad es representar a {self.name} en las interacciones del sitio web con la mayor fidelidad posible.
            Se te proporciona un resumen de la trayectoria profesional y el curriculum vitae de {self.name} que puedes usar para responder preguntas.
            Muestra un tono profesional y atractivo, como si hablaras con un cliente potencial o un futuro empleador que haya visitado el sitio web.
            Si no sabes la respuesta a alguna pregunta, usa la herramienta 'record_unknown_question' para registrar la pregunta que no pudiste responder, incluso si se trata de algo trivial o no relacionado con tu trayectoria profesional.
            Si el usuario participa en una conversación, intenta que se ponga en contacto por correo electrónico; pídele su correo electrónico, su nombre y regístralo con la herramienta 'record_user_details'."""
        
        system_prompt += f"\n\n## Resumen:\n{self.summary}\n\n## Perfil de LinkedIn:\n{self.cv}\n\n"
        system_prompt += f"En este contexto, por favor chatea con el usuario, manteniéndote siempre en el personaje de {self.name}."
        return system_prompt

    def chat(self, message: str, history: List[Dict] = None) -> str:
        history = history or []
        messages = [{"role": "system", "content": self.system_prompt()}] 
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=self._get_tools()
            )
            
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
                
        return response.choices[0].message.content

    def _get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "record_user_details",
                    "description": "Registra datos de usuarios interesados",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string"},
                            "name": {"type": "string"},
                            "notes": {"type": "string"}
                        },
                        "required": ["email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "record_unknown_question",
                    "description": "Registra preguntas no respondidas",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"}
                        },
                        "required": ["question"]
                    }
                }
            }
        ]
        