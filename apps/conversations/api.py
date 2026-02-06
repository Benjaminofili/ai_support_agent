import uuid
from typing import List, Optional

from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.security import HttpBearer

from apps.companies.models import Company

from .models import Conversation, Message

router = Router()


class ApiKeyAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            company = Company.objects.get(api_key=token)
            return company
        except Company.DoesNotExist:
            return None


# --- Schemas ---
class ChatRequest(Schema):
    message: str
    session_id: Optional[str] = None


class ChatResponse(Schema):
    conversation_id: uuid.UUID
    session_id: str
    response: str


class MessageOut(Schema):
    role: str
    content: str
    created_at: str


class ConversationOut(Schema):
    id: uuid.UUID
    channel: str
    customer_identifier: str
    status: str
    message_count: int
    created_at: str


# --- Endpoints ---
@router.post("/message/", response=ChatResponse, auth=ApiKeyAuth())
def send_message(request, data: ChatRequest):
    """
    Website chat endpoint.
    Send a message and get an AI response.
    """
    company = request.auth
    conversation = None

    # Find existing conversation if session_id provided
    if data.session_id and data.session_id not in ("string", "", "null"):
        try:
            conversation = Conversation.objects.get(
                id=data.session_id, company=company, channel=Conversation.Channel.WEB
            )
        except (Conversation.DoesNotExist, ValueError, Exception):
            # Invalid session_id, we'll create a new conversation
            conversation = None

    # Create new conversation if needed
    if not conversation:
        conversation = Conversation.objects.create(
            company=company,
            channel=Conversation.Channel.WEB,
            customer_identifier=f"web_{uuid.uuid4().hex[:8]}",
        )

    # Save customer message
    Message.objects.create(
        conversation=conversation, role=Message.Role.CUSTOMER, content=data.message
    )

    # Generate AI response
    try:
        from .services import generate_response

        ai_response = generate_response(company, data.message, conversation)
    except Exception as e:
        ai_response = (
            f"AI is not configured yet. Your message: '{data.message}' was received."
        )

    # Save AI message
    Message.objects.create(
        conversation=conversation, role=Message.Role.ASSISTANT, content=ai_response
    )

    return ChatResponse(
        conversation_id=conversation.id,
        session_id=str(conversation.id),
        response=ai_response,
    )


@router.get("/conversations/", response=List[ConversationOut], auth=ApiKeyAuth())
def list_conversations(request, channel: Optional[str] = None):
    """List all conversations for this company."""
    company = request.auth
    convos = Conversation.objects.filter(company=company)

    if channel:
        convos = convos.filter(channel=channel)

    return [
        ConversationOut(
            id=c.id,
            channel=c.channel,
            customer_identifier=c.customer_identifier,
            status=c.status,
            message_count=c.messages.count(),
            created_at=c.created_at.isoformat(),
        )
        for c in convos
    ]


@router.get(
    "/conversations/{convo_id}/messages/", response=List[MessageOut], auth=ApiKeyAuth()
)
def get_conversation_messages(request, convo_id: uuid.UUID):
    """Get all messages in a conversation."""
    company = request.auth
    conversation = get_object_or_404(Conversation, id=convo_id, company=company)

    return [
        MessageOut(role=m.role, content=m.content, created_at=m.created_at.isoformat())
        for m in conversation.messages.all()
    ]
