from __future__ import annotations

import re

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

        recommended_candidates = [
            item
            for item in evaluation_history
            if item.get("investment_decision", {}).get("decision") == "recommend"
        ]
        conditional_candidates = [
            item
            for item in evaluation_history
            if item.get("investment_decision", {}).get("decision")
            == "conditional_review"
        ]
        candidate_pool = (
            recommended_candidates or conditional_candidates or evaluation_history
        )
        best = max(
            candidate_pool,
            key=lambda item: float(
                item.get("investment_decision", {}).get("total_score", 0)
            ),
        )
        is_hold_report = not recommended_candidates

        startup_name = best["startup_profile"].get("name", "스타트업")

        prompt = (
            f"Primary startup for memo:\n{model_to_pretty_json(best)}\n\n"
            f"All evaluated startups:\n{model_to_pretty_json(evaluation_history)}\n\n"
            "Write the investment memo in Korean with these sections:\n"
            "# SUMMARY\n"
            "## 제조업 AI 시장 배경\n"
            "## 대상 스타트업 개요\n"
            "## 핵심 근거\n"
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

        # 점수표를 "## 투자 판단 및 제언" 섹션 바로 아래에 삽입
        DECISION_HEADER = "## 투자 판단 및 제언"

        if is_hold_report:
            hold_summary = _build_hold_summary(best, evaluation_history)
            if DECISION_HEADER in body:
                body = body.replace(
                    DECISION_HEADER,
                    f"{hold_summary}\n\n{DECISION_HEADER}",
                    1,
                )
            else:
                body += "\n\n" + hold_summary

        # 보고서 제목 삽입
        report_subtitle = (
            "> 제조업 AI 스타트업 보류 검토"
            if is_hold_report
            else "> 제조업 AI 스타트업 투자 평가"
        )
        title_block = f"# {startup_name} 투자 검토 보고서\n{report_subtitle}\n\n---\n\n"

        # 점수표 생성
        score_table = _build_score_table(best)

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
        reason = _sanitize_reason(criterion.get("reason", ""))
        rows.append(f"| {label} | {raw}/5 | {weighted} | {reason} |")

    table = (
        f"**판정: {decision_map.get(decision_label, decision_label)} | 종합 점수: {total_score}점**\n\n"
        "| 평가 항목 | 점수 | 가중 점수 | 근거 |\n"
        "|-----------|:----:|----------:|------|\n"
    )
    table += "\n".join(rows)
    table += f"\n| **합계** | | **{total_score}** | |\n"

    return table


def _build_hold_summary(best: dict, evaluation_history: list[dict]) -> str:
    best_name = best.get("startup_profile", {}).get("name", "대표 후보")
    best_score = best.get("investment_decision", {}).get("total_score", 0)

    lines = [
        "## 전체 후보 미달 요약",
        "- 이번 배치는 투자 추천 기준 미달로 보류 처리되었습니다.",
        f"- 대표 보류 후보: {best_name} ({best_score}점)",
    ]

    for item in evaluation_history:
        name = item.get("startup_profile", {}).get("name", "이름 미확인")
        shortfall = _extract_key_shortfall(item.get("investment_decision", {}))
        lines.append(f"- {name}: {shortfall}")

    return "\n".join(lines)


def _extract_key_shortfall(decision: dict) -> str:
    score_breakdown = decision.get("score_breakdown", {})
    if not score_breakdown:
        return "핵심 미달 사유를 확인할 수 없습니다."

    sorted_items = sorted(
        score_breakdown.items(),
        key=lambda pair: float(pair[1].get("weighted_score", 0)),
    )
    top_shortfalls = sorted_items[:2]

    parts: list[str] = []
    for field, item in top_shortfalls:
        label = LABELS.get(field, field)
        reason = _sanitize_reason(item.get("reason", "사유 정보 없음"))
        parts.append(f"{label} 미흡 - {reason}")

    return "; ".join(parts)


def _sanitize_reason(reason: str) -> str:
    cleaned = str(reason).strip()
    cleaned = re.sub(r"\([^)]*(https?://|www\.)[^)]*\)", "", cleaned)
    cleaned = re.sub(r"\(([^)]*출처[^)]*|[^)]*source[^)]*)\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned
