"""
RAG (Retrieval-Augmented Generation) Service
Uses ChromaDB for vector storage and sentence-transformers for embeddings
SECURITY: Stores only aggregated/anonymized data, no client PII
"""

import os
import logging
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service for RAG (Retrieval-Augmented Generation)
    Stores and retrieves context for LLM queries
    """

    def __init__(self):
        self.chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        # Initialize ChromaDB client
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"ChromaDB initialized at {self.chroma_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

        # Initialize embedding model
        try:
            self.embedder = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Embedding model loaded: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="financial_data",
            metadata={"description": "Aggregated financial data for RAG"}
        )

    def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> str:
        """
        Add a document to the knowledge base

        Args:
            content: Document text content (should NOT contain PII)
            metadata: Metadata dict (entity_type, entity_id, etc.)
            doc_id: Optional custom document ID

        Returns:
            Document ID
        """
        # Generate embedding
        embedding = self.embedder.encode(content).tolist()

        # Generate ID if not provided
        if doc_id is None:
            entity_type = metadata.get('entity_type', 'unknown')
            entity_id = metadata.get('entity_id', 'unknown')
            doc_id = f"{entity_type}_{entity_id}"

        # Add to ChromaDB
        try:
            self.collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.debug(f"Added document: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            raise

    def add_documents_batch(
        self,
        contents: List[str],
        metadatas: List[Dict[str, Any]],
        doc_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add multiple documents in batch for efficiency

        Args:
            contents: List of document texts
            metadatas: List of metadata dicts
            doc_ids: Optional list of custom document IDs

        Returns:
            List of document IDs
        """
        # Generate embeddings in batch
        embeddings = self.embedder.encode(contents).tolist()

        # Generate IDs if not provided
        if doc_ids is None:
            doc_ids = [
                f"{meta.get('entity_type', 'unknown')}_{meta.get('entity_id', i)}"
                for i, meta in enumerate(metadatas)
            ]

        # Add to ChromaDB
        try:
            self.collection.add(
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=doc_ids
            )
            logger.info(f"Added {len(doc_ids)} documents in batch")
            return doc_ids
        except Exception as e:
            logger.error(f"Failed to add documents batch: {e}")
            raise

    def query(
        self,
        question: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the knowledge base for relevant documents

        Args:
            question: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {"entity_type": "policy"})

        Returns:
            Query results dict with documents, metadatas, distances
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(question).tolist()

        # Query ChromaDB
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata if filter_metadata else None
            )
            logger.debug(f"Query returned {len(results['documents'][0])} results")
            return results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """
        Update an existing document

        Args:
            doc_id: Document ID
            content: New content
            metadata: New metadata
        """
        # Generate new embedding
        embedding = self.embedder.encode(content).tolist()

        try:
            self.collection.update(
                ids=[doc_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            logger.debug(f"Updated document: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise

    def delete_document(self, doc_id: str):
        """
        Delete a document from the knowledge base

        Args:
            doc_id: Document ID to delete
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted document: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise

    def get_collection_count(self) -> int:
        """Get total number of documents in collection"""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            return 0

    def clear_collection(self):
        """Clear all documents from collection (use with caution!)"""
        try:
            self.chroma_client.delete_collection(name="financial_data")
            self.collection = self.chroma_client.create_collection(
                name="financial_data",
                metadata={"description": "Aggregated financial data for RAG"}
            )
            logger.warning("Collection cleared!")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise


# Singleton instance
_rag_service = None


def get_rag_service() -> RAGService:
    """Get singleton instance of RAG service"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
