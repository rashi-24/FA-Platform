"""
Capital Companion Agent
Provides AI-powered general financial insights using RAG + LLM
SECURITY: Does NOT send client PII to external APIs
Uses aggregated/anonymized data only
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from typing import Dict, List, Any
from sqlalchemy import func

from models import Client, Policy, SIP, Meeting, PolicyStatus, SIPStatus
from services.llm_service import get_llm_service
from services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


class CapitalCompanionAgent:
    """
    Natural language query agent for general financial insights
    Provides daily insights and answers financial questions
    """

    def __init__(self):
        self.llm_service = get_llm_service()
        self.rag_service = get_rag_service()

    def query(self, question: str, db: Session) -> Dict[str, Any]:
        """
        Answer a general financial question using RAG + LLM

        Args:
            question: User's question
            db: Database session

        Returns:
            Dict with answer and sources
        """
        # Sanitize query to prevent PII requests
        is_safe, result = self.llm_service.sanitize_query(question)
        if not is_safe:
            return {
                "answer": result,
                "sources": [],
                "is_blocked": True
            }

        try:
            # Retrieve relevant context from RAG
            rag_results = self.rag_service.query(question, n_results=5)

            if rag_results and rag_results['documents'] and len(rag_results['documents'][0]) > 0:
                # Build context from retrieved documents
                context = "\n\n".join(rag_results['documents'][0])
                metadatas = rag_results['metadatas'][0] if rag_results['metadatas'] else []
            else:
                # No relevant documents found, use general stats
                context = self._get_general_stats(db)
                metadatas = []

            # Query LLM with context
            answer = self.llm_service.query(
                prompt=question,
                context=context,
                max_tokens=300,
                temperature=0.7
            )

            return {
                "answer": answer,
                "sources": metadatas,
                "is_blocked": False
            }

        except Exception as e:
            logger.error(f"Capital Companion query failed: {e}")
            return {
                "answer": "I'm sorry, I encountered an error processing your question. Please try again.",
                "sources": [],
                "is_blocked": False
            }

    def get_daily_insights(self, db: Session) -> List[Dict[str, Any]]:
        """
        Generate daily insights for the dashboard
        Returns aggregated analytics, no client-specific info

        Args:
            db: Database session

        Returns:
            List of insight dicts
        """
        insights = []
        today = date.today()

        try:
            # Insight 1: Policies expiring soon
            upcoming_renewals = db.query(Policy).filter(
                Policy.renewal_date.between(today, today + timedelta(days=30)),
                Policy.status == PolicyStatus.ACTIVE
            ).count()

            if upcoming_renewals > 0:
                insights.append({
                    "type": "policy_renewal",
                    "priority": "high" if upcoming_renewals > 5 else "medium",
                    "icon": "⚠️",
                    "title": "Upcoming Policy Renewals",
                    "message": f"{upcoming_renewals} {'policies' if upcoming_renewals > 1 else 'policy'} expiring in the next 30 days",
                    "count": upcoming_renewals
                })

            # Insight 2: SIPs due this month
            current_month = today.month
            active_sips = db.query(SIP).filter(
                SIP.status == SIPStatus.ACTIVE
            ).count()

            if active_sips > 0:
                insights.append({
                    "type": "sip_active",
                    "priority": "low",
                    "icon": "💰",
                    "title": "Active SIP Investments",
                    "message": f"{active_sips} SIPs actively building wealth",
                    "count": active_sips
                })

            # Insight 3: Client engagement
            recent_meetings = db.query(Meeting).filter(
                Meeting.meeting_date >= datetime.now() - timedelta(days=30)
            ).count()

            total_clients = db.query(Client).count()
            engagement_rate = (recent_meetings / total_clients * 100) if total_clients > 0 else 0

            if engagement_rate > 0:
                insights.append({
                    "type": "engagement",
                    "priority": "low",
                    "icon": "📊",
                    "title": "Client Engagement",
                    "message": f"{engagement_rate:.0f}% clients engaged this month ({recent_meetings} meetings)",
                    "count": recent_meetings
                })

            # Insight 4: Portfolio diversity
            total_policies = db.query(Policy).count()
            policy_types = db.query(Policy.policy_type).distinct().count()

            if total_policies > 0:
                insights.append({
                    "type": "portfolio_diversity",
                    "priority": "low",
                    "icon": "🎯",
                    "title": "Portfolio Diversity",
                    "message": f"{policy_types} different policy types across {total_policies} policies",
                    "count": policy_types
                })

            # Insight 5: AI tip of the day
            insights.append(self._get_daily_tip())

            return insights[:5]  # Return top 5 insights

        except Exception as e:
            logger.error(f"Failed to generate daily insights: {e}")
            return [{
                "type": "error",
                "priority": "low",
                "icon": "ℹ️",
                "title": "Insights Unavailable",
                "message": "Unable to generate insights at this time",
                "count": 0
            }]

    def _get_general_stats(self, db: Session) -> str:
        """
        Get general platform statistics as context

        Args:
            db: Database session

        Returns:
            Formatted stats string
        """
        total_clients = db.query(func.count(Client.id)).scalar()
        total_policies = db.query(func.count(Policy.id)).scalar()
        active_sips = db.query(func.count(SIP.id)).filter(SIP.status == SIPStatus.ACTIVE).scalar()

        return f"""
        Platform Statistics:
        - Total number of clients: {total_clients}
        - Total insurance policies: {total_policies}
        - Active SIP investments: {active_sips}
        """

    def _get_daily_tip(self) -> Dict[str, Any]:
        """
        Get a daily financial tip

        Returns:
            Insight dict with tip
        """
        tips = [
            "Regular SIP investments benefit from rupee cost averaging",
            "Term insurance provides maximum coverage at minimum cost",
            "Diversification across asset classes reduces portfolio risk",
            "Review insurance coverage annually to match life stage needs",
            "Emergency fund should cover 6-12 months of expenses",
            "Start retirement planning early to benefit from compounding",
            "Health insurance is as important as life insurance",
            "Avoid surrendering policies prematurely to maximize returns",
        ]

        import random
        tip = random.choice(tips)

        return {
            "type": "daily_tip",
            "priority": "low",
            "icon": "💡",
            "title": "Financial Tip of the Day",
            "message": tip,
            "count": 0
        }


# Singleton instance
_capital_companion_agent = None


def get_capital_companion_agent() -> CapitalCompanionAgent:
    """Get singleton instance of Capital Companion agent"""
    global _capital_companion_agent
    if _capital_companion_agent is None:
        _capital_companion_agent = CapitalCompanionAgent()
    return _capital_companion_agent
