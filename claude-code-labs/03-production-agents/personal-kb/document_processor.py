"""
Document Processor - Project 4.1
Handles ingestion, chunking, and embedding of various document types.
"""

import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Generator
from enum import Enum

# Document parsing
import fitz  # PyMuPDF for PDFs
import markdown
from bs4 import BeautifulSoup


class DocumentType(str, Enum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    CODE = "code"
    HTML = "html"


@dataclass
class DocumentChunk:
    """A chunk of a document with metadata."""
    id: str
    content: str
    document_id: str
    document_name: str
    document_type: DocumentType
    chunk_index: int
    total_chunks: int
    start_char: int
    end_char: int
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "document_type": self.document_type.value,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "start_char": self.start_char,
            "end_char": self.end_char,
            **self.metadata
        }


@dataclass
class Document:
    """A processed document."""
    id: str
    name: str
    path: str
    doc_type: DocumentType
    content: str
    chunks: list[DocumentChunk] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class DocumentProcessor:
    """Process documents into chunks for embedding."""
    
    # File extension mapping
    EXTENSION_MAP = {
        ".pdf": DocumentType.PDF,
        ".md": DocumentType.MARKDOWN,
        ".markdown": DocumentType.MARKDOWN,
        ".txt": DocumentType.TEXT,
        ".py": DocumentType.CODE,
        ".js": DocumentType.CODE,
        ".ts": DocumentType.CODE,
        ".jsx": DocumentType.CODE,
        ".tsx": DocumentType.CODE,
        ".java": DocumentType.CODE,
        ".go": DocumentType.CODE,
        ".rs": DocumentType.CODE,
        ".cpp": DocumentType.CODE,
        ".c": DocumentType.CODE,
        ".h": DocumentType.CODE,
        ".html": DocumentType.HTML,
        ".htm": DocumentType.HTML,
        ".json": DocumentType.CODE,
        ".yaml": DocumentType.CODE,
        ".yml": DocumentType.CODE,
        ".toml": DocumentType.CODE,
        ".sql": DocumentType.CODE,
        ".sh": DocumentType.CODE,
        ".bash": DocumentType.CODE,
    }
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size (smaller chunks are merged)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def process_file(self, file_path: str) -> Document:
        """Process a file into a Document with chunks."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine document type
        doc_type = self._get_document_type(path)
        
        # Extract content
        content = self._extract_content(path, doc_type)
        
        # Create document ID
        doc_id = self._generate_id(path, content)
        
        # Create document
        doc = Document(
            id=doc_id,
            name=path.name,
            path=str(path.absolute()),
            doc_type=doc_type,
            content=content,
            metadata={
                "file_size": path.stat().st_size,
                "extension": path.suffix,
            }
        )
        
        # Chunk the document
        doc.chunks = self._chunk_document(doc)
        
        return doc
    
    def process_text(
        self,
        text: str,
        name: str = "pasted_text",
        doc_type: DocumentType = DocumentType.TEXT
    ) -> Document:
        """Process raw text into a Document with chunks."""
        doc_id = self._generate_id(name, text)
        
        doc = Document(
            id=doc_id,
            name=name,
            path="",
            doc_type=doc_type,
            content=text,
            metadata={"source": "direct_input"}
        )
        
        doc.chunks = self._chunk_document(doc)
        
        return doc
    
    def _get_document_type(self, path: Path) -> DocumentType:
        """Determine document type from file extension."""
        ext = path.suffix.lower()
        return self.EXTENSION_MAP.get(ext, DocumentType.TEXT)
    
    def _extract_content(self, path: Path, doc_type: DocumentType) -> str:
        """Extract text content from a file."""
        if doc_type == DocumentType.PDF:
            return self._extract_pdf(path)
        elif doc_type == DocumentType.HTML:
            return self._extract_html(path)
        elif doc_type == DocumentType.MARKDOWN:
            return self._extract_markdown(path)
        else:
            # Text and code files
            return path.read_text(encoding="utf-8", errors="ignore")
    
    def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF."""
        text_parts = []
        
        with fitz.open(path) as pdf:
            for page_num, page in enumerate(pdf, 1):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num}]\n{text}")
        
        return "\n\n".join(text_parts)
    
    def _extract_html(self, path: Path) -> str:
        """Extract text from HTML."""
        html_content = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        return soup.get_text(separator="\n", strip=True)
    
    def _extract_markdown(self, path: Path) -> str:
        """Extract text from Markdown (preserving structure)."""
        md_content = path.read_text(encoding="utf-8", errors="ignore")
        # Keep markdown as-is for better context
        return md_content
    
    def _generate_id(self, identifier: any, content: str) -> str:
        """Generate a unique ID for a document."""
        hash_input = f"{identifier}:{content[:1000]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _chunk_document(self, doc: Document) -> list[DocumentChunk]:
        """Split document into chunks."""
        content = doc.content
        
        if doc.doc_type == DocumentType.CODE:
            return self._chunk_code(doc)
        elif doc.doc_type == DocumentType.MARKDOWN:
            return self._chunk_markdown(doc)
        else:
            return self._chunk_text(doc)
    
    def _chunk_text(self, doc: Document) -> list[DocumentChunk]:
        """Chunk plain text with sentence awareness."""
        content = doc.content
        chunks = []
        
        # Split into sentences (roughly)
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(
                        doc, current_chunk.strip(), chunk_index,
                        current_start, current_start + len(current_chunk)
                    ))
                    chunk_index += 1
                    # Overlap: keep last part
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_start = current_start + len(current_chunk) - len(overlap_text)
                    current_chunk = overlap_text + sentence + " "
                else:
                    current_chunk += sentence + " "
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(self._create_chunk(
                doc, current_chunk.strip(), chunk_index,
                current_start, current_start + len(current_chunk)
            ))
        
        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _chunk_markdown(self, doc: Document) -> list[DocumentChunk]:
        """Chunk markdown by headers."""
        content = doc.content
        chunks = []
        
        # Split by headers
        sections = re.split(r'\n(#{1,6}\s+[^\n]+)\n', content)
        
        current_section = ""
        current_header = ""
        current_start = 0
        chunk_index = 0
        
        for i, section in enumerate(sections):
            if re.match(r'^#{1,6}\s+', section):
                # This is a header
                if current_section.strip():
                    chunks.append(self._create_chunk(
                        doc, 
                        f"{current_header}\n{current_section}".strip(),
                        chunk_index,
                        current_start,
                        current_start + len(current_section),
                        metadata={"header": current_header}
                    ))
                    chunk_index += 1
                current_header = section
                current_start = content.find(section, current_start)
                current_section = ""
            else:
                current_section += section
                
                # Split large sections
                if len(current_section) > self.chunk_size:
                    sub_chunks = self._chunk_text(Document(
                        id=doc.id,
                        name=doc.name,
                        path=doc.path,
                        doc_type=DocumentType.TEXT,
                        content=current_section
                    ))
                    for sub in sub_chunks:
                        sub.metadata["header"] = current_header
                        sub.chunk_index = chunk_index
                        chunks.append(sub)
                        chunk_index += 1
                    current_section = ""
        
        # Add final section
        if current_section.strip():
            chunks.append(self._create_chunk(
                doc,
                f"{current_header}\n{current_section}".strip(),
                chunk_index,
                current_start,
                len(content),
                metadata={"header": current_header}
            ))
        
        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks if chunks else [self._create_chunk(doc, content, 0, 0, len(content))]
    
    def _chunk_code(self, doc: Document) -> list[DocumentChunk]:
        """Chunk code by functions/classes."""
        content = doc.content
        chunks = []
        
        # Try to split by function/class definitions
        # This is a simplified approach - works for Python, JS, etc.
        patterns = [
            r'\n((?:async\s+)?(?:def|function|class)\s+\w+[^\n]*(?:\n(?:[ \t]+[^\n]+))*)',  # Functions/classes
            r'\n((?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>[^\n]*(?:\n(?:[ \t]+[^\n]+))*)',  # Arrow functions
        ]
        
        # If we can't find code structures, fall back to line-based chunking
        found_structures = False
        for pattern in patterns:
            matches = list(re.finditer(pattern, "\n" + content))
            if matches:
                found_structures = True
                break
        
        if not found_structures:
            # Line-based chunking for code
            lines = content.split("\n")
            current_chunk = ""
            current_start = 0
            chunk_index = 0
            
            for line in lines:
                if len(current_chunk) + len(line) <= self.chunk_size:
                    current_chunk += line + "\n"
                else:
                    if current_chunk.strip():
                        chunks.append(self._create_chunk(
                            doc, current_chunk.strip(), chunk_index,
                            current_start, current_start + len(current_chunk)
                        ))
                        chunk_index += 1
                    current_start += len(current_chunk)
                    current_chunk = line + "\n"
            
            if current_chunk.strip():
                chunks.append(self._create_chunk(
                    doc, current_chunk.strip(), chunk_index,
                    current_start, len(content)
                ))
        else:
            # Structure-based chunking
            chunks = self._chunk_text(doc)
        
        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks if chunks else [self._create_chunk(doc, content, 0, 0, len(content))]
    
    def _create_chunk(
        self,
        doc: Document,
        content: str,
        chunk_index: int,
        start_char: int,
        end_char: int,
        metadata: dict = None
    ) -> DocumentChunk:
        """Create a DocumentChunk."""
        chunk_id = f"{doc.id}_{chunk_index}"
        
        return DocumentChunk(
            id=chunk_id,
            content=content,
            document_id=doc.id,
            document_name=doc.name,
            document_type=doc.doc_type,
            chunk_index=chunk_index,
            total_chunks=0,  # Will be updated later
            start_char=start_char,
            end_char=end_char,
            metadata=metadata or {}
        )


# Convenience function
def process_document(file_path: str, **kwargs) -> Document:
    """Process a document file into chunks."""
    processor = DocumentProcessor(**kwargs)
    return processor.process_file(file_path)


def process_text(text: str, name: str = "input", **kwargs) -> Document:
    """Process raw text into chunks."""
    processor = DocumentProcessor(**kwargs)
    return processor.process_text(text, name)


if __name__ == "__main__":
    # Test
    processor = DocumentProcessor(chunk_size=500)
    
    # Test with a markdown string
    test_md = """# Introduction

This is a test document about AI and machine learning.

## What is AI?

Artificial Intelligence (AI) refers to systems that can perform tasks 
that typically require human intelligence. This includes learning, 
reasoning, problem-solving, and understanding language.

## Machine Learning

Machine learning is a subset of AI that enables systems to learn 
from data without being explicitly programmed.

### Supervised Learning

In supervised learning, models learn from labeled data.

### Unsupervised Learning

In unsupervised learning, models find patterns in unlabeled data.
"""
    
    doc = processor.process_text(test_md, "test.md", DocumentType.MARKDOWN)
    
    print(f"Document: {doc.name}")
    print(f"Type: {doc.doc_type}")
    print(f"Chunks: {len(doc.chunks)}")
    
    for chunk in doc.chunks:
        print(f"\n--- Chunk {chunk.chunk_index + 1}/{chunk.total_chunks} ---")
        print(chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content)
