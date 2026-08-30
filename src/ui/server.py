import os
import sys
import uvicorn
from fastapi.responses import FileResponse
from src.server import app

UI_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", include_in_schema=False)
def serve_ui():
    return FileResponse(os.path.join(UI_DIR, "index.html"))

@app.get("/config.json", include_in_schema=False)
def serve_config():
    config_path = os.path.join(UI_DIR, "config.json")
    if os.path.exists(config_path):
        return FileResponse(config_path)
    example_path = os.path.join(UI_DIR, "config.json.example")
    if os.path.exists(example_path):
        return FileResponse(example_path)
    return {"api_endpoint": "http://localhost:8080"}

if __name__ == "__main__":
    print("========================================================================")
    print("🚀 AWS AI Security & OWASP LLM Top 10 Shield - Web UI Playground")
    print("👉 Interface live at: http://localhost:8080")
    print("========================================================================")
    uvicorn.run("src.ui.server:app", host="0.0.0.0", port=8080, reload=False)
