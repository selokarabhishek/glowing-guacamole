"""ChromaDB memory store for RAG functionality."""
import uuid
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.models.schemas import MemoryEntry


class MemoryStore:
    """ChromaDB-based memory store for storing and retrieving interactions."""

    def __init__(self, persist_dir: str, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize memory store.

        Args:
            persist_dir: Directory to persist ChromaDB data
            embedding_model: Sentence transformer model for embeddings
        """
        self.persist_dir = persist_dir
        self.embedding_model = embedding_model

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="visual_ai_interactions",
            metadata={"description": "Stored page analysis interactions"}
        )

    def store(
        self,
        url: str,
        analysis: str,
        instruction: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store an interaction in memory.

        Args:
            url: URL of the analyzed page
            analysis: AI analysis result
            instruction: User's instruction/prompt
            metadata: Additional metadata

        Returns:
            Entry ID
        """
        entry_id = str(uuid.uuid4())

        # Prepare metadata
        meta = metadata or {}
        meta.update({
            "url": url,
            "instruction": instruction,
        })

        # Store in ChromaDB
        # Use instruction + analysis as the document for embedding
        document = f"User instruction: {instruction}\n\nAnalysis: {analysis}"

        self.collection.add(
            ids=[entry_id],
            documents=[document],
            metadatas=[meta]
        )

        return entry_id

    def query(
        self,
        query_text: str,
        url_filter: Optional[str] = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """Query memory for relevant interactions.

        Args:
            query_text: Query text for semantic search
            url_filter: Optional URL to filter results
            limit: Maximum number of results

        Returns:
            List of matching memory entries
        """
        # Build where filter
        where = None
        if url_filter:
            where = {"url": url_filter}

        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query_text],
            n_results=limit,
            where=where
        )

        # Convert to MemoryEntry objects
        entries = []
        if results["ids"] and len(results["ids"]) > 0:
            ids = results["ids"][0]
            metadatas = results["metadatas"][0]
            documents = results["documents"][0]
            distances = results["distances"][0]

            for i, entry_id in enumerate(ids):
                meta = metadatas[i]
                # Extract analysis from document (it's after "Analysis: ")
                doc = documents[i]
                parts = doc.split("Analysis: ", 1)
                analysis = parts[1] if len(parts) > 1 else doc

                entries.append(MemoryEntry(
                    entry_id=entry_id,
                    url=meta.get("url", ""),
                    analysis=analysis,
                    instruction=meta.get("instruction", ""),
                    metadata={k: v for k, v in meta.items() if k not in ["url", "instruction"]},
                    distance=distances[i]
                ))

        return entries

    def delete(self, entry_id: str) -> bool:
        """Delete an entry from memory.

        Args:
            entry_id: ID of entry to delete

        Returns:
            True if deleted successfully
        """
        try:
            self.collection.delete(ids=[entry_id])
            return True
        except Exception:
            return False

    def get_count(self) -> int:
        """Get total number of entries in memory.

        Returns:
            Count of stored entries
        """
        return self.collection.count()

    def clear_all(self) -> bool:
        """Clear all entries from memory.

        Returns:
            True if cleared successfully
        """
        try:
            # Delete collection and recreate it
            self.client.delete_collection("visual_ai_interactions")
            self.collection = self.client.get_or_create_collection(
                name="visual_ai_interactions",
                metadata={"description": "Stored page analysis interactions"}
            )
            return True
        except Exception:
            return False
