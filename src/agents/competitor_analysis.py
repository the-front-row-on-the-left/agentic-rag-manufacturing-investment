from __future__ import annotations

from src.agents.base import BaseAgent
from src.prompts import COMPETITOR_ANALYSIS_SYSTEM
from src.schemas import CompetitorAnalysis
from src.state import GraphState
from src.tools.web_search import TavilySearchTool
from src.utils.text import model_to_pretty_json


class CompetitorAnalysisAgent(BaseAgent):
    def __init__(self, llm, settings, search_tool: TavilySearchTool) -> None:
        super().__init__(llm=llm, settings=settings)
        self.search_tool = search_tool

    def __call__(self, state: GraphState) -> dict:
        profile = state.get("startup_profile")
        tech_analysis = state.get("tech_analysis")
        market_analysis = state.get("market_analysis")

        if not profile or not tech_analysis or not market_analysis:
            raise RuntimeError(
                "startup_profile, tech_analysis, and market_analysis are required"
            )

        queries = [
            f'"{profile.name}" competitors manufacturing',
            f'{profile.core_product} manufacturing AI competitors',
            f'{profile.core_product} predictive maintenance competitors',
            f'manufacturing AI startup competitors {profile.target_industry[0] if profile.target_industry else "industrial"}',
        ]

        results = self.search_tool.batch_search(
            queries,
            topic="general",
            max_results=5,
            max_unique_results=10,
        )

        user_prompt = (
            f"Startup profile:\n{model_to_pretty_json(profile)}\n\n"
            f"Tech analysis:\n{model_to_pretty_json(tech_analysis)}\n\n"
            f"Market analysis:\n{model_to_pretty_json(market_analysis)}\n\n"
            f"Web evidence:\n{self.search_tool.to_context(results)}\n\n"
            "Compare direct competitors, indirect competitors, and alternative solutions.\n"
            "Return `evidence` as a list of EvidenceItem objects "
            "(claim, detail, source_title, source_url, confidence)."
        )

        competitor_analysis: CompetitorAnalysis = self.structured_invoke(
            CompetitorAnalysis,
            system_prompt=COMPETITOR_ANALYSIS_SYSTEM,
            user_prompt=user_prompt,
        )

        competitor_references = self.search_tool.to_references(results)

        return {
            "competitor_analysis": competitor_analysis,
            "competitor_references": competitor_references,
            "references": competitor_references,
        }
