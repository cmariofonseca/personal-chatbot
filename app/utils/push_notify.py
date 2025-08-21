from app.config.settings import settings
import os
import requests

# Envía una notificación push con el texto proporcionado mediante Pushover.
def push_notification(text: str) -> None:
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": settings.PUSHOVER_TOKEN,
            "user": settings.PUSHOVER_USER,
            "message": text,
        }
    )