# Agentic-rag-manufacturing-investment

제조업 AI 스타트업 투자 가능성 평가를 위한 LangGraph 기반 Agentic RAG 프로젝트입니다.

## 시작하기

### 1) 환경

- Python: `3.11`
- 패키지 관리: `uv`
- 벡터스토어: `Qdrant`

### 2) 설치

```bash
uv python install 3.11
uv venv --python 3.11
uv sync
cp .env.example .env
docker compose up -d qdrant
```

기존 가상환경이 이미 활성화돼 있으면 끄고 진행하는 편이 안전합니다.

```bash
deactivate  # already active virtualenv only
uv sync
```

### 3) RAG 문서 준비

- PDF 위치: `data/rag_docs/*.pdf`
- 메타데이터 파일: `data/rag_docs/manifest.json`

`manifest.json`을 현재 PDF 파일 기준으로 맞춘 뒤 인덱스를 생성합니다.

### 4) 벡터 인덱스 생성

벡터 인덱스는 앱 실행 시 자동 생성되지 않습니다. 아래 명령으로 명시적으로 생성해야 합니다.

```bash
uv run python build_index.py
```

### 5) 앱 실행

```bash
uv run python app.py --keyword "manufacturing AI startup" --max-candidates 5
```

### 6) 종료

```bash
docker compose down
```

## 결과 위치

- `outputs/final_report_*.md`
- `outputs/final_state_*.json`

## 아키텍처

- `startup_search`
- `company_summary`
- `tech_analysis` (RAG)
- `market_analysis` (RAG)
- `competitor_analysis`
- `investment_decision`
- `report_writer`

## 개발 워크플로우

### Git / PR 규칙

- 브랜치 단위로 작업하고 `main`에는 직접 커밋/직접 머지하지 않습니다.
- `main` 반영은 PR로만 수행합니다.
- PR 전 `git fetch` 후 `main` 기준으로 rebase 합니다.
- 커밋 메시지는 `type: 변경 내용 요약` 형식입니다.
- 허용 타입: `feature`, `fix`, `chore`, `docs`, `style`, `delete`, `refactor`

예시:

```text
feature: 신규 분석 에이전트 추가
fix: JSON 파싱 오류 수정
docs: Git 전략 문서 보강
chore: 의존성 업데이트
```

### pre-commit

- 기본 검사: `ruff check .`
- 기본 포맷: `ruff format .`

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Notes

- 외부 웹 검색: Tavily
- 임베딩: `BAAI/bge-m3`
- 벡터스토어: Qdrant
- LLM: `langchain-openai`
