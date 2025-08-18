import os
import requests
from ..config.settings import settings

def push_notification(text: str) -> None:
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": settings.PUSHOVER_TOKEN,
            "user": settings.PUSHOVER_USER,
            "message": text,
        }
    )