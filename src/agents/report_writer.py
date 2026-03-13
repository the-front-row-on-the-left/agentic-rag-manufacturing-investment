from __future__ import annotations

from src.agents.base import BaseAgent
from src.prompts import REPORT_WRITER_SYSTEM
from src.scoring import LABELS
from src.state import GraphState
from src.utils.references import dedupe_keep_order, merge_rag_references, dedupe_by_url
from src.utils.text import model_to_pretty_json


class ReportWriterAgent(BaseAgent):
    def __call__(self, state: GraphState) -> dict:
        evaluation_history = state.get("evaluation_history", [])
        eval_refs = []
        for item in evaluation_history:
            eval_refs.extend(item.get("references", []))
        references = dedupe_by_url(merge_rag_references(dedupe_keep_order(eval_refs)))


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

        startup_name = best["startup_profile"].get("name", "스타트업")

        prompt = (
            f"Primary startup for memo:\n{model_to_pretty_json(best)}\n\n"
            f"All evaluated startups:\n{model_to_pretty_json(evaluation_history)}\n\n"
            "Write the investment memo in Korean with these sections:\n"
            "# SUMMARY\n"
            "## 제조업 AI 시장 배경\n"
            "## 대상 스타트업 개요\n"
            "## 핵심 근거 (Evidence)\n"
            "## 기술 및 현장 적용성 분석\n"
            "## 시장성 분석\n"
            "## 경쟁사 및 대체 솔루션 비교\n"
            "## 경제성 분석\n"
            "## 종합 리스크 분석\n"
            "## 투자 판단 및 제언\n"
            "In analysis sections, cite evidence claims and source_title/source_url from EvidenceItem when possible.\n"
            "Do NOT include a score table or reference section — these are appended automatically.\n"
        )

        response = self.llm.invoke(
            [
                ("system", REPORT_WRITER_SYSTEM),
                ("human", prompt),
            ]
        )

        body = response.content.strip()

        # 보고서 제목 삽입
        title_block = (
            f"# {startup_name} 투자 검토 보고서\n"
            f"> 제조업 AI 스타트업 투자 평가\n\n"
            "---\n\n"
        )

        # 점수표 생성
        score_table = _build_score_table(best)

        # 점수표를 "## 투자 판단 및 제언" 섹션 바로 아래에 삽입
        DECISION_HEADER = "## 투자 판단 및 제언"
        if DECISION_HEADER in body:
            body = body.replace(
                DECISION_HEADER,
                f"{DECISION_HEADER}\n\n{score_table}",
                1,
            )
        else:
            body += f"\n\n{score_table}"

        # 레퍼런스 섹션
        reference_section = "# REFERENCE\n\n"
        if references:
            reference_section += "\n".join(f"- {ref}" for ref in references)
        else:
            reference_section += "- 없음"

        final_report = title_block + body + "\n\n" + reference_section
        return {"final_report_markdown": final_report}


def _build_score_table(best: dict) -> str:
    decision = best.get("investment_decision", {})
    score_breakdown = decision.get("score_breakdown", {})
    total_score = decision.get("total_score", 0)
    decision_label = decision.get("decision", "")

    decision_map = {
        "recommend": "투자 추천",
        "conditional_review": "조건부 검토",
        "hold": "⏸ 보류",
    }

    rows = []
    for field, criterion in score_breakdown.items():
        label = LABELS.get(field, field)
        raw = criterion.get("raw_score", "-")
        weighted = criterion.get("weighted_score", "-")
        reason = criterion.get("reason", "")
        rows.append(f"| {label} | {raw}/5 | {weighted} | {reason} |")

    table = (
        f"**판정: {decision_map.get(decision_label, decision_label)} | 종합 점수: {total_score}점**\n\n"
        "| 평가 항목 | 점수 | 가중 점수 | 근거 |\n"
        "|-----------|:----:|----------:|------|\n"
    )
    table += "\n".join(rows)
    table += f"\n| **합계** | | **{total_score}** | |\n"

    return table