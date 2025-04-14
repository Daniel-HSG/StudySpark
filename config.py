# config.py
import os

# Lese API-Schlüssel aus Umgebungsvariablen
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Optional: Füge eine Überprüfung hinzu
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY Umgebungsvariable ist nicht gesetzt. Bitte setze diese Variable, bevor du die Anwendung startest.")
