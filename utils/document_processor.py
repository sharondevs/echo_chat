import os
import asyncio
from typing import List, Dict, Any
from pathlib import Path
import aiofiles
import PyPDF2
import docx2txt
import logging
from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser
from config.config import settings

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.supported_extensions = {'.pdf', '.txt', '.docx', '.doc'}
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
    
    async def process_uploaded_files(self, files: List[Any]) -> List[Document]:
        """Process uploaded files and return LlamaIndex documents"""
        documents = []
        
        for file in files:
            try:
                content = await self._extract_text_from_file(file)
                if content:
                    doc = Document(
                        text=content,
                        metadata={
                            "filename": file.filename,
                            "file_size": file.size if hasattr(file, 'size') else 0,
                            "source": "uploaded"
                        }
                    )
                    documents.append(doc)
                    logger.info(f"Processed file: {file.filename}")
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
        
        return documents
    
    
    async def _extract_text_from_file(self, file) -> str:
        """Extract text from uploaded file object"""
        content = await file.read()
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension == '.txt':
            return content.decode('utf-8')
        elif file_extension == '.pdf':
            return self._extract_pdf_text(content)
        elif file_extension in ['.docx', '.doc']:
            return self._extract_docx_text(content)
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return ""
    
    async def _extract_text_from_path(self, file_path: Path) -> str:
        """Extract text from file path"""
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.txt':
            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                return await f.read()
        elif file_extension == '.pdf':
            with open(file_path, 'rb') as f:
                return self._extract_pdf_text(f.read())
        elif file_extension in ['.docx', '.doc']:
            return docx2txt.process(str(file_path))
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return ""
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF content"""
        try:
            import io
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""
    
    def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX content"""
        try:
            import io
            # For uploaded files, we need to save temporarily
            temp_path = f"/tmp/temp_doc_{id(content)}.docx"
            with open(temp_path, 'wb') as f:
                f.write(content)
            text = docx2txt.process(temp_path)
            os.remove(temp_path)
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            return "" 