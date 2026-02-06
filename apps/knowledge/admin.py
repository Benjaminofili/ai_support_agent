from django.contrib import admin

from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "company",
        "source_type",
        "status",
        "chunk_count",
        "created_at",
    ]
    list_filter = ["status", "source_type", "company"]
    search_fields = ["title"]
    readonly_fields = ["id", "chunk_count", "created_at", "updated_at"]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ["document", "chunk_index", "created_at"]
    list_filter = ["document__company"]
    readonly_fields = ["id", "embedding", "created_at"]
