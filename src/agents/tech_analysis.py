from __future__ import annotations

from src.agents.base import BaseAgent
from src.prompts import TECH_ANALYSIS_SYSTEM
from src.rag.retriever import AgenticRAGRetriever
from src.schemas import StartupProfile, TechAnalysis
from src.state import GraphState
from src.tools.web_search import TavilySearchTool
from src.utils.references import dedupe_keep_order
from src.utils.text import model_to_pretty_json


class TechAnalysisAgent(BaseAgent):
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
            raise RuntimeError("startup_profile is required for tech_analysis")

        queries = [
            f'"{profile.name}" "{profile.core_product}" deployment',
            f'"{profile.name}" AI model manufacturing integration',
            f'"{profile.name}" edge on-prem industrial AI',
        ]
        web_results = self.search_tool.batch_search(
            queries,
            topic="general",
            max_results=5,
            max_unique_results=6,
        )

        rag_queries = self.rag_retriever.plan_queries(
            task_name="technical diligence",
            startup_profile=profile,
            extra_focus=(
                "manufacturing deployability, required data, edge/on-prem constraints, "
                "MES/ERP/integration, adoption barriers, and technical limitations"
            ),
        )
        rag_chunks = self.rag_retriever.retrieve(
            rag_queries,
            tags=["tech", "manufacturing"],
            per_query_k=self.settings.top_k_tech,
            max_total=self.settings.top_k_tech,
        )

        user_prompt = (
            f"Startup profile:\n{model_to_pretty_json(profile)}\n\n"
            f"Web evidence:\n{self.search_tool.to_context(web_results)}\n\n"
            f"Local RAG evidence:\n{self.rag_retriever.to_context(rag_chunks)}\n\n"
            "Analyze the startup's technology and real-world deployability in manufacturing."
        )

        tech_analysis: TechAnalysis = self.structured_invoke(
            TechAnalysis,
            system_prompt=TECH_ANALYSIS_SYSTEM,
            user_prompt=user_prompt,
        )
        tech_analysis.startup_id = profile.startup_id
        tech_analysis.name = profile.name

        tech_references = dedupe_keep_order(
            [
                *self.search_tool.to_references(web_results),
                *self.rag_retriever.to_references(rag_chunks),
            ]
        )
        return {
            "tech_analysis": tech_analysis,
            "tech_references": tech_references,
            "references": tech_references,
        }
