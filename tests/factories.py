"""
Test factories for creating test data.

Uses factory_boy for consistent test data generation.
"""

import factory
from django.contrib.auth.models import User
from factory import fuzzy

from apps.companies.models import Company
from apps.conversations.models import Conversation, Message
from apps.knowledge.models import Document, DocumentChunk


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "testpass123")


class CompanyFactory(factory.django.DjangoModelFactory):
    """Factory for creating test companies."""

    class Meta:
        model = Company

    name = factory.Faker("company")
    slug = factory.Sequence(lambda n: f"company-{n}")
    owner = factory.SubFactory(UserFactory)
    ai_personality = "You are a helpful customer support agent."


class DocumentFactory(factory.django.DjangoModelFactory):
    """Factory for creating test documents."""

    class Meta:
        model = Document

    company = factory.SubFactory(CompanyFactory)
    title = factory.Faker("sentence", nb_words=4)
    source_type = Document.SourceType.PASTE
    raw_content = factory.Faker("paragraph", nb_sentences=5)
    status = Document.Status.COMPLETED
    chunk_count = 0


class DocumentChunkFactory(factory.django.DjangoModelFactory):
    """Factory for creating test document chunks."""

    class Meta:
        model = DocumentChunk

    document = factory.SubFactory(DocumentFactory)
    content = factory.Faker("paragraph")
    chunk_index = factory.Sequence(lambda n: n)
    embedding = factory.LazyFunction(lambda: [0.1] * 384)
    metadata = factory.LazyFunction(dict)


class ConversationFactory(factory.django.DjangoModelFactory):
    """Factory for creating test conversations."""

    class Meta:
        model = Conversation

    company = factory.SubFactory(CompanyFactory)
    channel = fuzzy.FuzzyChoice(
        [
            Conversation.Channel.WEB,
            Conversation.Channel.WHATSAPP,
            Conversation.Channel.EMAIL,
        ]
    )
    customer_identifier = factory.Sequence(lambda n: f"customer-{n}")
    status = Conversation.Status.ACTIVE


class MessageFactory(factory.django.DjangoModelFactory):
    """Factory for creating test messages."""

    class Meta:
        model = Message

    conversation = factory.SubFactory(ConversationFactory)
    role = fuzzy.FuzzyChoice(
        [
            Message.Role.CUSTOMER,
            Message.Role.ASSISTANT,
        ]
    )
    content = factory.Faker("sentence")
    metadata = factory.LazyFunction(dict)
