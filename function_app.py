import azure.functions as func
import logging
import os
import json
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

@app.function_name("EchoChatAPI")
@app.route(route="{*route}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def echo_chat_api(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Functions HTTP trigger for Echo-CHAT RAG API
    Designed to work with Azure API Management
    """
    logging.info(f'Processing {req.method} request to {req.url}')
    
    try:
        # Handle CORS preflight requests
        if req.method == "OPTIONS":
            return func.HttpResponse(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                    "Access-Control-Max-Age": "86400"
                }
            )
        
        # Import the ASGI adapter
        from azure.functions import AsgiMiddleware
        
        # Create ASGI middleware to handle FastAPI
        return await AsgiMiddleware(fastapi_app).handle_async(req)
        
    except Exception as e:
        logging.error(f"Error in Azure Functions handler: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )

@app.function_name("HealthCheck")
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Dedicated health check endpoint for API Management health probes
    """
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "timestamp": func.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "echo-chat-rag-api"
        }
        
        return func.HttpResponse(
            json.dumps(health_status),
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({"status": "unhealthy", "error": str(e)}),
            status_code=503,
            headers={"Content-Type": "application/json"}
        ) 

@app.route(route="func_app", auth_level=func.AuthLevel.FUNCTION)
def func_app(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )