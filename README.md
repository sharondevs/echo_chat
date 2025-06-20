# Echo-CHAT RAG Application

A scalable RAG (Retrieval-Augmented Generation) application built with FastAPI, featuring streaming chat capabilities and document querying with Google's Gemini models.

## Features

Echo-CHAT is an intelligent assistant that operates in two distinct modes:

1. **Resume Mode**: Specialized AI assistant for analyzing Sharon's professional profile with contextual understanding
2. **Documents Mode**: RAG-powered document Q&A system using vector search and conversational memory

The application leverages Google's latest Gemini 2.0 Flash model with LlamaIndex for sophisticated document processing and ChromaDB for semantic search capabilities.

## Key Features

### **Dual Operating Modes**
- **Resume Analysis**: Deep professional profile analysis with career insights and contextual responses
- **Document Q&A**: Upload and query multiple documents with persistent conversation context

### **Advanced AI Capabilities**
- **Streaming Responses**: Real-time streaming chat with Server-Sent Events (SSE)
- **Conversation Memory**: Persistent chat context within sessions for natural conversations
- **Semantic Search**: ChromaDB-powered vector search for accurate document retrieval
- **Context Caching**: Optimized performance with Google Gemini's context caching

### **Document Processing**
- **Multi-format Support**: PDF, TXT, DOCX, and DOC files
- **Intelligent Chunking**: Optimized text segmentation for better retrieval
- **Session Management**: Isolated document contexts per user session

### **Production Ready**
- **Docker Support**: Complete containerization with Docker Compose
- **Health Monitoring**: Comprehensive health checks and logging
- **Azure Functions Compatible**: Cloud deployment ready

## Quick Start

### Prerequisites

- Python 3.11+
- Google API Key with Gemini access
- Valid billing account for Google AI services

### Local Development

1. **Clone and setup**
```bash
git clone <repository-url>
cd echo_chat
chmod +x start.sh
./start.sh
```

2. **Configure your API key**
```bash
# Copy and edit environment file
cp env.example .env
# Edit .env file with your Google API key
GOOGLE_API_KEY=your_google_api_key_here
```

3. **Start the application**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Deployment

### Docker Deployment

1. **Build and run with Docker**
```bash
chmod +x deploy/docker-run.sh
./deploy/docker-run.sh
```

2. **Or use Docker Compose**
```bash
docker-compose up
```

### GitHub Actions Deployment

The repository includes a GitHub Actions workflow that:
- Tests the application on push/PR
- Builds and pushes Docker images to GitHub Container or other CRs
- Provides deployment hooks for your infrastructure

**Setup:**
1. Add `GOOGLE_API_KEY` to your GitHub repository secrets
2. Push to `main` branch to trigger deployment
3. Docker image will be available at `ghcr.io/your-username/echo_chat:latest`

## API Endpoints

### Core Endpoints

- `GET /echo-chat` - Health check with available modes
- `POST /echo-chat/stream-chat` - Streaming chat endpoint (main feature)
- `POST /echo-chat/upload` - Document upload for RAG indexing
- `GET /echo-chat/session/{session_id}` - Session statistics and info
- `DELETE /echo-chat/session/{session_id}` - Cleanup session resources
- `GET /echo-chat/modes` - Available query modes
- `GET /health` - Simple health check

### Usage Examples

#### Resume Analysis Chat
```bash
curl -X POST "http://localhost:8000/echo-chat/stream-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Sharon'\''s technical expertise and career progression?",
    "mode": "resume"
  }'
```

#### Document Upload & RAG Chat
```bash
# Upload documents first
curl -X POST "http://localhost:8000/echo-chat/upload" \
  -F "files=@technical_documentation.pdf" \
  -F "files=@project_specs.docx"

# Chat with uploaded documents (streaming response)
curl -X POST "http://localhost:8000/echo-chat/stream-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize the key technical requirements from these documents",
    "mode": "documents",
    "session_id": "your-session-id"
  }'
```

## Technology Stack

### AI & ML
- **Google Gemini 2.0 Flash**: Latest multimodal language model
- **LlamaIndex**: Advanced RAG framework with streaming support
- **Google GenAI Embeddings**: text-embedding-004 for semantic search
- **ChromaDB**: Vector database for document retrieval

### Backend & API
- **FastAPI**: High-performance async web framework
- **Uvicorn**: ASGI server with streaming support
- **Pydantic**: Data validation and settings management

### Document Processing
- **PyPDF2**: PDF text extraction
- **docx2txt**: Word document processing
- **aiofiles**: Async file handling

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google API key for Gemini models | - | ✅ |
| `RESUME_PATH` | Path to resume files | `./data/resume` | ❌ |
| `DOCUMENTS_PATH` | Document storage path | `./data/documents` | ❌ |
| `CHROMA_DB_PATH` | ChromaDB storage path | `./data/chroma_db` | ❌ |
| `ENVIRONMENT` | Application environment | `development` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |

### Model Configuration

The application is configured to use:
- **LLM**: Gemini 2.0 Flash (`gemini-2.0-flash`)
- **Embeddings**: Google GenAI text-embedding-004
- **Chunk Size**: 1024 tokens with 200 token overlap
- **Max Output**: 8192 tokens
- **Temperature**: 0.3 for documents, 0.4 for resume

## Architecture

### Resume Mode Architecture
```
User Query → Gemini 2.0 Flash → Context Cache (Resume) → Streaming Response
```

### Documents Mode Architecture  
```
Documents → Processing → ChromaDB Vector Store → LlamaIndex RAG → Chat Engine with Memory → Streaming Response
```

### Session Management
- **Resume Mode**: Stateless with context caching
- **Documents Mode**: Session-based with persistent chat memory and document context

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Development Notes

### Resume Mode Features
- Specialized for Sharon's professional profile analysis
- Uses Google Gemini's context caching for optimal performance
- Provides career insights, skills analysis, and professional guidance
- Third-person perspective responses as Sharon's assistant

### Documents Mode Features
- Session-based RAG with conversational memory
- Supports multiple document types and formats
- Vector similarity search with top-5 retrieval
- Persistent chat context within sessions
- Automatic session cleanup capabilities

## Project Structure

```
echo_chat/
├── main.py                 # FastAPI application
├── start.sh               # Local development script
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── config/
│   └── config.py          # Configuration settings
├── models/
│   └── models.py          # Pydantic models
├── services/
│   └── rag_service.py     # RAG orchestration
├── utils/
│   └── document_processor.py  # Document processing
├── deploy/
│   └── docker-run.sh      # Docker deployment script
├── .github/workflows/
│   └── deploy.yml         # GitHub Actions workflow
├── data/                  # Data storage
│   ├── chroma_db/        # Vector database
│   ├── documents/        # Uploaded documents
│   └── resume/           # Resume files
└── requirements.txt      # Dependencies
```

## Making Changes

The application is designed to be easily modifiable:

1. **Add new endpoints**: Edit `main.py`
2. **Modify configuration**: Update `config/config.py` and `env.example`
3. **Change document processing**: Edit `utils/document_processor.py`
4. **Update RAG logic**: Modify `services/rag_service.py`
5. **Add new models**: Update `models/models.py`

## Troubleshooting

### Common Issues

1. **Google API Key Issues**
   - Ensure your API key has access to Gemini models
   - Check API quotas and billing

2. **Document Processing Errors**
   - Verify file formats are supported (PDF, TXT, DOCX)
   - Check file permissions and sizes

3. **ChromaDB Issues**
   - Ensure write permissions to `data/chroma_db`
   - Clear database if needed: `rm -rf data/chroma_db`

## License

This project is licensed under the MIT License. 