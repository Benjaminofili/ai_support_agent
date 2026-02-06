import logging
from typing import List, Optional

import numpy as np
from django.conf import settings
from sentence_transformers import SentenceTransformer

from apps.companies.models import Company
from apps.knowledge.models import DocumentChunk

logger = logging.getLogger(__name__)

# Constants
EMBEDDING_DIMENSIONS = getattr(settings, "EMBEDDING_DIMENSIONS", 384)
MAX_CONTEXT_CHUNKS = getattr(settings, "MAX_CONTEXT_CHUNKS", 5)

# Embedding model singleton
_embedding_model = None
_model_loading = False


def get_embedding_model() -> SentenceTransformer:
    """
    Load sentence-transformers model for embeddings (cached singleton).

    Returns:
        SentenceTransformer: The loaded embedding model
    """
    global _embedding_model, _model_loading

    if _embedding_model is None and not _model_loading:
        _model_loading = True
        logger.info("Loading embedding model...")
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
        _model_loading = False

    return _embedding_model


def preload_model() -> Optional[SentenceTransformer]:
    """
    Pre-load the embedding model.
    Call this on Django/Celery startup to avoid cold start delays.

    Returns:
        SentenceTransformer: The loaded model, or None if failed
    """
    try:
        return get_embedding_model()
    except Exception as e:
        logger.error(f"Failed to preload embedding model: {e}", exc_info=True)
        return None


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding using local sentence-transformers model.

    Args:
        text: The text to generate embedding for

    Returns:
        List[float]: The embedding vector

    Raises:
        ValueError: If embedding generation fails
    """
    try:
        model = get_embedding_model()
        embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}", exc_info=True)
        raise ValueError(f"Failed to generate embedding: {e}")


def search_similar_chunks(
    company: Company, question: str, top_k: int = MAX_CONTEXT_CHUNKS
) -> List[DocumentChunk]:
    """
    Search for similar document chunks using cosine similarity.

    Args:
        company: The company whose documents to search
        question: The question to find relevant chunks for
        top_k: Maximum number of chunks to return

    Returns:
        List[DocumentChunk]: Most relevant chunks, sorted by similarity
    """
    try:
        question_embedding = generate_embedding(question)

        chunks = DocumentChunk.objects.filter(
            document__company=company, document__status="completed"
        ).select_related("document")

        if not chunks.exists():
            logger.warning(f"No document chunks found for company {company.id}")
            return []

        results = []
        question_vec = np.array(question_embedding)

        for chunk in chunks:
            chunk_vec = np.array(chunk.embedding)

            # Calculate cosine similarity
            norm_product = np.linalg.norm(question_vec) * np.linalg.norm(chunk_vec)
            if norm_product == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(question_vec, chunk_vec) / norm_product)

            results.append((chunk, similarity))

        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)

        logger.debug(f"Found {len(results)} chunks, returning top {top_k}")
        return [chunk for chunk, score in results[:top_k]]

    except Exception as e:
        logger.error(f"Chunk search failed: {e}", exc_info=True)
        return []


def generate_chat_response(prompt: str) -> str:
    """
    Generate response using Groq API.

    Args:
        prompt: The complete prompt to send to the LLM

    Returns:
        str: The generated response
    """
    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY not configured")
        return (
            "I'm sorry, but the AI service is not configured. Please contact support."
        )

    try:
        from groq import Groq

        client = Groq(api_key=settings.GROQ_API_KEY)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.MAX_TOKENS,
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Groq API error: {e}", exc_info=True)
        return "I'm experiencing technical difficulties. Please try again later."


def generate_response(company: Company, question: str, conversation=None) -> str:
    """
    Main RAG function - generates AI response using relevant context.

    1. Searches for relevant document chunks
    2. Builds context from chunks
    3. Generates response with Groq LLM

    Args:
        company: The company context for the query
        question: The user's question
        conversation: Optional conversation for multi-turn context

    Returns:
        str: The AI-generated response
    """
    logger.info(f"Generating response for company {company.id}: {question[:50]}...")

    # Search for relevant chunks
    relevant_chunks = search_similar_chunks(company, question, top_k=MAX_CONTEXT_CHUNKS)

    # Build context
    if not relevant_chunks:
        context = "No relevant information found in the knowledge base."
        logger.warning(f"No relevant chunks found for: {question[:50]}")
    else:
        context = "\n\n---\n\n".join([chunk.content for chunk in relevant_chunks])
        logger.debug(f"Using {len(relevant_chunks)} chunks for context")

    # Build prompt
    prompt = f"""You are a customer support agent for {company.name}.
{company.ai_personality}

IMPORTANT RULES:
1. ONLY answer based on the provided context below.
2. If the context doesn't contain the answer, say "I don't have information about that. Would you like me to connect you with a human agent?"
3. Be concise and helpful.
4. Never make up information.

CONTEXT FROM KNOWLEDGE BASE:
{context}

CUSTOMER QUESTION: {question}

YOUR RESPONSE:"""

    response = generate_chat_response(prompt)
    logger.info(f"Generated response: {response[:50]}...")

    return response
