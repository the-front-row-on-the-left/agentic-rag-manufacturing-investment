# Pre-commit 규칙

이 문서는 본 프로젝트에서 사용하는 pre-commit 규칙을 정리한다.  
목적은 코드 스타일을 일관되게 유지하고, 리뷰 전에 기본적인 품질 검사를 자동으로 수행하는 데 있다.

---

## 1. 기본 원칙

본 프로젝트는 `pre-commit`을 사용하여 커밋 시점에 코드 품질 검사를 자동으로 수행한다.  
Python 코드에 대해서는 **Ruff**를 기준으로 다음 두 가지를 적용한다.

- **Linter**: `ruff check`
- **Formatter**: `ruff format`

커밋 전에 위 검사가 통과하지 않으면 커밋이 차단될 수 있다.

---

## 2. 적용 목적

pre-commit을 사용하는 목적은 다음과 같다.

- 불필요한 스타일 차이 감소
- 사소한 문법 및 정적 분석 이슈의 조기 발견
- 리뷰 과정에서 스타일 논쟁 최소화
- 팀 전체 코드베이스의 일관성 유지

---

## 3. 사용 도구

### Ruff Linter
`ruff check`를 사용하여 다음과 같은 문제를 사전에 점검한다.

- 사용하지 않는 import
- 불필요한 변수
- 간단한 문법 및 스타일 문제
- 일부 잠재적 버그 패턴

### Ruff Formatter
`ruff format`을 사용하여 코드 포맷을 통일한다.

- 들여쓰기
- 줄바꿈
- 공백 규칙
- 문자열 및 코드 레이아웃

---

## 4. 권장 실행 순서

로컬 개발 중에는 아래 순서로 점검하는 것을 권장한다.

```bash
ruff check .
ruff format .
```

또는 수정 가능한 항목까지 포함하려면 다음과 같이 실행할 수 있다.

```bash
ruff check . --fix
ruff format .
```

---

## 5. pre-commit 설치 및 실행

### 설치

```bash
pip install pre-commit
pre-commit install
```

### 전체 파일 대상 수동 실행

```bash
pre-commit run --all-files
```

---

## 6. 권장 pre-commit 설정 예시

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.13
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

> 버전은 팀에서 사용하는 시점에 맞추어 조정할 수 있다.

---

## 7. 예외 처리 원칙

다음과 같은 경우에만 예외를 고려한다.

- 외부 라이브러리 제약으로 인해 특정 스타일을 강제하기 어려운 경우
- 자동 수정 시 의미가 훼손되는 경우
- 임시 실험 코드이지만 반드시 별도 브랜치에서만 관리되는 경우

예외가 필요한 경우에는 임의로 무시하지 않고, 팀원과 합의 후 적용한다.

---

## 8. CI 연계 권장 사항

가능하다면 pre-commit 규칙을 로컬에서만 끝내지 않고 CI에서도 동일하게 검증하는 것을 권장한다.

권장 검증 항목:

- `ruff check .`
- `ruff format --check .`

이렇게 하면 로컬 환경 차이로 인해 발생하는 누락을 줄일 수 있다.

---

## 9. 추가 권장 사항

아래 항목도 함께 적용하면 품질 유지에 도움이 된다.

- 파일 끝 줄 개행 유지
- trailing whitespace 제거
- 큰 파일 또는 불필요한 바이너리 파일 커밋 방지
- merge conflict marker 자동 탐지
- YAML / JSON / Markdown 기본 문법 검사

예시 hook:

- `end-of-file-fixer`
- `trailing-whitespace`
- `check-merge-conflict`
- `check-yaml`
- `check-json`

---

## 10. 운영 원칙 요약

- Python 코드 스타일의 단일 기준은 **Ruff**로 한다.
- 커밋 전에 linter와 formatter를 반드시 통과하도록 한다.
- 자동 수정 가능한 문제는 우선 자동 수정 후 커밋한다.
- pre-commit 규칙은 로컬과 CI에서 최대한 동일하게 유지한다.
