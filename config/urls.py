import logging

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import path, include
from django.views.generic import RedirectView
from ninja import NinjaAPI

from apps.channels.webhooks import router as webhooks_router
from apps.conversations.api import router as chat_router
from apps.knowledge.api import router as knowledge_router

logger = logging.getLogger(__name__)

# =============================================================================
# API CONFIGURATION WITH DOCUMENTATION
# =============================================================================

# Hack to fix NinjaAPI autoreload issue
# NinjaAPI registers itself globally. On reload, it claims duplication.
# We clear the specific registry key before creating a new instance.
if "api-1.0.0" in NinjaAPI._registry:
    NinjaAPI._registry.remove("api-1.0.0")

api = NinjaAPI(
    title="AI Support Agent API",
    version="1.0.0",
    description="""
## AI-Powered Customer Support Agent

This API provides endpoints for a B2B SaaS customer support system using
Retrieval-Augmented Generation (RAG).

### Features:
- **Knowledge Base Management**: Upload and process documents for AI context
- **Chat Interface**: Send messages and receive AI-generated responses with source citations
- **Multi-Channel Support**: WhatsApp and Email webhooks for seamless integration

### Authentication:
All endpoints require Bearer token authentication using your company API key.

**Header Format:**
```
Authorization: Bearer YOUR_API_KEY
```

### Rate Limiting:
- Standard tier: 100 requests per minute
- Enterprise tier: 1000 requests per minute

### Getting Started:
1. Obtain your API key from the admin dashboard
2. Upload knowledge base documents via `/api/knowledge/documents/`
3. Start chatting via `/api/chat/send/`

### Support:
For questions or issues, contact support@yourdomain.com
    """,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Add routers with tags for better organization
# Fix for Django Ninja double-attach issue during autoreload
for router in [knowledge_router, chat_router, webhooks_router]:
    if hasattr(router, "api"):
        router.api = None

api.add_router("/knowledge/", knowledge_router, tags=["Knowledge Base"])
api.add_router("/chat/", chat_router, tags=["Chat"])
api.add_router("/webhooks/", webhooks_router, tags=["Webhooks"])


def health_check(request):
    """
    Health check endpoint for monitoring service availability.
    
    Returns the status of critical system components including:
    - Overall system status
    - Database connectivity
    - Redis/Cache connectivity
    
    **Response Codes:**
    - 200: All systems operational
    - 503: One or more systems degraded
    
    **Example Response:**
```json
    {
        "status": "ok",
        "database": "connected",
        "redis": "connected"
    }
```
    """
    status = {
        "status": "ok",
        "database": "unknown",
        "redis": "unknown",
    }

    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        status["database"] = f"error: {str(e)}"
        status["status"] = "degraded"

    try:
        # Test Redis connection
        import redis

        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        status["redis"] = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        status["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"

    http_status = 200 if status["status"] == "ok" else 503
    return JsonResponse(status, status=http_status)


# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("health/", health_check, name="health_check"),
    # Authentication URLs
    path("", include("apps.companies.auth_urls")),
    # Dashboard URLs
    path("dashboard/", include("apps.companies.urls")),
    # Default redirect to login
    path("", RedirectView.as_view(pattern_name="login"), name="root"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)