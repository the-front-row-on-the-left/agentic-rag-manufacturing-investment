from __future__ import annotations

from urllib.parse import urlparse

from src.agents.base import BaseAgent
from src.prompts import COMPANY_SUMMARY_SYSTEM
from src.schemas import StartupProfile
from src.state import GraphState
from src.tools.web_search import TavilySearchTool
from src.utils.references import dedupe_keep_order
from src.utils.text import model_to_pretty_json


class CompanySummaryAgent(BaseAgent):
    EXCLUDED_DOMAINS = {
        "shop.baltimoreravens.com",
        "ravenlunatics.com",
        "theraveneffect.com",
    }

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
        profile = self._normalize_profile(profile, selected, results)

        new_references = self.search_tool.to_references(results)

        return {
            "startup_profile": profile,
            "references": new_references,
        }

    def _normalize_profile(
        profile: StartupProfile,
        selected,
        results,
    ) -> StartupProfile:
        profile.startup_id = selected.startup_id
        profile.name = selected.name
        profile.website = profile.website or selected.website
        profile.country = profile.country or selected.country
        official_domain = self._domain_from_url(profile.website or selected.website or "")
        profile.source_urls = dedupe_keep_order(
            self._filter_profile_urls(
                [*selected.source_urls, *profile.source_urls, *[r.url for r in results if r.url]],
                official_domain=official_domain,
            )
        )
        return profile

    def _filter_profile_urls(
        self,
        urls: list[str],
        *,
        official_domain: str,
    ) -> list[str]:
        filtered: list[str] = []
        for url in urls:
            domain = self._domain_from_url(url)
            if not domain or domain in self.EXCLUDED_DOMAINS:
                continue
            if official_domain and (domain == official_domain or domain.endswith(f".{official_domain}")):
                filtered.append(url)
                continue
            filtered.append(url)
        return filtered

    @staticmethod
    def _domain_from_url(url: str) -> str:
        return urlparse(url).netloc.lower().strip()
