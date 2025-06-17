import logging
from pathlib import Path
import uuid
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import json

from pydantic import Field

from models.models import (
    QueryMode, DocumentUploadResponse, HealthResponse
)
from services.rag_service import RAGService
from config.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global RAG service instance
rag_service: Optional[RAGService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global rag_service
    logger.info("Starting up RAG service...")
    rag_service = RAGService()
    logger.info("RAG service initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down RAG service...")

app = FastAPI(
    title="Echo-CHAT RAG API",
    description="A scalable RAG application with streaming chat and document querying capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your React app's URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

def get_rag_service() -> RAGService:
    """Dependency to get RAG service instance"""
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return rag_service

@app.get("/echo-chat", response_model=HealthResponse)
async def root():
    """Root endpoint - health check and service info"""
    try:
        service = get_rag_service()
        available_modes = service.get_available_modes()
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            modes_available=available_modes
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/echo-chat/stream-chat")  
async def stream_chat(
    message: str = Body(..., description="The chat message/question to ask"),
    mode: QueryMode = Body(..., description="Query mode"),
    session_id: Optional[str] = Body(None, description="Session ID for conversation context"),
    service: RAGService = Depends(get_rag_service)
):
    """
    Streaming chat endpoint with context and memory - React.js compatible
    
    - **message**: The chat message
    - **mode**: Query mode (resume or documents)
    - **session_id**: Session ID for document context and chat history
    """
    try:
        # Validate required parameters
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Question is required and cannot be empty")
        
        async def generate_stream():
            try:
                if mode == QueryMode.DOCUMENTS:
                    if not session_id:
                        error_chunk = json.dumps({
                            "error": "Session ID is required for documents mode",
                            "type": "error",
                            "session_id": session_id
                        })
                        yield f"data: {error_chunk}\n\n"
                        return
                    async for chunk in service.stream_chat(message, session_id):
                        # Ensure proper JSON serialization for React
                        json_chunk = json.dumps(chunk, ensure_ascii=False)
                        yield f"data: {json_chunk}\n\n"
                if mode == QueryMode.RESUME:
                    file_paths = [str(p) for p in Path(settings.resume_path).iterdir() if p.is_file()]
                    context_files = await asyncio.gather(*[service.upload_file(file) for file in file_paths])
                    async for chunk in service.resume_chat_stream(message=message, context_files=context_files):
                        json_chunk = json.dumps(chunk, ensure_ascii=False)
                        yield f"data: {json_chunk}\n\n"
                        
            except Exception as e:
                # Send error as SSE event
                error_chunk = json.dumps({
                    "error": str(e),
                    "type": "error",
                    "session_id": session_id
                })
                yield f"data: {error_chunk}\n\n"
        
        return StreamingResponse(
            generate_stream(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error in streaming chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing streaming chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/echo-chat/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = None,
    service: RAGService = Depends(get_rag_service)
):
    """
    Upload documents for querying
    
    - **files**: List of files to upload (PDF, TXT, DOCX supported)
    - **session_id**: Optional session ID (will be generated if not provided)
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Validate file types
        supported_extensions = {'.pdf', '.txt', '.docx', '.doc'}
        for file in files:
            file_ext = file.filename.split('.')[-1].lower()
            if f'.{file_ext}' not in supported_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(supported_extensions)}"
                )
        
        # Process and index documents
        file_count = await service.process_and_index_documents(files, session_id)
        
        return DocumentUploadResponse(
            message=f"Successfully processed {file_count} documents",
            file_count=file_count,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/echo-chat/session/{session_id}")
async def get_session_info(
    session_id: str,
    service: RAGService = Depends(get_rag_service)
):
    """Get information about a specific session"""
    try:
        stats = service.get_session_stats(session_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/echo-chat/session/{session_id}")
async def cleanup_session(
    session_id: str,
    service: RAGService = Depends(get_rag_service)
):
    """Clean up resources for a specific session"""
    try:
        service.cleanup_session(session_id)
        return {"message": f"Session {session_id} cleaned up successfully"}
    except Exception as e:
        logger.error(f"Error cleaning up session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/echo-chat/modes")
async def get_available_modes(service: RAGService = Depends(get_rag_service)):
    """Get available query modes"""
    try:
        modes = service.get_available_modes()
        return {"available_modes": modes}
    except Exception as e:
        logger.error(f"Error getting available modes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Simple health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    try:
        service = get_rag_service()
        available_modes = service.get_available_modes()
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.environment,
            "modes_available": available_modes
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    ) 