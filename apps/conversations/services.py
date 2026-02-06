"""
Conversation services for AI response generation.

Provides the main generate_response function that orchestrates:
- Groq LLM for chat responses
- HuggingFace for embeddings
- Fallback to OpenAI if configured
"""

import logging
from typing import Optional

from django.conf import settings
from apps.companies.models import Company
from apps.conversations.models import Conversation

logger = logging.getLogger(__name__)


def generate_response(
    company: Company, 
    question: str, 
    conversation: Optional[Conversation] = None
) -> str:
    """
    Core RAG function - uses Groq for chat, local model for embeddings.
    
    Args:
        company: Company context for the query
        question: Customer's question
        conversation: Optional conversation for context
        
    Returns:
        AI-generated response string
    """
    
    # Use Groq if configured
    if settings.GROQ_API_KEY:
        from .huggingface_service import generate_response as groq_generate
        return groq_generate(company, question, conversation)
    
    # Fall back to OpenAI if configured
    if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        return _generate_response_openai(company, question, conversation)
    
    logger.error("No AI service configured (GROQ or OpenAI)")
    return "I'm sorry, but the AI service is not currently available. Please try again later or contact support."


def _generate_response_openai(
    company: Company, 
    question: str, 
    conversation: Optional[Conversation] = None
) -> str:
    """
    OpenAI implementation (fallback).
    
    Args:
        company: Company context
        question: Customer question
        conversation: Optional conversation context
        
    Returns:
        AI-generated response
    """
    try:
        from openai import OpenAI
        from pgvector.django import L2Distance
        from apps.knowledge.models import DocumentChunk
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Generate embedding
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=question
        )
        question_embedding = embedding_response.data[0].embedding
        
        # Search for relevant chunks
        relevant_chunks = DocumentChunk.objects.filter(
            document__company=company
        ).order_by(
            L2Distance('embedding', question_embedding)
        )[:5]
        
        # Build context
        if not relevant_chunks:
            context = "No relevant information found in the knowledge base."
        else:
            context = "\n\n---\n\n".join([chunk.content for chunk in relevant_chunks])
        
        # Build system prompt
        system_prompt = f"""You are a customer support agent for {company.name}.
{company.ai_personality}

CONTEXT FROM KNOWLEDGE BASE:
{context}
"""
        
        # Get response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(
            f"OpenAI generation failed for company {company.id}",
            exc_info=True,
            extra={"company_id": str(company.id), "question": question[:50]}
        )
        return "I'm experiencing technical difficulties. Please try again in a moment."