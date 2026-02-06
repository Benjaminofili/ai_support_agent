"""
Knowledge Base API endpoints.

Provides endpoints for document management including:
- Upload documents (PDF, DOCX, TXT, CSV, JSON, Markdown)
- List and retrieve documents
- Delete documents

All endpoints require API key authentication.
"""

import logging
import uuid
from typing import List, Optional
from urllib.parse import urlencode

from django.shortcuts import get_object_or_404
from ninja import Router, File, UploadedFile, Schema, Form
from ninja.security import HttpBearer

from .models import Document
from .tasks import process_document_task
from apps.companies.models import Company

logger = logging.getLogger(__name__)
router = Router()


# =============================================================================
# AUTHENTICATION
# =============================================================================

class ApiKeyAuth(HttpBearer):
    """
    API Key authentication using Bearer token.
    
    The API key is the company's unique identifier for API access.
    Include in requests as: Authorization: Bearer <api_key>
    """
    
    def authenticate(self, request, token: str) -> Optional[Company]:
        """
        Authenticate request using API key.
        
        Args:
            request: The HTTP request
            token: The Bearer token (API key)
            
        Returns:
            Company if authenticated, None otherwise
        """
        try:
            company = Company.objects.select_related('owner').get(api_key=token)
            if not company.owner.is_active:
                logger.warning(f"Inactive company attempted API access: {company.id}")
                return None
            return company
        except Company.DoesNotExist:
            logger.warning(f"Invalid API key attempted: {token[:10]}...")
            return None


# =============================================================================
# SCHEMAS
# =============================================================================

class DocumentOut(Schema):
    """Document response schema."""
    id: uuid.UUID
    title: str
    source_type: str
    status: str
    chunk_count: int
    created_at: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Company FAQ",
                "source_type": "pdf",
                "status": "completed",
                "chunk_count": 15,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class UploadResponse(Schema):
    """Document upload response schema."""
    id: uuid.UUID
    message: str


class ErrorResponse(Schema):
    """Error response schema."""
    error: str


class MessageResponse(Schema):
    """Generic message response schema."""
    message: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/documents/upload/",
    response={200: UploadResponse, 400: ErrorResponse},
    auth=ApiKeyAuth(),
    summary="Upload a document",
    description="""
    Upload a document to the knowledge base.
    
    Supported formats:
    - PDF (.pdf)
    - Word Document (.docx)
    - Text files (.txt)
    - CSV files (.csv)
    - JSON files (.json)
    - Markdown files (.md)
    
    The document will be processed asynchronously:
    1. Text extraction
    2. Chunking into segments
    3. Embedding generation
    4. Storage in vector database
    
    Check document status using GET /documents/{id}/
    """
)
def upload_document(
    request,
    title: str = Form(...),
    file: UploadedFile = File(None),
    content: str = Form(None)
):
    """
    Upload a document file or paste text content.
    
    Args:
        title: Document title for display
        file: Optional file upload (PDF, DOCX, TXT, CSV, JSON, MD)
        content: Optional pasted text content
        
    Returns:
        Document ID and status message
    """
    company = request.auth
    
    if not file and not content:
        return 400, {"error": "Either file or content must be provided"}
    
    # Determine source type
    if file:
        filename = file.name.lower() if file.name else ""
        content_type = file.content_type
        
        if content_type == 'application/pdf' or filename.endswith('.pdf'):
            source_type = Document.SourceType.PDF
        elif filename.endswith('.docx'):
            source_type = Document.SourceType.DOCX
        elif filename.endswith('.csv'):
            source_type = Document.SourceType.CSV
        elif filename.endswith('.json'):
            source_type = Document.SourceType.JSON
        elif filename.endswith(('.md', '.markdown')):
            source_type = Document.SourceType.MARKDOWN
        elif filename.endswith(('.xlsx', '.xls')):
            source_type = Document.SourceType.EXCEL
        else:
            source_type = Document.SourceType.TEXT
    else:
        source_type = Document.SourceType.PASTE
    
    # Create document
    doc = Document.objects.create(
        company=company,
        title=title,
        source_type=source_type,
        file=file if file else None,
        raw_content=content if content else "",
        status=Document.Status.PENDING
    )
    
    # Queue processing task
    process_document_task.delay(str(doc.id))
    
    logger.info(f"Document created: {doc.title} (ID: {doc.id})")
    
    return {"id": doc.id, "message": "Document uploaded. Processing started."}


@router.get(
    "/documents/",
    response=List[DocumentOut],
    auth=ApiKeyAuth(),
    summary="List all documents",
    description="Retrieve a list of all documents for the authenticated company."
)
def list_documents(request, status: Optional[str] = None):
    """
    List all documents for this company.
    
    Args:
        status: Optional filter by status (pending, processing, completed, failed)
        
    Returns:
        List of documents
    """
    company = request.auth
    docs = Document.objects.filter(company=company)
    
    if status:
        docs = docs.filter(status=status)
    
    docs = docs.order_by('-created_at')
    
    return [
        DocumentOut(
            id=d.id,
            title=d.title,
            source_type=d.source_type,
            status=d.status,
            chunk_count=d.chunk_count,
            created_at=d.created_at.isoformat()
        ) for d in docs
    ]


@router.get(
    "/documents/{doc_id}/",
    response={200: DocumentOut, 404: ErrorResponse},
    auth=ApiKeyAuth(),
    summary="Get document details",
    description="Retrieve details of a specific document by ID."
)
def get_document(request, doc_id: uuid.UUID):
    """
    Get details of a specific document.
    
    Args:
        doc_id: UUID of the document
        
    Returns:
        Document details
    """
    company = request.auth
    doc = get_object_or_404(Document, id=doc_id, company=company)
    
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        status=doc.status,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at.isoformat()
    )


@router.delete(
    "/documents/{doc_id}/",
    response=MessageResponse,
    auth=ApiKeyAuth(),
    summary="Delete a document",
    description="Delete a document and all its associated chunks."
)
def delete_document(request, doc_id: uuid.UUID):
    """
    Delete a document and all its chunks.
    
    Args:
        doc_id: UUID of the document to delete
        
    Returns:
        Confirmation message
    """
    company = request.auth
    doc = get_object_or_404(Document, id=doc_id, company=company)
    title = doc.title
    doc.delete()
    
    logger.info(f"Document deleted: {title} (ID: {doc_id})")
    
    return {"message": f"Document '{title}' deleted"}