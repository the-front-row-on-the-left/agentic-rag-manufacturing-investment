"""
보고서 HTML/PDF 출력 유틸리티
- matplotlib 레이더/막대 차트 (한글 NanumGothic 폰트)
- 판정 색상 커버, 카드형 섹션, 점수표 색상 강조
"""

from __future__ import annotations

import base64
import io
import math
import re
import warnings
from pathlib import Path

import markdown as _markdown_lib
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as _fm
import matplotlib.pyplot as plt
from weasyprint import CSS as _CSS, HTML as _HTML

# ── 한글 폰트 등록 ────────────────────────────────────────────────────
_NANUM_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
_NANUM_BOLD_PATH = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
for _fp in (_NANUM_PATH, _NANUM_BOLD_PATH):
    if Path(_fp).exists():
        _fm.fontManager.addfont(_fp)

_KR_FONT = "NanumGothic"

# ── 평가 항목 최대 가중점수 매핑 ────────────────────────────────────────
_MAX_WEIGHTED: dict[str, float] = {
    "문제 적합성": 15.0,
    "시장성": 15.0,
    "기술 경쟁력": 15.0,
    "팀 역량": 15.0,
    "수익 모델": 5.0,
    "성장 잠재력": 10.0,
    "경쟁 우위": 10.0,
    "리스크": 5.0,
    "투자 매력도": 10.0,
}
_DEFAULT_MAX = 10.0


# ── 데이터 파싱 ───────────────────────────────────────────────────────
def _parse_report(md_text: str):
    name_m = re.search(r"^# (.+?) 투자 검토 보고서", md_text, re.MULTILINE)
    startup_name = name_m.group(1) if name_m else "스타트업"

    dec_m = re.search(r"\*\*판정: (.+?) \| 종합 점수: ([\d.]+)점\*\*", md_text)
    decision_text = dec_m.group(1) if dec_m else ""
    total_score = float(dec_m.group(2)) if dec_m else 0.0

    rows = re.findall(r"\| (.+?) \| (\d+)/5 \| ([\d.]+) \| .+? \|", md_text)
    criteria = [
        (r[0].strip(), int(r[1]), float(r[2]))
        for r in rows
        if r[0].strip() not in ("**합계**", "평가 항목")
    ]
    return startup_name, decision_text, total_score, criteria


# ── 차트 생성 ──────────────────────────────────────────────────────────
def _make_radar(criteria: list) -> str:
    labels = [c[0] for c in criteria]
    values = [c[1] for c in criteria]
    N = len(labels)
    if N < 3:
        return ""

    angles = [n / N * 2 * math.pi for n in range(N)]
    angles += angles[:1]
    vals = values + values[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=8.5, color="#2d3748",
                       fontfamily=_KR_FONT)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], size=7, color="#a0aec0")
    ax.grid(color="#cbd5e0", linestyle="--", linewidth=0.6, alpha=0.7)
    ax.spines["polar"].set_color("#cbd5e0")

    ax.fill(angles, vals, color="#3182ce", alpha=0.2)
    ax.plot(angles, vals, color="#2b6cb0", linewidth=2)
    ax.scatter(angles[:-1], values, color="#2b6cb0", s=45, zorder=5)

    plt.tight_layout()
    buf = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="#f8fafc")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def _make_bar(criteria: list) -> str:
    labels = [c[0] for c in criteria]
    weighted = [c[2] for c in criteria]
    maxes = [_MAX_WEIGHTED.get(lb, _DEFAULT_MAX) for lb in labels]

    colors = []
    for w, m in zip(weighted, maxes):
        r = w / m
        colors.append("#38a169" if r >= 0.8 else ("#3182ce" if r >= 0.6 else "#e53e3e"))

    fig, ax = plt.subplots(figsize=(5.8, max(3.2, len(labels) * 0.45)))
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    y = range(len(labels))
    bars = ax.barh(list(y), weighted, color=colors, height=0.55, alpha=0.85)
    for bar, val in zip(bars, weighted):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                f"{val}", va="center", ha="left", fontsize=8.5, color="#2d3748")

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=8.5, color="#2d3748",
                       fontfamily=_KR_FONT)
    ax.set_xlim(0, max(maxes) + 2)
    ax.set_xlabel("가중 점수", fontsize=8, color="#718096",
                  fontfamily=_KR_FONT)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#e2e8f0")
    ax.spines["bottom"].set_color("#e2e8f0")
    ax.tick_params(colors="#718096")
    ax.grid(axis="x", color="#e2e8f0", linestyle="--", linewidth=0.6, alpha=0.7)

    plt.tight_layout()
    buf = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="#f8fafc")
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ── CSS 문자열 ─────────────────────────────────────────────────────────
_CSS_STRING = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Noto Sans KR', 'NanumGothic', Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.8;
  color: #2d3748;
  background: #edf2f7;
}

.page-wrap {
  max-width: 860px;
  margin: 40px auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.10);
  overflow: hidden;
}

/* ── 커버 ── */
.cover {
  background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%);
  color: white;
  padding: 48px 48px 36px;
}
.cover h1 {
  font-size: 22pt;
  font-weight: 700;
  margin-bottom: 8px;
  color: white;
}
.cover .subtitle { font-size: 10pt; color: #bee3f8; font-weight: 300; }
.cover .badges { margin-top: 20px; }
.badge {
  display: inline-block;
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 10pt;
  font-weight: 700;
  margin-right: 8px;
}
.badge-score {
  background: rgba(255,255,255,0.18);
  color: white;
  border: 1.5px solid rgba(255,255,255,0.4);
}

/* ── 본문 ── */
.content { padding: 40px 48px 48px; }

h1 { display: none; }
blockquote { display: none; }
hr { display: none; }

h2 {
  font-size: 13pt;
  font-weight: 700;
  color: #1a365d;
  margin: 36px 0 14px;
  padding: 10px 16px;
  background: #ebf8ff;
  border-left: 4px solid #2b6cb0;
  border-radius: 0 6px 6px 0;
}

h3 {
  font-size: 11pt;
  font-weight: 600;
  color: #2c5282;
  margin: 20px 0 8px;
}

p { margin: 8px 0; }

ul, ol { padding-left: 1.5em; margin: 8px 0; }
li { margin-bottom: 5px; }

strong { font-weight: 700; color: #1a202c; }
a { color: #2b6cb0; word-break: break-all; }

/* ── 표 ── */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9.5pt;
  margin: 16px 0;
}
thead tr { background: #2b6cb0; color: white; }
th { padding: 9px 12px; text-align: left; font-weight: 600; }
td { padding: 7px 12px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
tr:nth-child(even) td { background: #f7fafc; }
/* 점수표 합계 행 */
tr:last-child td { font-weight: 700; background: #ebf8ff; color: #1a365d; }

/* ── 점수표 점수 셀 색상 강조 ── */
.score-high { color: #276749; font-weight: 700; }
.score-mid  { color: #2b6cb0; font-weight: 700; }
.score-low  { color: #c53030; font-weight: 700; }

/* ── 차트 ── */
.charts-row {
  display: flex;
  gap: 20px;
  margin: 20px 0;
}
.chart-box {
  flex: 1;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.chart-title {
  font-size: 9pt;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 10px;
}
.chart-box img { width: 100%; max-width: 320px; }

/* ── 레퍼런스 섹션 ── */
.refs-section {
  margin-top: 40px;
  padding: 20px 24px;
  background: #f7fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.refs-section h2 {
  background: none;
  border-left: none;
  padding: 0 0 8px;
  margin: 0 0 12px;
  font-size: 11pt;
  border-bottom: 1px solid #e2e8f0;
}
"""


# ── HTML 생성 ──────────────────────────────────────────────────────────
def md_to_html(md_text: str) -> str:
    startup_name, decision_text, total_score, criteria = _parse_report(md_text)

    # 판정 배지 색상
    if "추천" in decision_text and "조건부" not in decision_text:
        dec_bg, dec_color, dec_border = "#c6f6d5", "#276749", "#38a169"
    elif "조건부" in decision_text:
        dec_bg, dec_color, dec_border = "#fefcbf", "#744210", "#d69e2e"
    else:
        dec_bg, dec_color, dec_border = "#fed7d7", "#742a2a", "#e53e3e"

    # 차트
    radar_b64 = _make_radar(criteria)
    bar_b64 = _make_bar(criteria)
    charts_html = ""
    if radar_b64 and bar_b64:
        charts_html = f"""
<div class="charts-row">
  <div class="chart-box">
    <div class="chart-title">평가 항목별 원점수 (레이더)</div>
    <img src="data:image/png;base64,{radar_b64}" alt="레이더 차트">
  </div>
  <div class="chart-box">
    <div class="chart-title">항목별 가중 점수</div>
    <img src="data:image/png;base64,{bar_b64}" alt="막대 차트">
  </div>
</div>"""

    body = _markdown_lib.markdown(
        md_text, extensions=["tables", "fenced_code", "nl2br"]
    )

    # 투자 판단 섹션 바로 뒤에 차트 주입
    body = body.replace(
        "<h2>투자 판단 및 제언</h2>",
        f"<h2>투자 판단 및 제언</h2>{charts_html}",
    )

    badge_style = (
        f"background:{dec_bg};color:{dec_color};"
        f"border:1.5px solid {dec_border};"
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>{_CSS_STRING}</style>
</head>
<body>
<div class="page-wrap">
  <div class="cover">
    <h1>{startup_name} 투자 검토 보고서</h1>
    <div class="subtitle">제조업 AI 스타트업 투자 평가 시스템</div>
    <div class="badges">
      <span class="badge" style="{badge_style}">{decision_text}</span>
      <span class="badge badge-score">종합 {total_score}점</span>
    </div>
  </div>
  <div class="content">
    {body}
  </div>
</div>
</body>
</html>"""


# ── PDF 변환 ───────────────────────────────────────────────────────────
def html_to_pdf(html_str: str, output_path: str | Path) -> None:
    _HTML(string=html_str).write_pdf(
        str(output_path),
        stylesheets=[
            _CSS(
                string=(
                    "@page { size: A4; margin: 0; }"
                    "body { background: white; }"
                    ".page-wrap { max-width: 100%; margin: 0; "
                    "border-radius: 0; box-shadow: none; }"
                )
            )
        ],
    )


# ── 통합 출력 ──────────────────────────────────────────────────────────
def export_report(md_text: str, base_path: str | Path) -> dict[str, Path]:
    base = Path(base_path)
    md_path   = base.with_suffix(".md")
    html_path = base.with_suffix(".html")
    pdf_path  = base.with_suffix(".pdf")

    md_path.write_text(md_text, encoding="utf-8")

    html_str = md_to_html(md_text)
    html_path.write_text(html_str, encoding="utf-8")

    try:
        html_to_pdf(html_str, pdf_path)
    except Exception as e:
        print(f"[pdf_export] PDF 생성 실패: {e}")
        pdf_path = None

    return {"md": md_path, "html": html_path, "pdf": pdf_path}