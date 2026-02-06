import json
import logging

from django.conf import settings
from django.http import HttpResponse
from ninja import Router, Schema

logger = logging.getLogger(__name__)
router = Router()


def validate_twilio_request(request) -> bool:
    """
    Validate that the request came from Twilio.
    Returns True if valid or if validation is disabled in development/testing.
    """
    # Skip validation in DEBUG mode or during tests
    if settings.DEBUG:
        return True

    # Skip validation if credentials not set
    if not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio validation skipped: No auth token configured")
        return True

    try:
        from twilio.request_validator import RequestValidator

        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)

        # Get the full URL
        url = request.build_absolute_uri()

        # Get Twilio signature
        signature = request.META.get("HTTP_X_TWILIO_SIGNATURE", "")

        # If no signature provided, skip validation in dev
        if not signature:
            logger.debug("No Twilio signature provided")
            return settings.DEBUG

        # Validate
        is_valid = validator.validate(url, request.POST.dict(), signature)

        if not is_valid:
            logger.warning(
                f"Invalid Twilio signature from {request.META.get('REMOTE_ADDR')}"
            )

        return is_valid

    except Exception as e:
        logger.error(f"Twilio validation error: {e}")
        return settings.DEBUG  # Allow in debug mode


@router.post("/whatsapp/")
def whatsapp_webhook(request):
    """
    Receives incoming WhatsApp messages from Twilio.

    Security: Validates Twilio request signature in production.
    CSRF exempt: Twilio webhooks don't include session cookies.
    """
    from twilio.twiml.messaging_response import MessagingResponse

    from .tasks import process_whatsapp_message_task

    # Validate request (skipped in DEBUG mode)
    if not validate_twilio_request(request):
        logger.warning("Rejected invalid Twilio webhook request")
        return HttpResponse(status=403)

    # Extract message data
    from_number = request.POST.get("From", "")
    to_number = request.POST.get("To", "")
    body = request.POST.get("Body", "")
    message_sid = request.POST.get("MessageSid", "")

    logger.info(f"WhatsApp message received from {from_number}: {body[:50]}...")

    if body.strip():
        process_whatsapp_message_task.delay(
            from_number=from_number,
            to_number=to_number,
            body=body,
            message_sid=message_sid,
        )
        logger.info(f"Task queued for message {message_sid}")

    # Return empty TwiML response
    response = MessagingResponse()
    return HttpResponse(str(response), content_type="application/xml")


# Email Test Schema
class EmailTestRequest(Schema):
    """Schema for testing email functionality."""

    from_email: str
    subject: str
    body: str


@router.post("/email/test/")
def email_test_endpoint(request, data: EmailTestRequest):
    """
    Test endpoint to simulate incoming email.
    For demo purposes - manually trigger email responses.
    """
    from .tasks import process_email_message_task

    logger.info(f"Test email triggered from: {data.from_email}")

    process_email_message_task.delay(
        from_email=data.from_email, subject=data.subject, body=data.body
    )

    return {"status": "queued", "message": "Email processing started."}


@router.post("/email/")
def email_webhook(request):
    """
    Receives incoming emails (for inbound email setup).
    Handles both JSON and form data formats.
    """
    from .tasks import process_email_message_task

    try:
        # Handle both JSON and form data
        if request.content_type == "application/json":
            data = json.loads(request.body)
            from_email = data.get("from", data.get("from_email", ""))
            subject = data.get("subject", "No Subject")
            body = data.get("text", data.get("body", ""))
        else:
            from_email = request.POST.get("from", "")
            subject = request.POST.get("subject", "No Subject")
            body = request.POST.get("text", request.POST.get("body", ""))

        # Extract email from "Name <email>" format
        import re

        email_match = re.search(r"<(.+?)>", from_email)
        if email_match:
            from_email = email_match.group(1)

        logger.info(f"Email webhook received from: {from_email}")

        if body.strip() and from_email:
            process_email_message_task.delay(
                from_email=from_email, subject=subject, body=body
            )

        return HttpResponse("OK", status=200)

    except Exception as e:
        logger.error(f"Email webhook error: {e}", exc_info=True)
        return HttpResponse("Error", status=500)
