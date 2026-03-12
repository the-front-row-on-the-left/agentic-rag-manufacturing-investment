# Agentic-rag-manufacturing-investment

제조업 AI 스타트업 투자 가능성 평가를 위한 LangGraph 기반 Agentic RAG 프로젝트입니다.

## 시작하기

### 1) 환경

- Python: `3.11`
- 패키지 관리: `uv`

### 2) 설치

```bash
uv python install 3.11
uv venv --python 3.11
uv sync
```

### 3) 실행

```bash
cp .env.example .env
uv run python app.py --keyword "manufacturing AI startup" --max-candidates 5
```

### 4) 결과 위치

- `outputs/final_report_*.md`
- `outputs/final_state_*.json`

## 워크플로우 정리

### Git/PR 규칙

- 브랜치 단위로 작업하고 `main`에는 직접 커밋/직접 머지하지 않는다.
- `main` 반영은 PR로만 수행한다.
- PR 전 `git fetch` 후 `main` 기준으로 rebase 한다.
- 커밋 메시지는 `type: 변경 내용 요약` 형식이다.
- 허용 타입: `feature`, `fix`, `chore`, `docs`, `style`, `delete`, `refactor`

### Commit 메시지 예시

```text
feature: 신규 분석 에이전트 추가
fix: JSON 파싱 오류 수정
docs: Git 전략 문서 보강
chore: 의존성 업데이트
```

### pre-commit 규칙

- 도구는 Ruff 기반이다.
- 기본 검사: `ruff check .`
- 기본 포맷: `ruff format .`
- 권장 훅 실행:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## 아키텍처

- `startup_search`
- `company_summary`
- `tech_analysis` (RAG)
- `market_analysis` (RAG)
- `competitor_analysis`
- `investment_decision`
- `report_writer`
