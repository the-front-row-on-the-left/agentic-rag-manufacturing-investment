from __future__ import annotations

from pathlib import Path

# weasyprint, markdown 은 다음 이슈(의존성 추가) 완료 후 top-level import로 이동

_CSS_STRING = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');

@page {
    margin: 2.2cm 2.5cm;
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #888;
    }
}

body {
    font-family: 'Noto Sans KR', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.75;
    color: #1a1a1a;
}

h1 {
    font-size: 20pt;
    font-weight: 700;
    color: #0d1f3c;
    border-bottom: 2px solid #0d1f3c;
    padding-bottom: 6px;
    margin-top: 0;
}

h2 {
    font-size: 13pt;
    font-weight: 700;
    color: #1a3a5c;
    border-left: 4px solid #1a3a5c;
    padding-left: 10px;
    margin-top: 28px;
}

h3 {
    font-size: 11pt;
    font-weight: 700;
    color: #2c5282;
    margin-top: 18px;
}

blockquote {
    border-left: 3px solid #90aecb;
    margin: 4px 0 16px 0;
    padding: 4px 12px;
    color: #555;
    font-size: 9.5pt;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 16px 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5pt;
    margin: 14px 0;
    page-break-inside: avoid;
}

thead tr {
    background-color: #1a3a5c;
    color: white;
}

th {
    padding: 7px 10px;
    text-align: left;
    font-weight: 700;
}

td {
    padding: 6px 10px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
}

tr:nth-child(even) td {
    background-color: #f7fafc;
}

tr:last-child td {
    font-weight: 700;
    background-color: #edf2f7;
}

ul, ol {
    padding-left: 1.4em;
    margin: 6px 0;
}

li {
    margin-bottom: 4px;
}

strong {
    font-weight: 700;
    color: #1a1a1a;
}

a {
    color: #2b6cb0;
    word-break: break-all;
}

p {
    margin: 6px 0;
}

code {
    font-size: 9pt;
    background: #f0f4f8;
    padding: 1px 4px;
    border-radius: 3px;
}
"""


def md_to_html(md_text: str) -> str:
    """마크다운 문자열을 완전한 HTML 문자열로 변환한다."""
    import markdown  # 다음 이슈(의존성 추가) 완료 후 top-level로 이동
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
{body}
</body>
</html>"""


def html_to_pdf(html_text: str, pdf_path: Path) -> None:
    """HTML 문자열을 PDF 파일로 변환한다."""
    from weasyprint import CSS, HTML  # 다음 이슈(의존성 추가) 완료 후 top-level로 이동
    css = CSS(string=_CSS_STRING)
    HTML(string=html_text).write_pdf(
        target=str(pdf_path),
        stylesheets=[css],
    )


def export_report(md_path: Path, html_path: Path, pdf_path: Path) -> None:
    """마크다운 보고서를 HTML과 PDF로 동시 출력한다."""
    md_text = md_path.read_text(encoding="utf-8")
    html_text = md_to_html(md_text)

    html_path.write_text(html_text, encoding="utf-8")
    html_to_pdf(html_text, pdf_path)