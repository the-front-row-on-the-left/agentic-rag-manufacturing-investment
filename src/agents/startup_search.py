from __future__ import annotations

from urllib.parse import urlparse

from src.agents.base import BaseAgent
from src.prompts import STARTUP_SEARCH_SYSTEM
from src.schemas import StartupCandidate, StartupSearchResponse
from src.state import GraphState
from src.tools.web_search import TavilySearchTool


class StartupSearchAgent(BaseAgent):
    MIN_RELEVANCE_TERMS = {
        "manufacturing",
        "industrial",
        "factory",
        "production",
        "automation",
        "robot",
        "robotic",
        "quality",
        "inspection",
        "predictive",
        "maintenance",
        "oee",
        "supply chain",
        "plant",
    }
    EXCLUDED_DOMAINS = {
        "shop.baltimoreravens.com",
        "ravenlunatics.com",
        "theraveneffect.com",
    }

    def __init__(self, llm, settings, search_tool: TavilySearchTool) -> None:
        super().__init__(llm=llm, settings=settings)
        self.search_tool = search_tool

    def __call__(self, state: GraphState) -> dict:
        candidates = state.get("candidate_startups", [])
        current_index = state.get("current_index", -1)

        if candidates and (current_index + 1) < len(candidates):
            next_index = current_index + 1
            return self._select_existing_candidate(state, next_index)

        if candidates:
            return self._mark_search_complete()

        queries = [
            f'{state["input_keyword"]} startup',
            "manufacturing AI startup predictive maintenance startup",
            "manufacturing AI computer vision quality inspection startup",
            "industrial AI startup smart factory startup",
        ]

        search_results = self.search_tool.batch_search(
            queries,
            topic="general",
            max_results=6,
            max_unique_results=max(10, state.get("max_candidates", 5) * 2),
        )

        user_prompt = (
            f"User keyword: {state['input_keyword']}\n"
            f"Domain: {state['domain']}\n"
            f"Max candidates: {state['max_candidates']}\n\n"
            f"Web evidence:\n{self.search_tool.to_context(search_results)}\n\n"
            "Return a de-duplicated startup candidate list."
        )

        response: StartupSearchResponse = self.structured_invoke(
            StartupSearchResponse,
            system_prompt=STARTUP_SEARCH_SYSTEM,
            user_prompt=user_prompt,
        )

        deduped: list[StartupCandidate] = []
        seen_names: set[str] = set()
        for idx, candidate in enumerate(response.candidates, start=1):
            normalized_name = candidate.name.strip().lower()
            if not normalized_name or normalized_name in seen_names:
                continue
            if not self._is_candidate_eligible(candidate):
                continue
            seen_names.add(normalized_name)
            candidate.startup_id = f"s{len(deduped) + 1}"
            candidate.domain = state["domain"]
            deduped.append(candidate)
            if len(deduped) >= state["max_candidates"]:
                break

        new_references = self.search_tool.to_references(search_results)
        if not deduped:
            return {
                "selected_startup": None,
                "search_done": True,
                "references": new_references,
                "startup_profile": None,
                "tech_analysis": None,
                "market_analysis": None,
                "competitor_analysis": None,
                "investment_decision": None,
                "tech_references": [],
                "market_references": [],
                "competitor_references": [],
            }

        return {
            "candidate_startups": deduped,
            "current_index": 0,
            "selected_startup": deduped[0],
            "search_done": False,
            "references": new_references,
            **self._reset_current_candidate_state(),
        }

    def _select_existing_candidate(self, state: GraphState, index: int) -> dict:
        candidate = state["candidate_startups"][index]
        return {
            "current_index": index,
            "selected_startup": candidate,
            "search_done": False,
            **self._reset_current_candidate_state(),
        }

    @staticmethod
    def _reset_current_candidate_state() -> dict:
        return {
            "startup_profile": None,
            "tech_analysis": None,
            "market_analysis": None,
            "competitor_analysis": None,
            "investment_decision": None,
            "tech_references": [],
            "market_references": [],
            "competitor_references": [],
        }

    def _mark_search_complete(self) -> dict:
        return {
            "selected_startup": None,
            "search_done": True,
            **self._reset_current_candidate_state(),
        }

    def _is_candidate_eligible(self, candidate: StartupCandidate) -> bool:
        description = (candidate.short_description or "").strip().lower()
        if len(description) < 25:
            return False
        if not any(term in description for term in self.MIN_RELEVANCE_TERMS):
            return False

        source_urls = [url for url in candidate.source_urls if url]
        if not source_urls and not candidate.website:
            return False

        allowed_urls = [
            url
            for url in source_urls
            if self._domain_from_url(url) not in self.EXCLUDED_DOMAINS
        ]
        if source_urls and not allowed_urls:
            return False

        candidate.source_urls = allowed_urls
        return True

    @staticmethod
    def _domain_from_url(url: str) -> str:
        return urlparse(url).netloc.lower().strip()
