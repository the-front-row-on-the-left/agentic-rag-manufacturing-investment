from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.graph import build_graph
from src.utils.io import ensure_dir, to_jsonable

try:
    from src.utils.pdf_export import export_report
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manufacturing AI startup investment evaluation agent"
    )
    parser.add_argument(
        "--keyword",
        default=None,
        help="Search keyword. Example: 'manufacturing AI startup'",
    )
    parser.add_argument(
        "--domain",
        default=None,
        help="Domain keyword. Default: manufacturing",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=None,
        help="Maximum number of startup candidates to evaluate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings(
        input_keyword=args.keyword,
        domain=args.domain,
        max_candidates=args.max_candidates,
    )
    ensure_dir(settings.output_dir)

    graph = build_graph(settings=settings)

    initial_state: dict[str, Any] = {
        "input_keyword": settings.input_keyword,
        "domain": settings.domain,
        "max_candidates": settings.max_candidates,
        "candidate_startups": [],
        "current_index": -1,
        "selected_startup": None,
        "startup_profile": None,
        "tech_analysis": None,
        "tech_references": [],
        "market_analysis": None,
        "market_references": [],
        "competitor_analysis": None,
        "competitor_references": [],
        "investment_decision": None,
        "recommended_startups": [],
        "held_startups": [],
        "evaluation_history": [],
        "references": [],
        "final_report_markdown": "",
        "search_done": False,
    }

    final_state = graph.invoke(initial_state, config={"recursion_limit": 50})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = settings.output_dir / f"final_report_{timestamp}.md"
    state_path = settings.output_dir / f"final_state_{timestamp}.json"

    md_content = final_state.get("final_report_markdown", "")
    report_path.write_text(md_content, encoding="utf-8")
    state_path.write_text(
        json.dumps(to_jsonable(final_state), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if _PDF_AVAILABLE:
        html_path = settings.output_dir / f"final_report_{timestamp}.html"
        pdf_path = settings.output_dir / f"final_report_{timestamp}.pdf"
        try:
            export_report(
                md_path=report_path,
                html_path=html_path,
                pdf_path=pdf_path,
            )
            print(f"[html]   {html_path}")
            print(f"[pdf]    {pdf_path}")
        except Exception as e:
            print(f"[warn]   HTML/PDF 변환 실패: {e}")
    else:
        print("[warn]   weasyprint 미설치 — HTML/PDF 출력 생략 (다음 이슈에서 의존성 추가 예정)")

    decision = final_state.get("investment_decision")
    if decision:
        print(f"[done] last decision: {decision.decision} ({decision.total_score})")
    else:
        print("[done] no final investment decision object found")

    print(f"[report] {report_path}")
    print(f"[state]  {state_path}")


if __name__ == "__main__":
    main()