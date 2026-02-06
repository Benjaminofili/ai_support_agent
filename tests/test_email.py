"""
Test email sending with Resend
Run: python test_email.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.channels.tasks import process_email_message_task


def test_email():
    print("Testing email functionality...")
    
    # Simulate incoming email
    result = process_email_message_task(
        from_email="playbetgenius@gmail.com",  # Change to your real email to receive response
        subject="Test Support Question",
        body="What are your business hours?"
    )
    
    print(f"Result: {result}")


if __name__ == '__main__':
    test_email()