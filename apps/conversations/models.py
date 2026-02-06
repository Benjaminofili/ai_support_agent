import uuid
from typing import Optional

from django.db import models


class Conversation(models.Model):
    """
    A conversation thread with a customer.

    Attributes:
        id: Unique identifier (UUID)
        company: The company this conversation belongs to
        channel: Communication channel (web, whatsapp, email)
        customer_identifier: Unique identifier for the customer
        customer_name: Optional display name
        status: Current conversation status
    """

    class Channel(models.TextChoices):
        WEB = "web", "Website Chat"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"
        HANDED_OFF = "handed_off", "Handed Off to Human"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="conversations",
        db_index=True,  # ADD INDEX
    )

    channel = models.CharField(
        max_length=20, choices=Channel.choices, db_index=True  # ADD INDEX
    )
    customer_identifier = models.CharField(max_length=255, db_index=True)  # ADD INDEX
    customer_name = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,  # ADD INDEX
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # ADD INDEX
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            # Composite indexes for common queries
            models.Index(fields=["company", "status"]),
            models.Index(fields=["company", "-created_at"]),
            models.Index(fields=["company", "channel", "status"]),
            models.Index(fields=["customer_identifier", "company"]),
        ]
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self) -> str:
        return f"{self.channel} - {self.customer_identifier}"

    @property
    def message_count(self) -> int:
        """Get the number of messages in this conversation."""
        return self.messages.count()


class Message(models.Model):
    """
    A single message in a conversation.

    Attributes:
        id: Unique identifier (UUID)
        conversation: The parent conversation
        role: Who sent the message (customer, assistant, system)
        content: The message text
        source_chunks: Knowledge base chunks used to generate response
        metadata: Additional message data (e.g., subject for emails)
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        ASSISTANT = "assistant", "AI Assistant"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,  # ADD INDEX
    )

    role = models.CharField(
        max_length=20, choices=Role.choices, db_index=True  # ADD INDEX
    )
    content = models.TextField()

    source_chunks = models.ManyToManyField(
        "knowledge.DocumentChunk", blank=True, related_name="used_in_messages"
    )

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # ADD INDEX

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["conversation", "role"]),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:50]}..."
