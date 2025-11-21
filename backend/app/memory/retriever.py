"""Memory retriever for RAG-enhanced prompts."""
from typing import List, Optional
from app.memory.store import MemoryStore
from app.models.schemas import MemoryEntry


class MemoryRetriever:
    """Retrieves relevant context from memory to enhance prompts."""

    def __init__(self, memory_store: MemoryStore):
        """Initialize memory retriever.

        Args:
            memory_store: Memory store instance
        """
        self.store = memory_store

    def get_context(
        self,
        query: str,
        url: Optional[str] = None,
        limit: int = 3
    ) -> List[MemoryEntry]:
        """Get relevant context from memory.

        Args:
            query: Query text (user's prompt)
            url: Optional URL to prioritize
            limit: Maximum number of context entries

        Returns:
            List of relevant memory entries
        """
        return self.store.query(query, url_filter=url, limit=limit)

    def build_enhanced_prompt(
        self,
        user_prompt: str,
        url: Optional[str] = None,
        use_memory: bool = True
    ) -> tuple[str, bool]:
        """Build enhanced prompt with memory context.

        Args:
            user_prompt: User's original prompt
            url: URL of current page
            use_memory: Whether to use memory context

        Returns:
            Tuple of (enhanced_prompt, memory_used)
        """
        if not use_memory:
            return user_prompt, False

        # Get relevant context
        context_entries = self.get_context(user_prompt, url=url, limit=3)

        if not context_entries:
            return user_prompt, False

        # Build context section
        context_parts = []
        context_parts.append("RELEVANT PAST INTERACTIONS:")
        context_parts.append("")

        for i, entry in enumerate(context_entries, 1):
            context_parts.append(f"--- Past Interaction {i} ---")
            context_parts.append(f"URL: {entry.url}")
            context_parts.append(f"Previous instruction: {entry.instruction}")
            context_parts.append(f"Previous analysis: {entry.analysis[:300]}...")  # Truncate for context
            context_parts.append("")

        context_parts.append("---")
        context_parts.append("")
        context_parts.append("Using the context above when relevant, please:")

        # Combine context with user prompt
        enhanced_prompt = "\n".join(context_parts) + "\n" + user_prompt

        return enhanced_prompt, True
