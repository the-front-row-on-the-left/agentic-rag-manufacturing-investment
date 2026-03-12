from __future__ import annotations

from src.agents.base import BaseAgent
from src.prompts import MARKET_ANALYSIS_SYSTEM
from src.rag.retriever import AgenticRAGRetriever
from src.schemas import MarketAnalysis
from src.state import GraphState
from src.tools.web_search import TavilySearchTool
from src.utils.references import dedupe_keep_order
from src.utils.text import model_to_pretty_json


class MarketAnalysisAgent(BaseAgent):
    def __init__(
        self,
        llm,
        settings,
        search_tool: TavilySearchTool,
        rag_retriever: AgenticRAGRetriever,
    ) -> None:
        super().__init__(llm=llm, settings=settings)
        self.search_tool = search_tool
        self.rag_retriever = rag_retriever

    def __call__(self, state: GraphState) -> dict:
        profile = state.get("startup_profile")
        if not profile:
            raise RuntimeError("startup_profile is required for market_analysis")

        search_queries = [
            f'"{profile.name}" manufacturing AI customers',
            f'"{profile.name}" ROI manufacturing AI',
            f'{profile.core_product} manufacturing market growth',
            "manufacturing AI market growth industrial AI demand",
        ]

        web_results = self.search_tool.batch_search(
            search_queries,
            topic="general",
            max_results=5,
            max_unique_results=8,
        )

        rag_queries = self.rag_retriever.plan_queries(
            task_name="market diligence",
            startup_profile=profile,
            extra_focus=(
                "market size, growth, customer pain points, labor shortage, automation demand, "
                "quality inspection economics, predictive maintenance ROI, and adoption trends"
            ),
        )
        rag_chunks = self.rag_retriever.retrieve(
            rag_queries,
            tags=["market", "manufacturing"],
            per_query_k=self.settings.top_k_market,
            max_total=self.settings.top_k_market,
        )

        user_prompt = (
            f"Startup profile:\n{model_to_pretty_json(profile)}\n\n"
            f"Web evidence:\n{self.search_tool.to_context(web_results)}\n\n"
            f"Local RAG evidence:\n{self.rag_retriever.to_context(rag_chunks)}\n\n"
            "Analyze the startup's market opportunity and commercial value."
        )

        market_analysis: MarketAnalysis = self.structured_invoke(
            MarketAnalysis,
            system_prompt=MARKET_ANALYSIS_SYSTEM,
            user_prompt=user_prompt,
        )
        market_analysis.startup_id = profile.startup_id
        market_analysis.name = profile.name
        market_analysis.target_industry = (
            market_analysis.target_industry or profile.target_industry
        )

        market_references = dedupe_keep_order(
            [
                *self.search_tool.to_references(web_results),
                *self.rag_retriever.to_references(rag_chunks),
            ]
        )
        return {
            "market_analysis": market_analysis,
            "market_references": market_references,
            "references": market_references,
        }
