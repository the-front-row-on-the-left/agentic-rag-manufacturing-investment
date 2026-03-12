from __future__ import annotations

from langchain_openai import ChatOpenAI

from src.config import Settings


class BaseAgent:
    def __init__(self, llm: ChatOpenAI, settings: Settings) -> None:
        self.llm = llm
        self.settings = settings

    def structured_invoke(self, schema, *, system_prompt: str, user_prompt: str):
        structured_llm = self.llm.with_structured_output(schema, method="json_schema")
        return structured_llm.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
