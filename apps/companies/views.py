"""
Company views for dashboard and management.
"""

import logging
from typing import Any, Dict, Optional

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.http import HttpRequest,JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods


from apps.conversations.models import Conversation, Message
from apps.knowledge.models import Document, DocumentChunk

from .models import Company

logger = logging.getLogger(__name__)


def get_company(request: HttpRequest) -> Optional[Company]:
    """
    Get the company for the current request.

    For authenticated users, returns their owned company.
    For unauthenticated requests, returns the first company (demo mode).

    Args:
        request: The HTTP request

    Returns:
        Company instance or None if not found
    """
    if request.user.is_authenticated:
        company = Company.objects.select_related('owner').filter(
            owner=request.user
        ).first()
        if company:
            return company

    return Company.objects.first()


def get_stats(company: Company) -> Dict[str, Any]:
    """
    Get statistics for a company dashboard.

    Uses optimized queries with aggregation to avoid N+1 problems.

    Args:
        company: The company to get stats for

    Returns:
        Dict containing document, chunk, conversation, and message counts
    """
    # Document stats
    total_documents = Document.objects.filter(company=company).count()
    completed_documents = Document.objects.filter(company=company, status="completed").count()
    pending_documents = Document.objects.filter(company=company, status="pending").count()
    failed_documents = Document.objects.filter(company=company, status="failed").count()
    
    # Chunk count
    chunk_count = DocumentChunk.objects.filter(document__company=company).count()
    
    # Conversation stats
    total_conversations = Conversation.objects.filter(company=company).count()
    active_conversations = Conversation.objects.filter(company=company, status="active").count()
    
    # Message count
    total_messages = Message.objects.filter(conversation__company=company).count()
    
    # Channel breakdown
    whatsapp_conversations = Conversation.objects.filter(company=company, channel="whatsapp").count()
    web_conversations = Conversation.objects.filter(company=company, channel="web").count()
    email_conversations = Conversation.objects.filter(company=company, channel="email").count()

    stats = {
        # Document stats
        "total_documents": total_documents,
        "document_count": total_documents,  # Alias for compatibility
        "completed_documents": completed_documents,
        "pending_documents": pending_documents,
        "failed_documents": failed_documents,
        "chunk_count": chunk_count,
        
        # Conversation stats
        "total_conversations": total_conversations,
        "conversation_count": total_conversations,  # Alias for compatibility
        "active_conversations": active_conversations,
        
        # Message stats
        "total_messages": total_messages,
        "message_count": total_messages,  # Alias for compatibility
        
        # Channel breakdown
        "whatsapp_conversations": whatsapp_conversations,
        "web_conversations": web_conversations,
        "email_conversations": email_conversations,
        
        # Channel breakdown dict (for charts)
        "channel_breakdown": {
            "whatsapp": whatsapp_conversations,
            "web": web_conversations,
            "email": email_conversations,
        },
    }

    logger.debug(f"Stats for company {company.id}: {stats}")

    return stats


def get_base_context(request: HttpRequest, company: Company) -> Dict[str, Any]:
    """
    Get base context that's needed for all dashboard views.
    
    Args:
        request: The HTTP request
        company: The company instance
        
    Returns:
        Dict with company, api_key, and stats
    """
    stats = get_stats(company)
    
    return {
        "company": company,
        "api_key": company.api_key,
        "stats": stats,
    }


@login_required
def dashboard(request: HttpRequest):
    """
    Main dashboard view with company statistics.

    Displays:
    - Document counts and status
    - Conversation statistics
    - Recent conversations with messages (prefetched)
    """
    company = get_company(request)

    if not company:
        logger.warning(f"No company found for user {request.user.id}")
        return render(request, "dashboard/no_company.html")

    # Get base context with company, api_key, and stats
    context = get_base_context(request, company)

    # Get recent documents with single query
    recent_documents = Document.objects.filter(
        company=company
    ).order_by("-created_at")[:10]

    # Get recent conversations with prefetched messages (avoids N+1)
    recent_conversations = (
        Conversation.objects.filter(company=company)
        .select_related("company")
        .prefetch_related(
            Prefetch(
                "messages", 
                queryset=Message.objects.order_by("-created_at")[:5]
            )
        )
        .annotate(num_messages=Count("messages"))
        .order_by("-updated_at")[:10]
    )

    context.update({
        "recent_documents": recent_documents,
        "recent_conversations": recent_conversations,
    })

    return render(request, "dashboard/index.html", context)


@login_required
def conversation_detail(request: HttpRequest, conversation_id: str):
    """
    View a single conversation with all messages.

    Uses select_related and prefetch_related to optimize queries.
    
    Args:
        request: The HTTP request
        conversation_id: UUID of the conversation
    """
    company = get_company(request)

    if not company:
        return render(request, "dashboard/no_company.html")

    # Get conversation with optimized query
    conversation = get_object_or_404(
        Conversation.objects.select_related("company").prefetch_related(
            Prefetch(
                "messages", 
                queryset=Message.objects.order_by("created_at")
            )
        ),
        id=conversation_id,
        company=company,
    )

    # Get base context
    context = get_base_context(request, company)
    
    context.update({
        "conversation": conversation,
        "messages": conversation.messages.all(),
    })

    return render(request, "dashboard/conversation_detail.html", context)


@login_required
def document_list(request: HttpRequest):
    """
    List all documents for the company.

    Includes chunk counts using annotation.
    """
    company = get_company(request)

    if not company:
        return render(request, "dashboard/no_company.html")

    documents = (
        Document.objects.filter(company=company)
        .annotate(chunk_count_actual=Count("chunks"))
        .order_by("-created_at")
    )

    # Get base context
    context = get_base_context(request, company)
    
    context.update({
        "documents": documents,
    })

    return render(request, "dashboard/documents.html", context)


@login_required
def document_detail(request: HttpRequest, document_id: str):
    """
    View a single document with its chunks.

    Args:
        request: The HTTP request
        document_id: UUID of the document
    """
    company = get_company(request)

    if not company:
        return render(request, "dashboard/no_company.html")

    document = get_object_or_404(
        Document.objects.prefetch_related("chunks"),
        id=document_id,
        company=company,
    )

    # Get base context
    context = get_base_context(request, company)
    
    context.update({
        "document": document,
        "chunks": document.chunks.all(),
    })

    return render(request, "dashboard/document_detail.html", context)


def demo_dashboard(request: HttpRequest):
    """
    Public demo dashboard view.
    """
    company = Company.objects.first()
    
    if not company:
        return render(request, "dashboard/no_company.html")

    # Get base context
    context = get_base_context(request, company)

    recent_documents = Document.objects.filter(
        company=company
    ).order_by("-created_at")[:5]

    recent_conversations = (
        Conversation.objects.filter(company=company)
        .select_related("company")
        .prefetch_related(
            Prefetch(
                "messages", 
                queryset=Message.objects.order_by("-created_at")[:1]
            )
        )
        .annotate(num_messages=Count("messages"))
        .order_by("-updated_at")[:5]
    )

    context.update({
        "recent_documents": recent_documents,
        "recent_conversations": recent_conversations,
        "is_demo": True,
    })

    return render(request, "dashboard/index.html", context)


@login_required
def conversations_list(request: HttpRequest):
    """
    List all conversations with optional filtering.
    """
    company = get_company(request)
    if not company:
        return render(request, "dashboard/no_company.html")

    channel = request.GET.get("channel")
    
    queryset = Conversation.objects.filter(
        company=company
    ).select_related("company").prefetch_related(
        "messages"
    ).annotate(
        num_messages=Count("messages")
    ).order_by("-updated_at")

    if channel:
        queryset = queryset.filter(channel=channel)

    # Get base context with stats
    context = get_base_context(request, company)
    
    context.update({
        "conversations": queryset,
        "current_channel": channel,
    })

    return render(request, "dashboard/conversations.html", context)


@login_required
def documents_upload(request: HttpRequest):
    """
    View for uploading new documents.
    """
    company = get_company(request)
    if not company:
        return render(request, "dashboard/no_company.html")
    
    # Get base context with api_key and stats
    context = get_base_context(request, company)
    
    # Get existing documents for the list
    documents = Document.objects.filter(company=company).order_by("-created_at")
    context["documents"] = documents
    
    return render(request, "dashboard/upload.html", context)


@login_required
def settings_page(request: HttpRequest):
    """
    View for company settings.
    """
    company = get_company(request)
    if not company:
        return render(request, "dashboard/no_company.html")
    
    # Get base context
    context = get_base_context(request, company)
    
    return render(request, "dashboard/settings.html", context)


@login_required
def dashboard_config(request: HttpRequest):
    """
    View for dashboard configuration (placeholder).
    """
    company = get_company(request)
    if not company:
        return render(request, "dashboard/no_company.html")
    
    # Get base context
    context = get_base_context(request, company)
    
    return render(request, "dashboard/settings.html", context)


def chat_widget(request: HttpRequest):
    """
    Render the embeddable chat widget.
    This can be accessed publicly to test the chat interface.
    """
    # Get the company from query param or use first one
    company_id = request.GET.get('company')
    
    if company_id:
        company = Company.objects.filter(id=company_id).first()
    else:
        company = Company.objects.first()
    
    if not company:
        return render(request, "dashboard/no_company.html")
    
    context = {
        "company": company,
        "api_key": company.api_key,
    }
    
    return render(request, "chat/widget.html", context)



@login_required
@require_http_methods(["GET"])
def api_config_check(request):
    """
    Check API configuration for debugging.
    Returns the current user's company and API key status.
    """
    company = get_company(request)
    
    if not company:
        return JsonResponse({
            'status': 'error',
            'message': 'No company found for user',
            'user': request.user.username if request.user.is_authenticated else 'Anonymous'
        }, status=404)
    
    # Get stats
    stats = get_stats(company)
    
    return JsonResponse({
        'status': 'ok',
        'company': {
            'id': str(company.id),
            'name': company.name,
            'slug': company.slug,
            'owner': company.owner.username,
        },
        'api_key': {
            'exists': bool(company.api_key),
            'prefix': company.api_key[:8] + '...' if company.api_key else None,
            'length': len(company.api_key) if company.api_key else 0,
        },
        'stats': stats,
        'endpoints': {
            'upload': '/api/knowledge/documents/upload/',
            'documents': '/api/knowledge/documents/',
            'chat': '/api/chat/conversations/',
            'whatsapp': '/api/webhooks/whatsapp/',
            'email': '/api/webhooks/email/test/',
        },
        'user': {
            'username': request.user.username,
            'is_authenticated': request.user.is_authenticated,
            'is_staff': request.user.is_staff,
        }
    })