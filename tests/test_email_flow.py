"""
Test complete email flow with AI response
Run: python test_email_flow.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.channels.tasks import process_email_message_task
from django.conf import settings


def test_email_with_ai():
    """Test email processing with AI response."""
    
    print("="*70)
    print("  AI EMAIL RESPONSE TESTING")
    print("="*70)
    
    print("\n📧 EMAIL CONFIGURATION:")
    print(f"From: {settings.EMAIL_HOST_USER}")
    
    # Get recipient
    print("\n📮 RECIPIENT OPTIONS:")
    print("1. Send to yourself")
    print("2. Send to teacher/evaluator")
    print("3. Custom email address")
    
    choice = input("\nSelect (1-3): ").strip()
    
    if choice == '1':
        recipient = settings.EMAIL_HOST_USER
    elif choice == '2':
        recipient = input("Enter teacher's email: ").strip()
    elif choice == '3':
        recipient = input("Enter email address: ").strip()
    else:
        recipient = settings.EMAIL_HOST_USER
    
    if not recipient or '@' not in recipient:
        print("❌ Invalid email")
        return
    
    print(f"\n📬 Recipient: {recipient}")
    
    # Select or create question
    print("\n❓ TEST QUESTIONS:")
    questions = [
        "What is your return policy?",
        "What are your business hours?",
        "How long does shipping take?",
        "What payment methods do you accept?",
        "How do I contact customer support?",
        "Do you offer international shipping?",
        "What is your warranty policy?",
        "Can I cancel my order?",
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")
    print("9. Custom question")
    
    q_choice = input("\nSelect question (1-9): ").strip()
    
    if q_choice == '9':
        question = input("Enter your question: ").strip()
    elif q_choice.isdigit() and 1 <= int(q_choice) <= len(questions):
        question = questions[int(q_choice) - 1]
    else:
        question = questions[0]
    
    print("\n" + "="*70)
    print(f"📧 Processing Email:")
    print(f"To: {recipient}")
    print(f"Question: {question}")
    print("="*70)
    
    print("\n⏳ Generating AI response...")
    
    # Process email (synchronous for testing)
    try:
        result = process_email_message_task(
            from_email=recipient,
            subject=f"Customer Query: {question[:30]}...",
            body=question
        )
        
        print("\n" + "="*70)
        print("📊 RESULT:")
        print("="*70)
        
        if result.get('status') == 'sent':
            print(f"✅ SUCCESS! Email sent to {recipient}")
            print("\n📬 Check the inbox for:")
            print(f"  Subject: Re: Customer Query: {question[:30]}...")
            print(f"  Content: AI-generated response based on knowledge base")
            
            # Show what was sent
            from apps.conversations.models import Message
            last_message = Message.objects.filter(
                role=Message.Role.ASSISTANT,
                conversation__customer_identifier=recipient
            ).last()
            
            if last_message:
                print("\n💬 AI Response Preview:")
                print("-"*50)
                print(last_message.content[:200] + "..." if len(last_message.content) > 200 else last_message.content)
                print("-"*50)
        else:
            print(f"❌ Error: {result.get('message')}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)


def quick_test():
    """Quick test with default settings."""
    
    print("\n🚀 QUICK EMAIL TEST")
    print("="*50)
    
    from apps.channels.tasks import send_email_response
    
    result = send_email_response(
        to_email=settings.EMAIL_HOST_USER,
        subject="Quick Test",
        message="This is a quick test of the email system. If you receive this, everything is working!"
    )
    
    if result.get('status') == 'sent':
        print(f"✅ Email sent to {settings.EMAIL_HOST_USER}")
    else:
        print(f"❌ Failed: {result.get('message')}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  AI SUPPORT AGENT - EMAIL FLOW TESTING")
    print("="*70)
    
    print("\n1. Full AI response test")
    print("2. Quick email test")
    
    choice = input("\nSelect (1-2): ").strip()
    
    if choice == '2':
        quick_test()
    else:
        test_email_with_ai()