"""
Channel tasks for processing incoming messages.

Handles WhatsApp and Email message processing asynchronously.
"""

import logging
from typing import Any, Dict

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from apps.companies.models import Company
from apps.conversations.models import Conversation, Message
from apps.conversations.services import generate_response

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, time_limit=120)
def process_whatsapp_message_task(
    self, from_number: str, to_number: str, body: str, message_sid: str
) -> Dict[str, Any]:
    """
    Process incoming WhatsApp message.

    Pipeline:
    1. Find or create conversation
    2. Save customer message
    3. Generate AI response
    4. Save AI response
    5. Send response via Twilio

    Args:
        from_number: Customer's WhatsApp number
        to_number: Our WhatsApp number
        body: Message content
        message_sid: Twilio message ID

    Returns:
        Dict with status and details
    """
    logger.info(f"Processing WhatsApp from {from_number}: {body[:50]}...")

    try:
        # Get company (for MVP, use first company)
        company = Company.objects.first()
        if not company:
            logger.error("No company configured")
            return {"status": "error", "message": "No company configured"}

        # Find or create conversation
        conversation, created = Conversation.objects.get_or_create(
            company=company,
            channel=Conversation.Channel.WHATSAPP,
            customer_identifier=from_number,
            defaults={"status": Conversation.Status.ACTIVE},
        )

        if created:
            logger.info(f"New WhatsApp conversation: {conversation.id}")

        # Save customer message
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.CUSTOMER,
            content=body,
            metadata={"message_sid": message_sid},
        )
        logger.debug("Customer message saved")

        # Generate AI response
        logger.info("Generating AI response...")
        ai_response = generate_response(company, body, conversation)
        logger.info(f"AI response: {ai_response[:50]}...")

        # Save AI response
        Message.objects.create(
            conversation=conversation, role=Message.Role.ASSISTANT, content=ai_response
        )

        # Send response via Twilio
        return send_twilio_message(from_number, ai_response)

    except Exception as e:
        logger.error(f"WhatsApp processing error: {e}", exc_info=True)

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30 * (2**self.request.retries))

        return {"status": "error", "message": str(e)}


def send_twilio_message(to_number: str, message: str) -> Dict[str, Any]:
    """
    Send a WhatsApp message via Twilio.

    Args:
        to_number: Recipient's WhatsApp number
        message: Message content

    Returns:
        Dict with status and message SID
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.error("Twilio credentials not configured")
        return {"status": "error", "message": "Twilio not configured"}

    try:
        from twilio.rest import Client as TwilioClient

        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        logger.info(f"Sending to: {to_number}, from: {settings.TWILIO_WHATSAPP_NUMBER}")

        twilio_message = client.messages.create(
            body=message, from_=settings.TWILIO_WHATSAPP_NUMBER, to=to_number
        )

        logger.info(f"Message sent! SID: {twilio_message.sid}")
        return {"status": "sent", "message_sid": twilio_message.sid}

    except Exception as e:
        logger.error(f"Twilio send error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, max_retries=3, time_limit=120)
def process_email_message_task(
    self, from_email: str, subject: str, body: str
) -> Dict[str, Any]:
    """
    Process incoming email message.

    Pipeline:
    1. Find or create conversation
    2. Save customer message
    3. Generate AI response
    4. Save AI response
    5. Send response via Gmail SMTP

    Args:
        from_email: Customer's email address
        subject: Email subject
        body: Email body content

    Returns:
        Dict with status and details
    """
    logger.info(f"Processing email from {from_email}: {subject}")

    try:
        # Get company
        company = Company.objects.first()
        if not company:
            logger.error("No company configured")
            return {"status": "error", "message": "No company configured"}

        # Find or create conversation
        conversation, created = Conversation.objects.get_or_create(
            company=company,
            channel=Conversation.Channel.EMAIL,
            customer_identifier=from_email,
            defaults={"status": Conversation.Status.ACTIVE},
        )

        if created:
            logger.info(f"New email conversation: {conversation.id}")

        # Save customer message
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.CUSTOMER,
            content=body,
            metadata={"subject": subject},
        )
        logger.debug("Customer email saved")

        # Generate AI response
        logger.info("Generating AI response...")
        ai_response = generate_response(company, body, conversation)
        logger.info(f"AI response: {ai_response[:50]}...")

        # Save AI response
        Message.objects.create(
            conversation=conversation, role=Message.Role.ASSISTANT, content=ai_response
        )

        # Send response via email
        return send_email_response(from_email, subject, ai_response)

    except Exception as e:
        logger.error(f"Email processing error: {e}", exc_info=True)

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30 * (2**self.request.retries))

        return {"status": "error", "message": str(e)}


def send_email_response(to_email: str, subject: str, message: str) -> Dict[str, Any]:
    """
    Send an email response via Django's email backend (Gmail SMTP).

    Args:
        to_email: Recipient's email address
        subject: Original email subject
        message: Response content

    Returns:
        Dict with status
    """
    try:
        # Validate email configuration
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            logger.error("Email credentials not configured")
            return {"status": "error", "message": "Email not configured"}

        from_email = settings.DEFAULT_FROM_EMAIL
        reply_subject = f"Re: {subject}"

        logger.info(f"Sending email to: {to_email}")
        logger.debug(f"From: {from_email}, Subject: {reply_subject}")

        # Send email using Django's send_mail
        send_mail(
            subject=reply_subject,
            message=message,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )

        logger.info(f"[OK] Email sent to {to_email}")
        return {"status": "sent", "to": to_email}

    except Exception as e:
        logger.error(f"Email send error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
