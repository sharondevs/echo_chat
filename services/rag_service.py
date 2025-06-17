import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from google import genai
from google.genai import types
from utils.document_processor import DocumentProcessor
from models.models import QueryMode
from config.config import settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from google.genai.types import EmbedContentConfig



logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.document_indexes: Dict[str, VectorStoreIndex] = {}
        self.chat_engines: Dict[str, Any] = {}  # Store chat engines per session for RAG

        # let's initialize the gemini client for streaming resume chats
        self.resume_client = genai.Client(api_key=settings.google_api_key)
        self.resume_chat = None
        self.resume_generation_config = types.GenerateContentConfig(
             temperature=0.4,
             system_instruction=settings.resume_system_prompt,
             max_output_tokens=settings.max_tokens,
             frequency_penalty=settings.frequency_penalty,
             presence_penalty=settings.presence_penalty,
            )

        # this setup's llamaindex for RAG mode
        self._setup_llama_index()
    
    #  RAG DOCUMENT MODE 
    def _setup_llama_index(self):
        """Initialize LlamaIndex with Gemini LLM and Google embeddings"""
        try:
            # Initialize Gemini LLM
            self.llm = Gemini(
                model=settings.model_name,
                api_key=settings.google_api_key,
                temperature=0.3
            )
            
            # Initialize Google embeddings
            self.embed_model = GoogleGenAIEmbedding(
                model_name="text-embedding-004",
                embed_batch_size=100,
                api_key=settings.google_api_key,
            )
            
            # Set global LlamaIndex settings
            Settings.llm = self.llm
            Settings.embed_model = self.embed_model
            Settings.chunk_size = settings.chunk_size
            Settings.chunk_overlap = settings.chunk_overlap
            
            logger.info("LlamaIndex with Gemini initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LlamaIndex: {str(e)}")
            raise
    
    async def process_and_index_documents(self, files: List[Any], session_id: str) -> int:
        """Process uploaded files and create vector index for session"""
        try:
            # Process files into LlamaIndex documents
            documents = await self.document_processor.process_uploaded_files(files)
            
            if documents:
                # Create vector index using Gemini embeddings
                index = VectorStoreIndex.from_documents(
                    documents,
                    embed_model=self.embed_model
                )
                self.document_indexes[session_id] = index
                
                # Initialize chat engine for this session
                await self._create_chat_engine(session_id)
                
                logger.info(f"Created document index for session {session_id} with {len(documents)} documents")
                return len(documents)
            else:
                logger.warning("No documents processed")
                return 0
                
        except Exception as e:
            logger.error(f"Error processing and indexing documents: {str(e)}")
            raise
    
    async def _create_chat_engine(self, session_id: str):
        """Create a chat engine with memory for a session"""
        if session_id not in self.document_indexes:
            raise ValueError(f"No documents available for session {session_id}")
        
        index = self.document_indexes[session_id]
        
        # Create query engine with streaming support
        query_engine = index.as_query_engine(
            llm=self.llm,
            embed_model=self.embed_model,
            response_mode="tree_summarize",
            similarity_top_k=5,
            streaming=True,  # Enable streaming
            verbose=True
        )
        
        # Create chat engine with memory
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        
        chat_engine = CondenseQuestionChatEngine.from_defaults(
            query_engine=query_engine,
            memory=memory,
            llm=self.llm,
            verbose=True
        )
        
        self.chat_engines[session_id] = chat_engine
        return chat_engine

    async def stream_chat(self, message: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response with context and memory"""
        try:
            if session_id not in self.chat_engines:
                # Create chat engine if it doesn't exist
                await self._create_chat_engine(session_id)
            
            chat_engine = self.chat_engines[session_id]
            
            # Get streaming response from chat engine
            streaming_response = chat_engine.stream_chat(message)
            
            # Extract sources if available
            sources = []
            if hasattr(streaming_response, 'source_nodes') and streaming_response.source_nodes:
                for node in streaming_response.source_nodes:
                    if hasattr(node, 'metadata') and 'filename' in node.metadata:
                        sources.append(node.metadata['filename'])
            
            # Stream the response
            for token in streaming_response.response_gen:
                yield {
                    "text": token,
                    "sources": sources,
                    "metadata": {
                        "session_id": session_id,
                        "query_type": "streaming_chat",
                        "model_used": settings.model_name
                    }
                }
            
            logger.info(f"Streaming chat processed for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}")
            raise
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a document session"""
        if session_id in self.document_indexes:
            index = self.document_indexes[session_id]
            return {
                "session_id": session_id,
                "documents_count": len(index.docstore.docs),
                "has_documents": True,
                "index_created": True,
                "has_chat_engine": session_id in self.chat_engines
            }
        return {
            "session_id": session_id,
            "documents_count": 0,
            "has_documents": False,
            "index_created": False,
            "has_chat_engine": False
        }
    
    def cleanup_session(self, session_id: str):
        """Clean up resources for a session"""
        if session_id in self.document_indexes:
            del self.document_indexes[session_id]
        if session_id in self.chat_engines:
            del self.chat_engines[session_id]
        logger.info(f"Cleaned up session: {session_id}")
    

    # RAG RESUME MODE 
    
    # this is the upload function for resume mode
    async def upload_file(self, file_path: str) -> Optional[Any]:
        """Upload a file to GEMINI API."""
        try:
            uploaded_file = self.resume_client.files.upload(file=file_path)
            return uploaded_file
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return None

    # This is for context caching (if needed)
    async def add_content_cache(self, personal_docs: bool = True, docs: bool = False):
        try:
            if personal_docs:
                personal_file_paths = [str(p) for p in Path(settings.resume_path).iterdir() if p.is_file()]
                contents = await asyncio.gather(*[self.upload_file(file) for file in personal_file_paths])
                if docs:
                    doc_file_paths = [str(p) for p in Path(settings.documents_path).iterdir() if p.is_file()]
                    doc_contents = await asyncio.gather(*[self.upload_file(file) for file in doc_file_paths])
                    contents.extend(doc_contents)
                
            self.cached_content = await self.resume_client.caches.create(
                model=settings.model_name,
                config=types.CreateCachedContentConfig(
                    contents=contents,
                    system_instruction=settings.resume_system_prompt,
                    ttl=f"{settings.cache_ttl}s",
                ),
            )
            self.resume_generation_config.cached_content = self.cached_content.name

        except Exception as e:
            print(f"Error creating cached content: {str(e)}")
    
    async def delete_cached_content(self) -> None:
        """Delete the cached content."""
        await self.resume_client.caches.delete(name=self.cached_content.name)
    
    async def update_cached_content(self, files: List[types.File]) -> None:
        """Update the cached content."""
        self.cached_content = await self.resume_client.caches.create(
                model=settings.model_name,
                config=types.CreateCachedContentConfig(
                    contents=[
                        types.Content(
                            role="user",
                            parts= files,
                        )
                    ],
                    system_instruction=settings.resume_system_prompt,
                    ttl=f"{settings.cache_ttl}s",
                ),
            )
        self.resume_generation_config.cached_content = self.cached_content.name

    # resume chat mode
    async def resume_chat_reset(self) -> None:
        self.resume_chat = self.resume_client.chats.create(model=settings.model_name)
    
    async def resume_chat_stream(self, message: str, 
                                 context_files:  Optional[List[types.File]] = None,
                                 context: Optional[str] = None,
                                 ) -> AsyncGenerator[Dict[str, Any], None]:
        if not self.resume_chat:
            await self.resume_chat_reset()
        
        formatted_prompt = self._prompt_builder(message=message, context_files=context_files, context=context)
        
        try:
            
            response_stream = self.resume_chat.send_message_stream(
                formatted_prompt,
                config=self.resume_generation_config
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield {
                        "text": chunk.text,
                        "sources": None,
                        "metadata": {
                            "session_id": None,
                            "query_type": "streaming_chat",
                            "model_used": settings.model_name
                        }
                    }
        except Exception as e:
            yield f"Error in resume chat stream: {str(e)}"
    
    async def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get the chat history from the current session."""
        if not self.resume_chat:
            return []
        
        try:
            history = []
            for message in self.resume_chat.get_history():
                history.append({
                    "role": message.role,
                    "content": message.parts[0].text if message.parts else ""
                })
            return history
        except Exception as e:
            print(f"Error getting chat history: {str(e)}")
            return []

    def _prompt_builder(self, message: str, context_files: Optional[List[types.File]] = None, context: Optional[str] = None) -> str:
        main_msg = f"""
        Context: {context}
        Question: {message}
        Answer: """
        if context_files: 
            return context_files + [ main_msg]
        else: 
            return [main_msg]
        

    def get_available_modes(self) -> List[str]:
        """Get list of available query modes"""
        return [mode.value for mode in QueryMode]
    