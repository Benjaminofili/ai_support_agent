import uuid
from typing import List

from django.conf import settings
from django.db import models
from pgvector.django import VectorField

# Constants
EMBEDDING_DIMENSIONS = getattr(settings, "EMBEDDING_DIMENSIONS", 384)


class Document(models.Model):
    """
    A document uploaded by a company.

    Documents are processed into chunks, which are then embedded
    for semantic search during RAG (Retrieval-Augmented Generation).

    Attributes:
        id: Unique identifier (UUID)
        company: The company that owns this document
        title: Human-readable document title
        source_type: Type of document (pdf, text, paste, etc.)
        file: Optional uploaded file
        raw_content: Optional pasted content
        status: Processing status
        error_message: Error details if processing failed
        chunk_count: Number of chunks created from this document
    """

    class SourceType(models.TextChoices):
        PDF = "pdf", "PDF File"
        TEXT = "text", "Text File"
        MARKDOWN = "markdown", "Markdown File"
        DOCX = "docx", "Word Document"
        CSV = "csv", "CSV File"
        JSON = "json", "JSON File"
        EXCEL = "excel", "Excel File"
        PASTE = "paste", "Pasted Content"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="documents",
        db_index=True,  # ADD INDEX
    )

    title = models.CharField(max_length=255, db_index=True)  # ADD INDEX
    source_type = models.CharField(
        max_length=10, choices=SourceType.choices, db_index=True  # ADD INDEX
    )
    file = models.FileField(upload_to="documents/", null=True, blank=True)
    raw_content = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,  # ADD INDEX
    )
    error_message = models.TextField(blank=True)
    chunk_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # ADD INDEX
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["company", "-created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self) -> str:
        return f"{self.company.name} - {self.title}"


class DocumentChunk(models.Model):
    """
    A chunk of text from a document, with its vector embedding.

    Chunks are used for semantic search during RAG to find
    relevant context for answering questions.

    Attributes:
        id: Unique identifier (UUID)
        document: The parent document
        content: The text content of this chunk
        chunk_index: Position of this chunk in the document
        embedding: Vector embedding for semantic search
        metadata: Additional chunk data (source, page number, etc.)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks",
        db_index=True,  # ADD INDEX
    )

    content = models.TextField()
    chunk_index = models.IntegerField(db_index=True)  # ADD INDEX

    # Vector embedding - dimensions based on model used
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
        ]
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"

    def __str__(self) -> str:
        return f"Chunk {self.chunk_index} of {self.document.title}"
