from app.config.settings import settings
from app.utils.push_notify import push_notification
from openai import OpenAI
from pathlib import Path
from pypdf import PdfReader
from typing import List, Dict
import httpx
import json

class Me:
    # Inicializa el agente cargando configuración, CV y resumen
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent.parent

        # Definir rutas de datos
        projects_path = base_dir / "data" / "projects" / "projects.json"
        cv_path = base_dir / "data" / "cvs" / "cv-carlos-fonseca-2025-es.pdf"
        summary_path = base_dir / "data" / "summaries" / "summary-es.txt"
        
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,  
            base_url="https://api.deepseek.com"
        )
        
        # Datos del perfil
        self.name = "Carlos Fonseca"
        self.projects = self._load_projects(projects_path)
        self.cv = self._load_cv(cv_path)
        self.summary = self._load_summary(summary_path)

    # Carga y convierte el contenido JSON de un archivo en un objeto de Python.
    def _load_projects(self, path: Path) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    # Carga y extrae texto del CV en formato PDF
    def _load_cv(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Archivo CV no encontrado en: {path}")
        
        cv_text = []
        reader = PdfReader(path)
        for page in reader.pages:
            if text := page.extract_text():
                cv_text.append(text)
        return "\n".join(cv_text)

    # Lee y valida el contenido del archivo de resumen
    def _load_summary(self, path: Path) -> str:
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError("El archivo summary está vacío")
        return content

    # Maneja las llamadas a herramientas/funciones de OpenAI
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

    # Registra detalles de usuarios interesados y envía notificación
    def _record_user_details(self, email: str, name: str = "Nombre no indicado", notes: str = "no proporcionadas") -> Dict:
        push_notification(f"Registrando {name} con email {email} y notas {notes}")
        return {"recorded": "ok"}

    # Registra preguntas no respondidas y envía notificación
    def _record_unknown_question(self, question: str) -> Dict:
        push_notification(f"Registrando pregunta no respondida: {question}")
        return {"recorded": "ok"}

    # Genera el prompt del sistema con instrucciones para el AI
    def system_prompt(self) -> str:
        projects_str = "\n".join(
            f"- {p['projectName']} ({p['date']}) – {p['description']}" for p in self.projects
        )

        return (
            f"Eres Carlos Fonseca, ingeniero de sistemas con más de 10 años de experiencia en desarrollo de software. "
            f"Tu tarea es responder de forma clara, breve y profesional a preguntas sobre tu experiencia laboral, habilidades, herramientas y proyectos. "
            f"Habla con el usuario como si fuera un posible cliente o reclutador. "
            f"Si no sabes algo, registra la pregunta con 'record_unknown_question'. "
            f"Si el usuario muestra interés, invítalo a dejar su correo y registra con 'record_user_details'."
            f"\n\nResumen profesional:\n{self.summary}"
            f"\n\nProyectos destacados:\n{projects_str}"
            f"\n\nCV (extraído de PDF):\n{self.cv}"
        )

    # Procesa mensajes del chat y maneja la conversación con OpenAI
    def chat(self, message: str, history: List[Dict] = None) -> str:
        history = history or []

        # Construcción de mensajes base
        messages = [{"role": "system", "content": self.system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        while True:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=self._get_tools(),
                max_tokens=400,
                temperature=0.5,
            )

            choice = response.choices[0]
            finish_reason = choice.finish_reason

            if finish_reason == "tool_calls":
                tool_calls = choice.message.tool_calls
                messages.append(choice.message)
                messages.extend(self.handle_tool_call(tool_calls))
            else:
                return choice.message.content


    # Devuelve una lista de herramientas que el agente puede usar.
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
        