"""
Portfolio Review Agent
Analyzes client portfolios using RULE-BASED logic (NO LLM)
SECURITY: No client data sent to external APIs
All analysis performed locally
"""

import logging
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from datetime import date, timedelta

from models import Client, Policy, SIP, PolicyStatus, SIPStatus

logger = logging.getLogger(__name__)


class PortfolioReviewAgent:
    """
    Analyzes client portfolio and generates insights
    Uses rule-based scoring and recommendations (no external API calls)
    """

    def analyze_client(self, client_id: int, db: Session) -> Dict[str, Any]:
        """
        Analyze client portfolio and generate AI-powered insights

        Args:
            client_id: Client ID
            db: Database session

        Returns:
            Dict with portfolio analysis
        """
        try:
            # Get client data
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {"error": "Client not found"}

            policies = client.policies
            sips = client.sips

            # Calculate metrics
            total_premium = sum(p.premium_amount for p in policies if p.status == PolicyStatus.ACTIVE)
            active_sips = [s for s in sips if s.status == SIPStatus.ACTIVE]
            total_sip_amount = sum(s.amount for s in active_sips)

            # Calculate portfolio score
            portfolio_score = self._calculate_score(policies, sips)

            # Assess risk level
            risk_level = self._assess_risk_level(policies, sips)

            # Generate recommendations
            recommendations = self._generate_recommendations(client, policies, sips)

            # Identify coverage gaps
            coverage_gaps = self._identify_coverage_gaps(policies)

            return {
                "portfolio_score": portfolio_score,
                "risk_level": risk_level,
                "total_annual_premium": total_premium,
                "total_monthly_sip": total_sip_amount,
                "active_policies_count": len([p for p in policies if p.status == PolicyStatus.ACTIVE]),
                "active_sips_count": len(active_sips),
                "recommendations": recommendations,
                "coverage_gaps": coverage_gaps,
                "summary": self._generate_summary(portfolio_score, risk_level, policies, sips)
            }

        except Exception as e:
            logger.error(f"Portfolio analysis failed for client {client_id}: {e}")
            return {"error": "Analysis failed"}

    def _calculate_score(self, policies: List[Policy], sips: List[SIP]) -> int:
        """
        Calculate portfolio health score (0-100)

        Args:
            policies: List of client policies
            sips: List of client SIPs

        Returns:
            Score from 0-100
        """
        score = 50  # Base score

        active_policies = [p for p in policies if p.status == PolicyStatus.ACTIVE]
        active_sips = [s for s in sips if s.status == SIPStatus.ACTIVE]

        # Insurance coverage (30 points)
        if len(active_policies) >= 3:
            score += 30  # Well-diversified insurance
        elif len(active_policies) >= 2:
            score += 20  # Moderate coverage
        elif len(active_policies) >= 1:
            score += 10  # Minimal coverage

        # Investment discipline (20 points)
        if len(active_sips) >= 3:
            score += 20  # Excellent SIP discipline
        elif len(active_sips) >= 2:
            score += 15  # Good SIP discipline
        elif len(active_sips) >= 1:
            score += 10  # Some SIP investment

        # Portfolio maintenance (bonus points)
        all_active = all(p.status == PolicyStatus.ACTIVE for p in policies)
        if all_active and len(policies) > 0:
            score += 10  # All policies maintained

        return min(score, 100)

    def _assess_risk_level(self, policies: List[Policy], sips: List[SIP]) -> str:
        """
        Determine risk profile based on portfolio composition

        Args:
            policies: List of policies
            sips: List of SIPs

        Returns:
            Risk level: Conservative, Moderate, or Aggressive
        """
        active_sips = [s for s in sips if s.status == SIPStatus.ACTIVE]
        active_policies = [p for p in policies if p.status == PolicyStatus.ACTIVE]

        if len(active_policies) == 0:
            return "Undefined"

        # Calculate SIP to policy ratio
        sip_ratio = len(active_sips) / max(len(active_policies), 1)

        if sip_ratio > 2:
            return "Aggressive"  # Heavy investment focus
        elif sip_ratio > 1:
            return "Moderate"  # Balanced approach
        else:
            return "Conservative"  # Insurance-heavy

    def _generate_recommendations(
        self,
        client: Client,
        policies: List[Policy],
        sips: List[SIP]
    ) -> List[str]:
        """
        Generate rule-based recommendations

        Args:
            client: Client object
            policies: List of policies
            sips: List of SIPs

        Returns:
            List of recommendation strings
        """
        recommendations = []

        active_policies = [p for p in policies if p.status == PolicyStatus.ACTIVE]
        active_sips = [s for s in sips if s.status == SIPStatus.ACTIVE]

        # Insurance recommendations
        if len(active_policies) < 2:
            recommendations.append("Consider adding term life insurance for comprehensive coverage")

        has_health = any('health' in p.policy_type.lower() for p in active_policies)
        if not has_health:
            recommendations.append("Add health insurance to protect against medical expenses")

        # Check for expiring policies
        today = date.today()
        expiring_soon = [p for p in active_policies if p.renewal_date and (p.renewal_date - today).days <= 30]
        if expiring_soon:
            recommendations.append(f"{len(expiring_soon)} {'policy is' if len(expiring_soon) == 1 else 'policies are'} expiring soon - review renewal terms")

        # Investment recommendations
        if len(active_sips) == 0:
            recommendations.append("Start a SIP to build long-term wealth systematically")
        elif len(active_sips) < 2:
            recommendations.append("Diversify SIP investments across different fund categories")

        # Balance recommendation
        total_premium = sum(p.premium_amount for p in active_policies)
        total_sip = sum(s.amount for s in active_sips)

        if total_premium > 0 and total_sip == 0:
            recommendations.append("Balance protection with wealth creation through SIP investments")
        elif total_sip > 0 and total_premium == 0:
            recommendations.append("Add insurance protection to complement your investment portfolio")

        # If portfolio is good
        if len(recommendations) == 0:
            recommendations.append("Your portfolio is well-balanced. Continue maintaining your SIPs and policies.")

        return recommendations[:5]  # Return top 5

    def _identify_coverage_gaps(self, policies: List[Policy]) -> List[str]:
        """
        Identify insurance coverage gaps

        Args:
            policies: List of policies

        Returns:
            List of coverage gaps
        """
        gaps = []

        active_policies = [p for p in policies if p.status == PolicyStatus.ACTIVE]
        policy_types = [p.policy_type.lower() for p in active_policies]

        # Check for common coverage types
        essential_types = {
            'term': 'Term life insurance',
            'health': 'Health insurance',
            'accident': 'Accidental death insurance'
        }

        for key, name in essential_types.items():
            if not any(key in ptype for ptype in policy_types):
                gaps.append(f"Missing {name}")

        if len(gaps) == 0:
            gaps.append("No major coverage gaps identified")

        return gaps

    def _generate_summary(
        self,
        score: int,
        risk_level: str,
        policies: List[Policy],
        sips: List[SIP]
    ) -> str:
        """
        Generate portfolio summary text

        Args:
            score: Portfolio score
            risk_level: Risk level
            policies: List of policies
            sips: List of SIPs

        Returns:
            Summary string
        """
        active_policies = len([p for p in policies if p.status == PolicyStatus.ACTIVE])
        active_sips = len([s for s in sips if s.status == SIPStatus.ACTIVE])

        if score >= 80:
            health = "excellent"
        elif score >= 60:
            health = "good"
        elif score >= 40:
            health = "moderate"
        else:
            health = "needs improvement"

        return f"""Portfolio health is {health} with a score of {score}/100.
        Risk profile: {risk_level}.
        {active_policies} active {'policy' if active_policies == 1 else 'policies'}
        and {active_sips} active SIP{'s' if active_sips != 1 else ''}."""


# Singleton instance
_portfolio_agent = None


def get_portfolio_agent() -> PortfolioReviewAgent:
    """Get singleton instance of portfolio review agent"""
    global _portfolio_agent
    if _portfolio_agent is None:
        _portfolio_agent = PortfolioReviewAgent()
    return _portfolio_agent
