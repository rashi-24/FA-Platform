"""
Knowledge Indexer Service
Indexes aggregated financial data into ChromaDB for RAG
SECURITY: Anonymizes data before indexing, no client PII stored
"""

import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date, datetime

from models import Client, Policy, SIP, Meeting
from services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    """
    Indexes financial data into ChromaDB for RAG retrieval
    Stores only aggregated/anonymized data
    """

    def __init__(self):
        self.rag_service = get_rag_service()

    def index_all(self, db: Session):
        """
        Index all existing data into ChromaDB
        Called on startup or after bulk data import

        Args:
            db: Database session
        """
        logger.info("Starting knowledge base indexing...")

        try:
            # Index aggregated statistics
            self._index_aggregate_stats(db)

            # Index policy insights (anonymized)
            self._index_policy_insights(db)

            # Index SIP insights (anonymized)
            self._index_sip_insights(db)

            # Index meeting insights (anonymized)
            self._index_meeting_insights(db)

            logger.info(f"Indexing complete. Total documents: {self.rag_service.get_collection_count()}")

        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            raise

    def _index_aggregate_stats(self, db: Session):
        """Index overall platform statistics"""
        from sqlalchemy import func
        from models import PolicyStatus, SIPStatus

        total_clients = db.query(func.count(Client.id)).scalar()
        total_policies = db.query(func.count(Policy.id)).scalar()
        active_policies = db.query(func.count(Policy.id)).filter(
            Policy.status == PolicyStatus.ACTIVE
        ).scalar()
        total_sips = db.query(func.count(SIP.id)).scalar()
        active_sips = db.query(func.count(SIP.id)).filter(
            SIP.status == SIPStatus.ACTIVE
        ).scalar()

        content = f"""
        Platform Overview:
        - Total Clients: {total_clients}
        - Total Policies: {total_policies} ({active_policies} active)
        - Total SIPs: {total_sips} ({active_sips} active)
        """

        self.rag_service.add_document(
            content=content.strip(),
            metadata={
                "entity_type": "aggregate_stats",
                "entity_id": "platform_overview",
                "indexed_at": datetime.now().isoformat()
            },
            doc_id="stats_platform_overview"
        )

        logger.info("Indexed aggregate statistics")

    def _index_policy_insights(self, db: Session):
        """Index policy-related insights (aggregated by provider, type)"""
        from sqlalchemy import func

        # Policies by provider
        policy_by_provider = db.query(
            Policy.provider,
            func.count(Policy.id).label('count')
        ).group_by(Policy.provider).all()

        for provider, count in policy_by_provider:
            content = f"Insurance provider {provider} has {count} policies in the system."
            self.rag_service.add_document(
                content=content,
                metadata={
                    "entity_type": "policy_aggregate",
                    "provider": provider,
                    "count": count
                },
                doc_id=f"policy_provider_{provider.replace(' ', '_')}"
            )

        # Policies by type
        policy_by_type = db.query(
            Policy.policy_type,
            func.count(Policy.id).label('count')
        ).group_by(Policy.policy_type).all()

        for policy_type, count in policy_by_type:
            content = f"There are {count} {policy_type} policies in the portfolio."
            self.rag_service.add_document(
                content=content,
                metadata={
                    "entity_type": "policy_aggregate",
                    "policy_type": policy_type,
                    "count": count
                },
                doc_id=f"policy_type_{policy_type.replace(' ', '_')}"
            )

        logger.info(f"Indexed {len(policy_by_provider)} providers and {len(policy_by_type)} policy types")

    def _index_sip_insights(self, db: Session):
        """Index SIP-related insights (aggregated)"""
        from sqlalchemy import func

        # SIPs by fund
        sip_by_fund = db.query(
            SIP.fund_name,
            func.count(SIP.id).label('count')
        ).group_by(SIP.fund_name).limit(20).all()  # Top 20 funds

        for fund_name, count in sip_by_fund:
            content = f"Mutual fund {fund_name} has {count} active SIP subscriptions."
            self.rag_service.add_document(
                content=content,
                metadata={
                    "entity_type": "sip_aggregate",
                    "fund_name": fund_name,
                    "count": count
                },
                doc_id=f"sip_fund_{fund_name.replace(' ', '_')[:50]}"
            )

        logger.info(f"Indexed {len(sip_by_fund)} SIP funds")

    def _index_meeting_insights(self, db: Session):
        """Index general meeting insights (no client names)"""
        from sqlalchemy import func

        # Meeting frequency (monthly)
        meeting_count = db.query(func.count(Meeting.id)).scalar()

        content = f"Total meetings conducted: {meeting_count}. Regular client engagement is maintained."
        self.rag_service.add_document(
            content=content,
            metadata={
                "entity_type": "meeting_aggregate",
                "total_count": meeting_count
            },
            doc_id="meeting_overview"
        )

        logger.info("Indexed meeting insights")

    def reindex_entity(self, entity_type: str, entity_id: int, db: Session):
        """
        Reindex a specific entity after update
        Called after CRUD operations

        Args:
            entity_type: Type of entity (client, policy, sip)
            entity_id: Entity ID
            db: Database session
        """
        # For now, just re-index aggregates
        # In production, could index specific entity insights
        try:
            if entity_type in ["policy", "sip"]:
                self._index_aggregate_stats(db)
                logger.debug(f"Re-indexed after {entity_type} update")
        except Exception as e:
            logger.error(f"Re-indexing failed for {entity_type}:{entity_id} - {e}")


# Singleton instance
_knowledge_indexer = None


def get_knowledge_indexer() -> KnowledgeIndexer:
    """Get singleton instance of knowledge indexer"""
    global _knowledge_indexer
    if _knowledge_indexer is None:
        _knowledge_indexer = KnowledgeIndexer()
    return _knowledge_indexer
