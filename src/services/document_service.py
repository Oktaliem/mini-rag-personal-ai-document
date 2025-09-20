"""
Document processing service.

This service handles document reading, processing, and management operations.
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader

from ..core.config import settings


class DocumentService:
    """Service for document processing operations."""
    
    def __init__(self) -> None:
        self.allowed_extensions = {".pdf", ".md", ".txt"}
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def sha1_u64(self, text: str) -> int:
        """Convert text to SHA1 hash as uint64."""
        h = hashlib.sha1(text.encode("utf-8", errors="ignore")).digest()
        return int.from_bytes(h[:8], "big", signed=False)
    
    def read_docs(self, datapath: str) -> List[Dict[str, Any]]:
        """Read documents from a folder or file."""
        items: List[Dict[str, Any]] = []
        p = Path(datapath)
        if not p.exists():
            return items

        if p.is_file():
            items = self._read_single_file(p)
        else:
            for file_path in p.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.allowed_extensions:
                    items.extend(self._read_single_file(file_path))
        
        return items
    
    def _read_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read a single file and return document items."""
        try:
            if file_path.suffix.lower() == ".pdf":
                return self._read_pdf(file_path)
            else:
                return self._read_text_file(file_path)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
    
    def _read_pdf(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            if text.strip():
                return [{
                    "text": text.strip(),
                    "doc_path": str(file_path),
                    "mtime": file_path.stat().st_mtime
                }]
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
        return []
    
    def _read_text_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read text file (txt, md, etc.)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read().strip()
            
            if text:
                return [{
                    "text": text,
                    "doc_path": str(file_path),
                    "mtime": file_path.stat().st_mtime
                }]
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
        return []
    
    def chunk_words(self, text: str, size: Optional[int] = None, overlap: Optional[int] = None) -> List[str]:
        """Split text into overlapping chunks of words."""
        if size is None:
            size = self.chunk_size
        if overlap is None:
            overlap = self.chunk_overlap
        
        words = text.split()
        if len(words) <= size:
            return [text] if text.strip() else []
        
        chunks = []
        for i in range(0, len(words), size - overlap):
            chunk = " ".join(words[i:i + size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def process_uploaded_files(self, files: List[Any]) -> Dict[str, Any]:
        """Process uploaded files and save them to the documents directory."""
        docs_dir = Path(settings.docs_dir)
        docs_dir.mkdir(exist_ok=True)
        
        saved_files = []
        failed_files = []
        
        for file in files:
            try:
                # Check file extension
                if not file.filename or not any(file.filename.lower().endswith(ext) for ext in self.allowed_extensions):
                    ext = Path(file.filename).suffix.lower() if file.filename else ""
                    failed_files.append(f"Unsupported extension: {ext}")
                    continue
                
                # Save file
                file_path = docs_dir / file.filename
                with open(file_path, "wb") as buffer:
                    content = file.file.read()
                    buffer.write(content)
                
                saved_files.append(file.filename)
                
            except Exception as e:
                failed_files.append(f"{file.filename}: {str(e)}")
        
        if failed_files:
            # Return error format (validation now handled at endpoint level)
            error_msg = failed_files[0] if len(failed_files) == 1 else f"{len(failed_files)} files failed"
            return {
                "status": "error",
                "detail": error_msg
            }
        else:
            # Success format matching original API
            return {
                "saved": saved_files,
                "message": "Files uploaded. Indexing has started."
            }
    
    def get_document_stats(self, datapath: str) -> Dict[str, Any]:
        """Get statistics about documents in a directory."""
        docs = self.read_docs(datapath)
        
        total_chars = sum(len(doc["text"]) for doc in docs)
        total_words = sum(len(doc["text"].split()) for doc in docs)
        
        return {
            "total_documents": len(docs),
            "total_characters": total_chars,
            "total_words": total_words,
            "average_chars_per_doc": total_chars // len(docs) if docs else 0,
            "average_words_per_doc": total_words // len(docs) if docs else 0
        }
