"""VoiceClone API — Local FastAPI server

Endpoints:
  POST /clone          Clone voice from audio
  POST /speak          Synthesize text with cloned voice
  GET  /voices         List cloned voices
  GET  /voices/{id}    Get voice details
  DELETE /voices/{id}  Delete a voice
  GET  /health         Server health/status

All endpoints are local-only (localhost:8765).
No authentication needed — it's your computer.
"""
