import uuid
from typing import Optional

from django.contrib.auth.models import User
from django.db import models


class Company(models.Model):
    """
    Represents a B2B client company.

    All documents and conversations belong to a company.
    Multi-tenancy is achieved by filtering all queries by company.

    Attributes:
        id: Unique identifier (UUID)
        name: Company display name
        slug: URL-friendly identifier
        owner: Admin user for this company
        api_key: Authentication key for API access
        ai_personality: Custom instructions for AI responses
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)  # ADD INDEX
    slug = models.SlugField(unique=True, db_index=True)  # Already indexed (unique)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_companies",
        db_index=True,  # ADD INDEX
    )

    api_key = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        db_index=True,  # Already indexed (unique)
    )

    ai_personality = models.TextField(
        default="You are a helpful customer support agent. Be concise and friendly.",
        help_text="Custom instructions for how the AI should respond",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def save(self, *args, **kwargs) -> None:
        """Generate API key if not set."""
        if not self.api_key:
            self.api_key = uuid.uuid4().hex + uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    @property
    def document_count(self) -> int:
        """Get the number of documents for this company."""
        return self.documents.count()

    @property
    def conversation_count(self) -> int:
        """Get the number of conversations for this company."""
        return self.conversations.count()
