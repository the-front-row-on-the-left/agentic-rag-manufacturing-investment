# Agentic-rag-manufacturing-investment

## 1. 프로젝트 개요

이 저장소는 Git 협업 규칙과 코드 품질 체크를 문서로 정리해 둔 구성입니다.

- Git 전략: `git_commit_and_merge_strategy.md`
- pre-commit 규칙: `pre_commit_rules.md`

아래는 두 문서의 간단 정리본입니다.

## 2. Git/Merge 전략 요약

- 모든 작업은 브랜치에서 수행
- `main`은 직접 푸시/직접 머지 금지
- `main` 반영은 PR(리뷰) 기준으로 진행
- PR 전 `main` 기준으로 rebase 후 충돌 해결
- 커밋 메시지는 `type: 변경 내용 요약` 형식
  - 허용 타입: `feature`, `fix`, `chore`, `docs`, `style`, `delete`, `refactor`
- 작은 단위 PR 권장, PR 본문에 변경 목적/요약/검증 내역 기재
- 머지 전 검증은 기본적으로 pre-commit 및 테스트 통과

추천 커밋 타입 예시:

```text
feature: 신규 분석 에이전트 추가
fix: JSON 파싱 오류 수정
chore: pre-commit 설정 업데이트
docs: 전략 문서 보강
```

## 3. pre-commit 규칙 요약

- 핵심 도구: **Ruff**
  - `ruff check`
  - `ruff format`
- 커밋 전에 포맷/린트 이슈 최소화
- 권장 실행:

```bash
ruff check .
ruff format .
```

- 자동 수정까지 허용 시:

```bash
ruff check . --fix
ruff format .
```

- pre-commit 기본 예시 훅
  - `ruff`
  - `ruff-format`
  - `end-of-file-fixer`, `trailing-whitespace`, `check-yaml`, `check-json`, `check-merge-conflict` 등

## 4. 시작하기 (Getting Started)

필수 환경:

- Python: `3.11`
- 패키지/의존성 관리: `uv`

### 4.1 환경 구성

```bash
# 1) Python 3.11 런타임 준비 (필요 시)
uv python install 3.11

# 2) 프로젝트 가상환경 생성 (3.11 지정)
uv venv --python 3.11

# 3) 의존성 동기화
uv sync
```

### 4.2 의존성/도구 확인

```bash
uv run python -V
uv run pre-commit --version
```

### 4.3 pre-commit 설정

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

### 4.4 실행 환경 활성화(옵션)

```bash
source .venv/bin/activate
```

> 이미 `pyproject.toml`에 `requires-python = ">=3.11"`가 설정되어 있으면
> Python 3.11 이상을 기준으로 관리됩니다.
