import azure.functions as func
import logging
import os
from pathlib import Path

# Set up environment for Azure Functions
os.environ.setdefault("ENVIRONMENT", "production")

# Ensure data directories exist
data_dir = Path("/tmp/echo_chat_data")
data_dir.mkdir(exist_ok=True)
(data_dir / "chroma_db").mkdir(exist_ok=True)
(data_dir / "documents").mkdir(exist_ok=True)
(data_dir / "resume").mkdir(exist_ok=True)

# Update paths for Azure Functions
os.environ.setdefault("CHROMA_DB_PATH", str(data_dir / "chroma_db"))
os.environ.setdefault("DOCUMENTS_PATH", str(data_dir / "documents"))
os.environ.setdefault("RESUME_PATH", str(data_dir / "resume"))

from main import app as fastapi_app

# Create Azure Functions app
app = func.FunctionApp()

@app.function_name("HttpTrigger")
@app.route(route="{*route}", auth_level=func.AuthLevel.ANONYMOUS)
async def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Functions HTTP trigger that wraps the FastAPI application
    """
    logging.info(f'Processing {req.method} request to {req.url}')
    
    # Import the ASGI adapter
    from azure.functions import AsgiMiddleware
    
    # Create ASGI middleware to handle FastAPI
    return await AsgiMiddleware(fastapi_app).handle_async(req) 