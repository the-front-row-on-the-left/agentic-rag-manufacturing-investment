from __future__ import annotations

from src.agents.base import BaseAgent
from src.prompts import COMPANY_SUMMARY_SYSTEM
from src.schemas import StartupProfile
from src.state import GraphState
from src.tools.web_search import TavilySearchTool
from src.utils.references import dedupe_keep_order
from src.utils.text import model_to_pretty_json


class CompanySummaryAgent(BaseAgent):
    def __init__(self, llm, settings, search_tool: TavilySearchTool) -> None:
        super().__init__(llm=llm, settings=settings)
        self.search_tool = search_tool

    def __call__(self, state: GraphState) -> dict:
        selected = state.get("selected_startup")
        if not selected:
            raise RuntimeError("selected_startup is required for company_summary")

        queries = [
            f'"{selected.name}" official website',
            f'"{selected.name}" manufacturing AI product',
            f'"{selected.name}" customers manufacturing AI',
            f'"{selected.name}" founders manufacturing AI',
        ]

        results = self.search_tool.batch_search(
            queries,
            topic="general",
            max_results=5,
            max_unique_results=8,
        )

        user_prompt = (
            f"Selected startup:\n{model_to_pretty_json(selected)}\n\n"
            f"Web evidence:\n{self.search_tool.to_context(results)}\n\n"
            "Summarize the startup into the structured schema."
        )

        profile: StartupProfile = self.structured_invoke(
            StartupProfile,
            system_prompt=COMPANY_SUMMARY_SYSTEM,
            user_prompt=user_prompt,
        )
        profile.startup_id = selected.startup_id
        profile.name = selected.name
        profile.website = profile.website or selected.website
        profile.country = profile.country or selected.country
        profile.source_urls = dedupe_keep_order(
            [*selected.source_urls, *profile.source_urls, *[r.url for r in results if r.url]]
        )

        new_references = self.search_tool.to_references(results)

        return {
            "startup_profile": profile,
            "references": new_references,
        }
