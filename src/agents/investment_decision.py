from __future__ import annotations

from src.agents.base import BaseAgent
from src.prompts import INVESTMENT_DECISION_SYSTEM
from src.scoring import finalize_investment_decision
from src.schemas import InvestmentDecisionDraft
from src.state import GraphState
from src.utils.text import model_to_pretty_json


class InvestmentDecisionAgent(BaseAgent):
    def __call__(self, state: GraphState) -> dict:
        profile = state.get("startup_profile")
        tech_analysis = state.get("tech_analysis")
        market_analysis = state.get("market_analysis")
        competitor_analysis = state.get("competitor_analysis")

        if not all([profile, tech_analysis, market_analysis, competitor_analysis]):
            raise RuntimeError(
                "startup_profile, tech_analysis, market_analysis, and competitor_analysis are required"
            )

        user_prompt = (
            f"Startup profile:\n{model_to_pretty_json(profile)}\n\n"
            f"Tech analysis:\n{model_to_pretty_json(tech_analysis)}\n\n"
            f"Market analysis:\n{model_to_pretty_json(market_analysis)}\n\n"
            f"Competitor analysis:\n{model_to_pretty_json(competitor_analysis)}\n\n"
            "Score the startup using the manufacturing VC rubric."
        )

        draft: InvestmentDecisionDraft = self.structured_invoke(
            InvestmentDecisionDraft,
            system_prompt=INVESTMENT_DECISION_SYSTEM,
            user_prompt=user_prompt,
        )
        final_decision = finalize_investment_decision(draft)

        evaluation_record = {
            "startup_profile": profile.model_dump(),
            "tech_analysis": tech_analysis.model_dump(),
            "market_analysis": market_analysis.model_dump(),
            "competitor_analysis": competitor_analysis.model_dump(),
            "investment_decision": final_decision.model_dump(),
            "references": sorted(set(
                [
                    *state.get("tech_references", []),
                    *state.get("market_references", []),
                    *state.get("competitor_references", []),
                ]
            )),
        }

        updates = {
            "investment_decision": final_decision,
            "evaluation_history": [evaluation_record],
        }

        if final_decision.decision == "recommend":
            updates["recommended_startups"] = [evaluation_record]
        else:
            updates["held_startups"] = [evaluation_record]

        return updates
