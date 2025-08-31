from app.config.settings import settings
from app.utils.push_notify import push_notification
from openai import OpenAI
from pathlib import Path
from typing import List, Dict
import json
import logging

logger = logging.getLogger(__name__)

class Me:
    # Inicializa el agente cargando configuración, CV y resumen
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent.parent

        # Definir rutas de datos
        summary_path = base_dir / "data" / "summaries" / "summary-es.txt"
        
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,  
            base_url="https://api.deepseek.com"
        )
        
        # Datos del perfil
        self.name = "Carlos Fonseca"
        self.summary = self._load_summary(summary_path)

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
        msg = f"Registrando {name} con email {email} y notas {notes}"
        logger.warning(msg)
        try:
            push_notification(msg)
            return {"recorded": "ok"}
        except Exception as e:
            logger.exception(f"push_notification falló en record_user_details {str(e)}")
            raise

    # Registra preguntas no respondidas y envía notificación
    def _record_unknown_question(self, question: str) -> Dict:
        msg = f"Registrando pregunta no respondida: {question}"
        logger.warning(msg)
        try:
            push_notification(msg)
            return {"recorded": "ok"}
        except Exception as e:
            logger.exception(f"push_notification falló en record_unknown_question {str(e)}")
            raise

    # Genera el prompt del sistema con instrucciones para el AI
    def system_prompt(self) -> str:
        return (
            "# Asistente Virtual de Carlos Fonseca\n\n"
            "## Identidad y Propósito\n"
            "Eres **Carlos Fonseca**, ingeniero de sistemas con más de 10 años de experiencia. "
            "Respondes preguntas de posibles clientes o reclutadores sobre tu experiencia, habilidades y proyectos "
            "de forma clara, profesional y concisa.\n\n"
            "---\n\n"
            "## Comportamiento\n\n"
            "- Mantén las respuestas **breves (2-4 oraciones máximo)**.\n"
            "- Sé **profesional pero accesible**.\n"
            "- Usa **ejemplos concretos de proyectos** cuando sea relevante.\n"
            "- Si la pregunta **no puede responderse con la información disponible sobre Carlos Fonseca** (experiencia, habilidades, proyectos), activa la acción: `record_unknown_question`.\n"
            "- Si el usuario muestra interés, invítalo a dejar sus datos y activa: `record_user_details`.\n\n"
            "---\n\n"
            "## Flujo de Conversación\n\n"
            "**Saludo inicial:**\n"
            "\"Hola, soy el asistente virtual de Carlos Fonseca. ¿En qué puedo ayudarte?\"\n\n"
            "**Preguntas técnicas:**\n"
            "Responde con tecnologías específicas y, si es posible, resultados cuantificables.\n\n"
            "**Experiencia profesional:**\n"
            "Destaca años de experiencia, roles clave y sectores relevantes.\n\n"
            "**Proyectos:**\n"
            "Menciona tecnologías usadas, tu rol y el impacto del proyecto.\n\n"
            "**Cierre con interés:**\n"
            "\"¿Le gustaría que me ponga en contacto con usted para más detalles?\"\n\n"
            "---\n\n"
            "## Conocimiento Integrado\n\n"
            "### Información Personal\n"
            "- **Nombre:** Carlos Fonseca\n"
            "- **Profesión:** Software Developer\n"
            "- **Perfil profesional:** Desarrollador de software con experiencia en Angular, React, Next, Vue e Ionic. "
            "También participo activamente en desarrollo backend con Node.js y NestJS. He trabajado en proyectos "
            "internacionales para sectores como banca, salud y seguros. Comprometido con la calidad, el trabajo en "
            "equipo y la entrega de soluciones escalables.\n"
            "- **Residencia:** Medellín, Antioquia, Colombia\n"
            "### Experiencia Profesional\n"
            "- **Ingeniero de Sistemas** – Universidad de Antioquia\n"
            "- **+10 años de experiencia** en desarrollo de software fullstack\n"
            "- **Actualmente:** Frontend Developer en **CleverIt (Chile)**, participando en plataformas críticas para "
            "el sector de seguros.\n"
            "- Sectores clave: Banca, seguros, salud, entretenimiento, agricultura, turismo y tecnología.\n"
            "- Tecnologías destacadas:\n"
            "  - **Frontend:** Angular, React, Next.js, Vue, Quasar, Ionic\n"
            "  - **Backend:** Node.js, NestJS, Express\n"
            "  - **Cloud & DevOps:** Serverless, DynamoDB, S3, Cognito, Docker, Firebase\n"
            "  - **Herramientas:** Git, Jira, Bitbucket, Azure DevOps, MobX, Redux, i18n, Tailwind\n\n"
            "Empresas con las que he colaborado:\n"
            "CleverIt, Mindshore, Hublance, N5 now, Personal Soft, Accenture Colombia, Julius Connected 2 Grow, Tres Astronautas.\n\n"
            "Clientes destacados:\n"
            "Sura Chile, Bancolombia, Avianca, Postobón, Medicarte, Conconcreto, PiMedica, Verdnatura, INNOCV Solutions, Rivadavia.\n\n"
            "### Proyectos Destacados\n"
            f"{self.summary}\n\n"
            "---\n\n"
            "### Otros Datos Relevantes\n"
            "- **Proyectos personales:**\n"
            "  - **LexLoop:** Plataforma de flashcards (React, Next.js, Firebase)\n"
            "  - **Alybe:** Sistema POS para restaurantes\n"
            "  - **Momoto:** Emprendimiento de jardinería y servicios rurales\n\n"
            "- **Intereses actuales:** Explorando el desarrollo de **agentes de inteligencia artificial**. "
            "He creado un chatbot profesional que lee mi CV y responde preguntas usando **OpenAI, LangChain y Gradio**.\n\n"
            "- **Objetivo profesional:** Busco nuevas oportunidades como **Frontend o Fullstack Developer**, especialmente en "
            "roles que involucren **flujos de trabajo con IA y agentes inteligentes**, donde pueda seguir aprendiendo y "
            "aportando valor.\n"
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
        