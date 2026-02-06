"""
AI Customer Support Agent - Complete Test Suite
Unit Tests → Integration Tests

Run: python manage.py test tests
Or run directly: python tests/test_suite.py
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import json
import uuid

from django.contrib.auth.models import User
from django.test import Client, TestCase

from apps.companies.models import Company
from apps.conversations.huggingface_service import (generate_embedding,
                                                    generate_response,
                                                    search_similar_chunks)
from apps.conversations.models import Conversation, Message
from apps.knowledge.models import Document, DocumentChunk
from apps.knowledge.tasks import process_document_task

# =============================================================================
# UNIT TESTS - Individual Component Testing
# =============================================================================


class CompanyModelTest(TestCase):
    """Test Company model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_company_creation(self):
        """Test company can be created"""
        company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )
        self.assertEqual(company.name, "Test Corp")
        self.assertIsNotNone(company.id)
        self.assertTrue(isinstance(company.id, uuid.UUID))

    def test_api_key_auto_generation(self):
        """Test API key is automatically generated"""
        company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )
        self.assertIsNotNone(company.api_key)
        self.assertEqual(len(company.api_key), 64)  # Two UUIDs without hyphens

    def test_default_ai_personality(self):
        """Test default AI personality is set"""
        company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )
        self.assertIn("helpful", company.ai_personality.lower())


class DocumentModelTest(TestCase):
    """Test Document model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )

    def test_document_creation(self):
        """Test document can be created"""
        doc = Document.objects.create(
            company=self.company,
            title="Test Document",
            source_type=Document.SourceType.PASTE,
            raw_content="This is test content",
            status=Document.Status.PENDING,
        )
        self.assertEqual(doc.title, "Test Document")
        self.assertEqual(doc.status, Document.Status.PENDING)
        self.assertEqual(doc.chunk_count, 0)

    def test_document_status_choices(self):
        """Test document status transitions"""
        doc = Document.objects.create(
            company=self.company,
            title="Test Doc",
            source_type=Document.SourceType.TEXT,
            raw_content="Content",
        )

        # Test status transitions
        self.assertEqual(doc.status, Document.Status.PENDING)

        doc.status = Document.Status.PROCESSING
        doc.save()
        self.assertEqual(doc.status, Document.Status.PROCESSING)

        doc.status = Document.Status.COMPLETED
        doc.chunk_count = 5
        doc.save()
        self.assertEqual(doc.status, Document.Status.COMPLETED)
        self.assertEqual(doc.chunk_count, 5)


class ConversationModelTest(TestCase):
    """Test Conversation and Message models"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )

    def test_conversation_creation(self):
        """Test conversation can be created"""
        convo = Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WEB,
            customer_identifier="web_test123",
        )
        self.assertEqual(convo.channel, Conversation.Channel.WEB)
        self.assertEqual(convo.status, Conversation.Status.ACTIVE)

    def test_message_creation(self):
        """Test message can be added to conversation"""
        convo = Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WEB,
            customer_identifier="web_test123",
        )

        msg = Message.objects.create(
            conversation=convo, role=Message.Role.CUSTOMER, content="Hello, I need help"
        )

        self.assertEqual(msg.role, Message.Role.CUSTOMER)
        self.assertEqual(msg.content, "Hello, I need help")
        self.assertEqual(convo.messages.count(), 1)

    def test_conversation_message_ordering(self):
        """Test messages are ordered by creation time"""
        convo = Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WEB,
            customer_identifier="web_test123",
        )

        msg1 = Message.objects.create(
            conversation=convo, role=Message.Role.CUSTOMER, content="First message"
        )

        msg2 = Message.objects.create(
            conversation=convo, role=Message.Role.ASSISTANT, content="Second message"
        )

        messages = list(convo.messages.all())
        self.assertEqual(messages[0].id, msg1.id)
        self.assertEqual(messages[1].id, msg2.id)


class EmbeddingServiceTest(TestCase):
    """Test HuggingFace embedding service"""

    def test_generate_embedding(self):
        """Test embedding generation"""
        text = "This is a test sentence for embedding"
        embedding = generate_embedding(text)

        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 384)  # MiniLM dimension
        self.assertTrue(all(isinstance(x, float) for x in embedding))

    def test_embedding_consistency(self):
        """Test same text produces same embedding"""
        text = "Consistent test"
        emb1 = generate_embedding(text)
        emb2 = generate_embedding(text)

        # Should be very close (not exact due to floating point)
        import numpy as np

        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        self.assertGreater(similarity, 0.99)

    def test_different_texts_different_embeddings(self):
        """Test different texts produce different embeddings"""
        emb1 = generate_embedding("The weather is sunny")
        emb2 = generate_embedding("I love pizza")

        import numpy as np

        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        self.assertLess(similarity, 0.9)  # Should be quite different


class DocumentChunkTest(TestCase):
    """Test DocumentChunk model and vector search"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )
        self.doc = Document.objects.create(
            company=self.company,
            title="Test FAQ",
            source_type=Document.SourceType.PASTE,
            raw_content="Test content",
            status=Document.Status.COMPLETED,
        )

    def test_chunk_creation_with_embedding(self):
        """Test chunk can be created with embedding"""
        content = "Our return policy is 30 days"
        embedding = generate_embedding(content)

        chunk = DocumentChunk.objects.create(
            document=self.doc, content=content, chunk_index=0, embedding=embedding
        )

        self.assertEqual(chunk.content, content)
        self.assertEqual(len(chunk.embedding), 384)

    def test_search_similar_chunks(self):
        """Test semantic search for similar chunks"""
        # Create test chunks
        chunks_data = [
            "Our return policy allows returns within 30 days",
            "Shipping takes 5-7 business days",
            "We accept credit cards and PayPal",
        ]

        for i, content in enumerate(chunks_data):
            embedding = generate_embedding(content)
            DocumentChunk.objects.create(
                document=self.doc, content=content, chunk_index=i, embedding=embedding
            )

        # Search for return policy
        results = search_similar_chunks(
            self.company, "What is your refund policy?", top_k=1
        )

        self.assertEqual(len(results), 1)
        self.assertIn("return", results[0].content.lower())


# =============================================================================
# INTEGRATION TESTS - API Endpoints
# =============================================================================


class KnowledgeAPITest(TestCase):
    """Test Knowledge Base API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )
        self.auth_header = f"Bearer {self.company.api_key}"

    def test_list_documents_requires_auth(self):
        """Test listing documents requires authentication"""
        response = self.client.get("/api/knowledge/documents/")
        self.assertEqual(response.status_code, 401)

    def test_list_documents_with_auth(self):
        """Test listing documents with valid API key"""
        response = self.client.get(
            "/api/knowledge/documents/", HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_upload_document_paste(self):
        """Test uploading pasted content"""
        # Django Ninja expects title and content as query params, not JSON body
        response = self.client.post(
            "/api/knowledge/documents/upload/?title=Test%20FAQ&content=This%20is%20test%20content%20for%20the%20FAQ",
            HTTP_AUTHORIZATION=self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("message", data)

        # Verify document was created
        doc = Document.objects.get(id=data["id"])
        self.assertEqual(doc.title, "Test FAQ")
        self.assertEqual(doc.source_type, Document.SourceType.PASTE)

    def test_get_document_details(self):
        """Test retrieving document details"""
        doc = Document.objects.create(
            company=self.company,
            title="Test Doc",
            source_type=Document.SourceType.TEXT,
            raw_content="Content",
            status=Document.Status.COMPLETED,
            chunk_count=5,
        )

        response = self.client.get(
            f"/api/knowledge/documents/{doc.id}/", HTTP_AUTHORIZATION=self.auth_header
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Test Doc")
        self.assertEqual(data["chunk_count"], 5)

    def test_delete_document(self):
        """Test deleting a document"""
        doc = Document.objects.create(
            company=self.company,
            title="To Delete",
            source_type=Document.SourceType.TEXT,
            raw_content="Content",
        )

        response = self.client.delete(
            f"/api/knowledge/documents/{doc.id}/", HTTP_AUTHORIZATION=self.auth_header
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Document.objects.filter(id=doc.id).exists())


class ChatAPITest(TestCase):
    """Test Chat API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )
        self.auth_header = f"Bearer {self.company.api_key}"

        # Create test document with chunks
        self.doc = Document.objects.create(
            company=self.company,
            title="FAQ",
            source_type=Document.SourceType.PASTE,
            raw_content="Our return policy is 30 days. Shipping takes 5-7 days.",
            status=Document.Status.COMPLETED,
        )

        # Create chunks
        chunks = [
            "Our return policy allows returns within 30 days of purchase.",
            "Standard shipping takes 5-7 business days.",
        ]
        for i, content in enumerate(chunks):
            embedding = generate_embedding(content)
            DocumentChunk.objects.create(
                document=self.doc, content=content, chunk_index=i, embedding=embedding
            )

    def test_send_message_creates_conversation(self):
        """Test sending message creates new conversation"""
        response = self.client.post(
            "/api/chat/message/",
            data=json.dumps({"message": "Hello"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("conversation_id", data)
        self.assertIn("session_id", data)
        self.assertIn("response", data)

        # Verify conversation was created
        convo = Conversation.objects.get(id=data["conversation_id"])
        self.assertEqual(convo.company, self.company)
        self.assertEqual(convo.channel, Conversation.Channel.WEB)
        self.assertEqual(convo.messages.count(), 2)  # Customer + Assistant

    def test_send_message_with_session_id(self):
        """Test continuing existing conversation"""
        # Create existing conversation
        convo = Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WEB,
            customer_identifier="web_test",
        )

        response = self.client.post(
            "/api/chat/message/",
            data=json.dumps(
                {"message": "Follow up question", "session_id": str(convo.id)}
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["conversation_id"], str(convo.id))

        # Should have 2 messages now
        convo.refresh_from_db()
        self.assertEqual(convo.messages.count(), 2)

    def test_list_conversations(self):
        """Test listing conversations"""
        # Create test conversations
        Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WEB,
            customer_identifier="web_1",
        )
        Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WHATSAPP,
            customer_identifier="whatsapp:+123456",
        )

        response = self.client.get(
            "/api/chat/conversations/", HTTP_AUTHORIZATION=self.auth_header
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)

    def test_filter_conversations_by_channel(self):
        """Test filtering conversations by channel"""
        Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WEB,
            customer_identifier="web_1",
        )
        Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WHATSAPP,
            customer_identifier="whatsapp:+123456",
        )

        response = self.client.get(
            "/api/chat/conversations/?channel=web", HTTP_AUTHORIZATION=self.auth_header
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["channel"], "web")

    def test_get_conversation_messages(self):
        """Test retrieving messages from a conversation"""
        convo = Conversation.objects.create(
            company=self.company,
            channel=Conversation.Channel.WEB,
            customer_identifier="web_test",
        )

        Message.objects.create(
            conversation=convo, role=Message.Role.CUSTOMER, content="Question"
        )
        Message.objects.create(
            conversation=convo, role=Message.Role.ASSISTANT, content="Answer"
        )

        response = self.client.get(
            f"/api/chat/conversations/{convo.id}/messages/",
            HTTP_AUTHORIZATION=self.auth_header,
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["role"], "customer")
        self.assertEqual(data[1]["role"], "assistant")


class WhatsAppWebhookTest(TestCase):
    """Test WhatsApp webhook endpoint"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )

    def test_whatsapp_webhook_receives_message(self):
        """Test WhatsApp webhook accepts Twilio POST"""
        response = self.client.post(
            "/api/webhooks/whatsapp/",
            data={
                "From": "whatsapp:+1234567890",
                "To": "whatsapp:+0987654321",
                "Body": "Test message",
                "MessageSid": "SM123456789",
            },
        )

        # Should return 200 with TwiML
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn("Response", response.content.decode())


# =============================================================================
# DOCUMENT PROCESSING TESTS
# =============================================================================


class DocumentProcessingTest(TestCase):
    """Test document processing tasks"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )

    def test_process_pasted_content(self):
        """Test processing pasted text content"""
        doc = Document.objects.create(
            company=self.company,
            title="FAQ",
            source_type=Document.SourceType.PASTE,
            raw_content="Q: What is your return policy?\nA: We accept returns within 30 days.\n\nQ: How long does shipping take?\nA: Shipping takes 5-7 business days.",
            status=Document.Status.PENDING,
        )

        # Process synchronously for testing
        result = process_document_task(str(doc.id))

        # Verify document was processed
        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.COMPLETED)
        self.assertGreater(doc.chunk_count, 0)

        # Verify chunks were created
        chunks = DocumentChunk.objects.filter(document=doc)
        self.assertEqual(chunks.count(), doc.chunk_count)

        # Verify embeddings exist
        for chunk in chunks:
            self.assertEqual(len(chunk.embedding), 384)

    def test_process_empty_content_fails(self):
        """Test processing document with no content fails gracefully"""
        doc = Document.objects.create(
            company=self.company,
            title="Empty Doc",
            source_type=Document.SourceType.PASTE,
            raw_content="",
            status=Document.Status.PENDING,
        )

        result = process_document_task(str(doc.id))

        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.FAILED)
        self.assertIn("No text content", doc.error_message)


# =============================================================================
# RAG TESTS
# =============================================================================


class RAGTest(TestCase):
    """Test Retrieval-Augmented Generation"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.company = Company.objects.create(
            name="Test Corp", slug="test-corp", owner=self.user
        )

        # Create document with FAQ
        self.doc = Document.objects.create(
            company=self.company,
            title="Company FAQ",
            source_type=Document.SourceType.PASTE,
            raw_content="FAQ content",
            status=Document.Status.COMPLETED,
        )

        # Create knowledge chunks
        faq_items = [
            "Our return policy allows returns within 30 days of purchase. Items must be in original condition.",
            "Standard shipping takes 5-7 business days. Express shipping is 2-3 days.",
            "We accept Visa, MasterCard, American Express, and PayPal.",
            "Customer support is available Monday-Friday 9 AM to 5 PM EST.",
            "All products come with a 1-year warranty covering manufacturing defects.",
        ]

        for i, content in enumerate(faq_items):
            embedding = generate_embedding(content)
            DocumentChunk.objects.create(
                document=self.doc, content=content, chunk_index=i, embedding=embedding
            )

    def test_rag_retrieves_relevant_context(self):
        """Test RAG retrieves relevant chunks for question"""
        question = "What is your refund policy?"
        chunks = search_similar_chunks(self.company, question, top_k=3)

        self.assertGreater(len(chunks), 0)
        # Should retrieve the return policy chunk
        self.assertTrue(any("return" in chunk.content.lower() for chunk in chunks))

    def test_rag_responds_to_in_context_question(self):
        """Test RAG generates response for question in knowledge base"""
        from django.conf import settings

        # Skip if no Groq API key (won't test actual generation)
        if not settings.GROQ_API_KEY:
            self.skipTest("GROQ_API_KEY not configured")

        question = "What payment methods do you accept?"
        response = generate_response(self.company, question)

        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        # Response should mention payment methods
        self.assertTrue(
            any(
                word in response.lower()
                for word in ["visa", "mastercard", "paypal", "payment"]
            )
        )

    def test_rag_handles_out_of_context_question(self):
        """Test RAG handles questions outside knowledge base"""
        from django.conf import settings

        if not settings.GROQ_API_KEY:
            self.skipTest("GROQ_API_KEY not configured")

        question = "What's the weather like today?"
        response = generate_response(self.company, question)

        # Should indicate lack of information
        self.assertTrue(
            any(
                phrase in response.lower()
                for phrase in [
                    "don't have information",
                    "not available",
                    "cannot answer",
                    "no information",
                ]
            )
        )


# =============================================================================
# RUN TESTS
# =============================================================================


def run_tests():
    """Run all tests and print summary"""
    import unittest

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        CompanyModelTest,
        DocumentModelTest,
        ConversationModelTest,
        EmbeddingServiceTest,
        DocumentChunkTest,
        KnowledgeAPITest,
        ChatAPITest,
        WhatsAppWebhookTest,
        DocumentProcessingTest,
        RAGTest,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
