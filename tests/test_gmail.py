"""
Test Gmail SMTP email sending
Run: python test_gmail.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings


def test_gmail_smtp():
    """Test sending email via Gmail SMTP."""
    
    print("="*60)
    print("Testing Gmail SMTP Configuration")
    print("="*60)
    
    # Check configuration
    print(f"\nEmail Backend: {settings.EMAIL_BACKEND}")
    print(f"SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"From Email: {settings.EMAIL_HOST_USER}")
    print(f"TLS Enabled: {settings.EMAIL_USE_TLS}")
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ ERROR: Email credentials not configured!")
        print("Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
        return False
    
    # Send test email
    try:
        print("\n📧 Sending test email...")
        
        send_mail(
            subject='AI Support Agent - Test Email',
            message='This is a test email from your AI Support Agent system.\n\nIf you received this, Gmail SMTP is working correctly!',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself first
            fail_silently=False,
        )
        
        print(f"✅ SUCCESS! Test email sent to {settings.EMAIL_HOST_USER}")
        print("\nCheck your inbox (including spam folder)")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nCommon issues:")
        print("1. App Password not generated or incorrect")
        print("2. 2-Step Verification not enabled")
        print("3. IMAP/SMTP not enabled in Gmail settings")
        return False


def test_custom_email():
    """Test sending email to any address."""
    
    print("\n" + "="*60)
    print("Send Test Email to Custom Address")
    print("="*60)
    
    recipient_email = input("\nEnter recipient email address: ").strip()
    
    if not recipient_email or '@' not in recipient_email:
        print("❌ Invalid email address")
        return False
    
    print("\nEmail Type:")
    print("1. Simple test email")
    print("2. AI System demo (for teacher/evaluator)")
    print("3. Custom message")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        subject = 'AI Support Agent - Test Email'
        message = f'''Hello,

This is a test email from the AI Support Agent system.

If you're receiving this, the email integration is working correctly!

System Details:
- Sent from: {settings.EMAIL_HOST_USER}
- Using: Gmail SMTP
- Django Email Backend

Best regards,
AI Support Agent
'''
    
    elif choice == '2':
        subject = 'AI Support Agent Demo - Student Project'
        message = '''Hello,

I'm demonstrating my AI-powered customer support system as part of my project.

🤖 PROJECT OVERVIEW:
This system automatically responds to customer inquiries using Retrieval-Augmented Generation (RAG).

📚 KEY FEATURES:
- Document ingestion and processing
- Semantic search using vector embeddings
- Multi-channel support (WhatsApp, Email, Web Chat)
- Async processing with Celery
- Knowledge base management

🛠 TECH STACK:
- Backend: Django + Django Ninja API
- AI: HuggingFace (embeddings) + Groq LLaMA 3.1 (chat)
- Database: PostgreSQL with pgvector extension
- Queue: Celery + Redis
- Integrations: Twilio (WhatsApp), Gmail SMTP (Email)

💡 HOW IT WORKS:
1. Companies upload their documents (PDFs, text files, etc.)
2. System processes documents into searchable chunks
3. When customers ask questions, AI searches relevant information
4. Generates contextual responses using only company knowledge

This email demonstrates the email integration component of the system.

Best regards,
Your Student's AI Support Agent
'''
    
    elif choice == '3':
        subject = input("Enter email subject: ").strip()
        print("\nEnter your message (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == '':
                break
            lines.append(line)
        message = '\n'.join(lines)
    
    else:
        print("❌ Invalid option")
        return False
    
    try:
        print(f"\n📧 Sending email to {recipient_email}...")
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        print(f"✅ SUCCESS! Email sent to {recipient_email}")
        print("\nThe recipient should receive it within seconds!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPossible issues:")
        print("1. Gmail may block if it looks like spam")
        print("2. Check your app password is correct")
        print("3. The recipient's email server might be blocking")
        return False


def test_multiple_recipients():
    """Test sending to multiple recipients at once."""
    
    print("\n" + "="*60)
    print("Send Email to Multiple Recipients")
    print("="*60)
    
    recipients = []
    print("\nEnter email addresses (press Enter after each, blank line to finish):")
    
    while True:
        email = input(f"Email {len(recipients) + 1}: ").strip()
        if not email:
            break
        if '@' in email:
            recipients.append(email)
        else:
            print("  ⚠️  Invalid email, skipping...")
    
    if not recipients:
        print("❌ No valid recipients entered")
        return False
    
    print(f"\n📋 Will send to {len(recipients)} recipient(s):")
    for email in recipients:
        print(f"  - {email}")
    
    confirm = input("\nConfirm send? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return False
    
    try:
        print(f"\n📧 Sending emails...")
        
        send_mail(
            subject='AI Support Agent - Multi-Recipient Test',
            message=f'''Hello,

This is a test email from the AI Support Agent system sent to multiple recipients.

This demonstrates the system's ability to handle multiple email notifications simultaneously.

Recipients in this batch: {len(recipients)}

Best regards,
AI Support Agent System
''',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipients,
            fail_silently=False,
        )
        
        print(f"✅ SUCCESS! Email sent to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main_menu():
    """Main menu for email testing."""
    
    print("\n" + "="*70)
    print("  AI SUPPORT AGENT - EMAIL TESTING SUITE")
    print("="*70)
    
    while True:
        print("\n📧 EMAIL TEST OPTIONS:")
        print("1. Test basic configuration (send to yourself)")
        print("2. Send to custom email address")
        print("3. Send to multiple recipients")
        print("4. Test AI email response flow")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            test_gmail_smtp()
        
        elif choice == '2':
            test_custom_email()
        
        elif choice == '3':
            test_multiple_recipients()
        
        elif choice == '4':
            print("\n💡 To test AI email response flow, run:")
            print("   python test_email_flow.py")
            print("\nThis will simulate a customer email and generate an AI response.")
        
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option")
        
        if choice in ['1', '2', '3']:
            input("\nPress Enter to continue...")


if __name__ == '__main__':
    # Check if configuration exists
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("❌ ERROR: Email not configured!")
        print("\nPlease add to your .env file:")
        print("EMAIL_HOST_USER=your-gmail@gmail.com")
        print("EMAIL_HOST_PASSWORD=your-16-char-app-password")
    else:
        main_menu()