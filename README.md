# Echo-CHAT RAG Application

A scalable RAG (Retrieval-Augmented Generation) application built with FastAPI, featuring streaming chat capabilities and document querying with Google's Gemini models.

## Features

- **Dual Query Modes**: Resume analysis and document-based Q&A
- **Streaming Chat**: Real-time streaming responses for better UX
- **Document Upload**: Support for PDF, TXT, and DOCX files
- **Session Management**: Persistent chat context and document indexing
- **Vector Search**: ChromaDB-powered semantic search

## Quick Start

### Prerequisites

- Python 3.11+
- Google API Key (for Gemini models)

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

- `GET /echo-chat` - Health check and service info
- `POST /echo-chat/stream-chat` - Streaming chat endpoint
- `POST /echo-chat/upload` - Document upload for indexing
- `GET /echo-chat/session/{session_id}` - Session information
- `DELETE /echo-chat/session/{session_id}` - Cleanup session
- `GET /echo-chat/modes` - Available query modes
- `GET /health` - Simple health check

### Usage Examples

#### Resume Chat
```bash
curl -X POST "http://localhost:8000/echo-chat/stream-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my work experience?",
    "mode": "resume"
  }'
```

#### Document Upload & Chat
```bash
# Upload documents
curl -X POST "http://localhost:8000/echo-chat/upload" \
  -F "files=@document1.pdf" \
  -F "files=@document2.txt"

# Chat with documents
curl -X POST "http://localhost:8000/echo-chat/stream-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize the uploaded documents",
    "mode": "documents",
    "session_id": "your-session-id"
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini models | Required |
| `RESUME_PATH` | Path to resume files | `./data/resume` |
| `DOCUMENTS_PATH` | Path for document storage | `./data/documents` |
| `CHROMA_DB_PATH` | ChromaDB storage path | `./data/chroma_db` |

| `ENVIRONMENT` | Application environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

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

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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