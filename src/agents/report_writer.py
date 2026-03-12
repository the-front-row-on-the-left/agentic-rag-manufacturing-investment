from __future__ import annotations

from src.agents.base import BaseAgent
from src.prompts import REPORT_WRITER_SYSTEM
from src.state import GraphState
from src.utils.references import dedupe_keep_order
from src.utils.text import model_to_pretty_json


class ReportWriterAgent(BaseAgent):
    def __call__(self, state: GraphState) -> dict:
        evaluation_history = state.get("evaluation_history", [])
        eval_refs = []
        for item in evaluation_history:
            eval_refs.extend(item.get("references", []))
        references = dedupe_keep_order(eval_refs)

        if not evaluation_history:
            report = "# SUMMARY\n\n평가된 스타트업이 없습니다.\n\n# REFERENCE\n\n- 없음"
            return {"final_report_markdown": report}

        recommended = None
        for item in evaluation_history:
            if item["investment_decision"]["decision"] == "recommend":
                recommended = item
                break
        best = recommended or max(
            evaluation_history,
            key=lambda item: float(item["investment_decision"]["total_score"]),
        )

        prompt = (
            f"Primary startup for memo:\n{model_to_pretty_json(best)}\n\n"
            f"All evaluated startups:\n{model_to_pretty_json(evaluation_history)}\n\n"
            "Write the investment memo in Korean with these sections:\n"
            "# SUMMARY\n"
            "## 제조업 AI 시장 배경\n"
            "## 대상 스타트업 개요\n"
            "## 기술 및 현장 적용성 분석\n"
            "## 시장성 분석\n"
            "## 경쟁사 및 대체 솔루션 비교\n"
            "## 경제성 분석\n"
            "## 종합 리스크 분석\n"
            "## 투자 판단 및 제언\n"
        )

        response = self.llm.invoke(
            [
                ("system", REPORT_WRITER_SYSTEM),
                ("human", prompt),
            ]
        )

        reference_section = "# REFERENCE\n\n"
        if references:
            reference_section += "\n".join(f"- {ref}" for ref in references)
        else:
            reference_section += "- 없음"

        final_report = response.content.strip() + "\n\n" + reference_section
        return {"final_report_markdown": final_report}
