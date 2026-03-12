# Orchestration Guide

## 목적

이 문서는 LangGraph 기반 제조업 AI 스타트업 투자 평가 파이프라인의 전체 연결 구조, 상태 전달 방식, 에이전트 계약, 역할 분담을 고정하기 위한 협업 기준서다.  
목표는 팀원 간 인터페이스 충돌을 막고, 상태 필드와 입출력 포맷 변경 시 영향 범위를 빠르게 판단할 수 있게 만드는 것이다.

## 1번 담당 범위

1번의 책임 범위는 `오케스트레이션 + 스타트업 탐색 시작부`다.

- 그래프 시작점과 라우팅 규칙을 정의하고 유지한다.
- `GraphState` 중 탐색 시작부와 연결되는 공통 상태를 관리한다.
- `startup_search -> company_summary` 구간의 입력/출력 계약을 고정한다.
- 후보 반복 평가 시 다음 후보 선택과 상태 초기화 규칙이 유지되도록 한다.

### 1번 주요 산출물

- 그래프 흐름 설명
- 스타트업 후보 리스트(`candidate_startups`)
- 현재 평가 대상(`selected_startup`)
- 기업 프로필 JSON(`startup_profile`)

## 전체 그래프 흐름

기본 흐름은 아래와 같다.

```text
startup_search
  -> company_summary
  -> tech_analysis
  -> market_analysis
  -> competitor_analysis
  -> investment_decision
  -> report_writer
```

현재 구현상 `company_summary` 이후 `tech_analysis` 와 `market_analysis` 는 둘 다 실행되며, 두 결과가 준비된 뒤 `competitor_analysis` 로 합류한다.

### 시작부 실행 흐름

`startup_search` 와 `company_summary` 는 1번이 직접 설명해야 하는 시작부 흐름이다.

1. `START` 에서 항상 `startup_search` 로 진입한다.
2. `startup_search` 는 기존 후보 목록이 없으면 웹 검색 결과를 바탕으로 `candidate_startups` 를 생성한다.
3. 첫 후보를 `selected_startup` 으로 선택하고 `current_index=0` 으로 설정한다.
4. 이미 후보 목록이 있으면 새 검색 없이 다음 후보를 선택한다.
5. 더 이상 볼 후보가 없으면 `selected_startup=None`, `search_done=True` 로 종료 상태를 만든다.
6. `startup_router` 는 `selected_startup` 와 `search_done` 값을 보고 `company_summary` 또는 `report_writer` 로 보낸다.
7. `company_summary` 는 `selected_startup` 을 입력으로 받아 검색 근거를 보강한 `startup_profile` 을 생성한다.

## 그래프 라우팅 규칙

### 1. `startup_search -> company_summary / report_writer`

- `selected_startup` 이 `None` 이거나 `search_done == True` 이면 `report_writer` 로 이동한다.
- 그 외에는 `company_summary` 로 이동한다.

### 2. `investment_decision -> startup_search / report_writer`

- `investment_decision` 이 비어 있으면 `report_writer` 로 이동한다.
- `investment_decision.decision == "recommend"` 이면 즉시 `report_writer` 로 이동한다.
- `decision` 이 `conditional_review` 또는 `hold` 이고, 아직 평가하지 않은 후보가 남아 있으면 다음 후보를 보기 위해 `startup_search` 로 돌아간다.
- 남은 후보가 없으면 `report_writer` 로 이동한다.

## GraphState 정의

현재 코드 기준 주요 상태 필드는 아래와 같다.

| 필드 | 타입 | 작성자 | 주요 사용자 | 설명 |
| --- | --- | --- | --- | --- |
| `input_keyword` | `str` | app 초기 입력 | `startup_search` | 사용자의 탐색 키워드 |
| `domain` | `str` | app 초기 입력 | `startup_search` | 도메인 기본값, 현재는 `manufacturing` |
| `max_candidates` | `int` | app 초기 입력 | `startup_search` | 평가할 최대 후보 수 |
| `candidate_startups` | `list[StartupCandidate]` | `startup_search` | `startup_search` | 검색된 전체 후보 목록 |
| `current_index` | `int` | `startup_search` | `startup_search`, `investment_decision` | 현재 평가 중인 후보 인덱스 |
| `selected_startup` | `StartupCandidate \| None` | `startup_search` | `company_summary` | 현재 라운드의 대상 후보 |
| `search_done` | `bool` | `startup_search` | 라우터 | 후보 평가 종료 여부 |
| `startup_profile` | `StartupProfile \| None` | `company_summary` | 후속 전 분석 agent | 기업 요약 프로필 |
| `tech_analysis` | `TechAnalysis \| None` | `tech_analysis` | `competitor_analysis`, `investment_decision` | 기술 분석 결과 |
| `tech_references` | `list[str]` | `tech_analysis` | `investment_decision`, `report_writer` | 기술 분석 근거 출처 |
| `market_analysis` | `MarketAnalysis \| None` | `market_analysis` | `competitor_analysis`, `investment_decision` | 시장 분석 결과 |
| `market_references` | `list[str]` | `market_analysis` | `investment_decision`, `report_writer` | 시장 분석 근거 출처 |
| `competitor_analysis` | `CompetitorAnalysis \| None` | `competitor_analysis` | `investment_decision` | 경쟁사 비교 결과 |
| `competitor_references` | `list[str]` | `competitor_analysis` | `investment_decision`, `report_writer` | 경쟁 분석 근거 출처 |
| `investment_decision` | `InvestmentDecision \| None` | `investment_decision` | 라우터, `report_writer` | 최종 투자 판단 |
| `recommended_startups` | `list[dict]` | `investment_decision` | `report_writer` | 추천 판정 기업 누적 |
| `held_startups` | `list[dict]` | `investment_decision` | `report_writer` | 보류 판정 기업 누적 |
| `evaluation_history` | `list[dict]` | `investment_decision` | `report_writer` | 모든 평가 결과 누적 |
| `references` | `list[str]` | 각 분석 agent | `report_writer` | 전체 참고문헌 누적 |
| `final_report_markdown` | `str` | `report_writer` | app 출력 | 최종 보고서 markdown |

## 에이전트 계약

### `startup_search`

- 입력
  - `input_keyword`
  - `domain`
  - `max_candidates`
  - 선택적으로 기존 `candidate_startups`, `current_index`
- 출력
  - `candidate_startups`
  - `current_index`
  - `selected_startup`
  - `search_done`
  - `references`
- 실패 처리
  - 후보가 하나도 없으면 예외를 발생시킨다.
  - 다음 후보 선택 시에는 분석 결과 필드를 초기화한다.
  - 후보를 모두 평가한 뒤에는 `selected_startup=None`, `search_done=True` 로 종료 상태를 반환한다.

### `company_summary`

- 입력
  - `selected_startup`
- 출력
  - `startup_profile`
  - `references`
- 실패 처리
  - `selected_startup` 이 없으면 예외를 발생시킨다.

### `tech_analysis`

- 입력
  - `startup_profile`
- 출력
  - `tech_analysis`
  - `tech_references`
  - `references`
- 실패 처리
  - `startup_profile` 이 없으면 예외를 발생시킨다.

### `market_analysis`

- 입력
  - `startup_profile`
- 출력
  - `market_analysis`
  - `market_references`
  - `references`
- 실패 처리
  - `startup_profile` 이 없으면 예외를 발생시킨다.

### `competitor_analysis`

- 입력
  - `startup_profile`
  - `tech_analysis`
  - `market_analysis`
- 출력
  - `competitor_analysis`
  - `competitor_references`
  - `references`
- 실패 처리
  - 세 입력 중 하나라도 없으면 예외를 발생시킨다.

### `investment_decision`

- 입력
  - `startup_profile`
  - `tech_analysis`
  - `market_analysis`
  - `competitor_analysis`
  - 각종 reference 필드
- 출력
  - `investment_decision`
  - `evaluation_history`
  - `recommended_startups` 또는 `held_startups`
- 실패 처리
  - 필수 분석 결과가 누락되면 예외를 발생시킨다.

### `report_writer`

- 입력
  - `evaluation_history`
  - `references`
- 출력
  - `final_report_markdown`
- 실패 처리
  - 평가 결과가 없으면 빈 결과 리포트를 생성한다.

## 입출력 스키마

| 생산자 | 출력 필드 | 형식 | 소비자 | 설명 |
| --- | --- | --- | --- | --- |
| `startup_search` | `candidate_startups` | `list[StartupCandidate]` | `startup_search`, 라우터 | 검색된 후보 전체 목록 |
| `startup_search` | `current_index` | `int` | `startup_search`, `investment_decision` | 현재 평가 중인 후보 위치 |
| `startup_search` | `selected_startup` | `StartupCandidate` | `company_summary` | 대상 기업 최소 프로필 |
| `startup_search` | `search_done` | `bool` | 라우터 | 후보 평가 종료 여부 |
| `company_summary` | `startup_profile` | `StartupProfile` | `tech_analysis`, `market_analysis`, `competitor_analysis`, `investment_decision` | 정규화된 기업 개요 |
| `tech_analysis` | `tech_analysis` | `TechAnalysis` | `competitor_analysis`, `investment_decision`, `report_writer` | 기술/배포성 평가 |
| `tech_analysis` | `tech_references` | `list[str]` | `investment_decision`, `report_writer` | 기술 분석 근거 |
| `market_analysis` | `market_analysis` | `MarketAnalysis` | `competitor_analysis`, `investment_decision`, `report_writer` | 시장/ROI 평가 |
| `market_analysis` | `market_references` | `list[str]` | `investment_decision`, `report_writer` | 시장 분석 근거 |
| `competitor_analysis` | `competitor_analysis` | `CompetitorAnalysis` | `investment_decision`, `report_writer` | 경쟁 구도와 차별점 |
| `competitor_analysis` | `competitor_references` | `list[str]` | `investment_decision`, `report_writer` | 경쟁 분석 근거 |
| `investment_decision` | `investment_decision` | `InvestmentDecision` | 라우터, `report_writer` | 최종 판정 |
| `investment_decision` | `evaluation_history` | `list[dict]` | `report_writer` | 평가 이력 누적 |
| `report_writer` | `final_report_markdown` | `str` | 최종 출력 | 사용자 제공 보고서 |

## 상태 필드 책임

### 작성 원칙

- 한 필드에는 기본 작성자 1명을 둔다.
- 다른 agent 는 해당 필드를 읽을 수는 있지만, 덮어쓰기는 하지 않는다.
- 예외적으로 `references` 는 누적 필드이므로 각 agent 가 append 성격으로 추가할 수 있다.

### 변경 규칙

- `selected_startup` 이 바뀌면 아래 필드는 반드시 초기화한다.
  - `startup_profile`
  - `tech_analysis`
  - `market_analysis`
  - `competitor_analysis`
  - `investment_decision`
  - `tech_references`
  - `market_references`
  - `competitor_references`
- 분석 결과 객체는 생성 후 구조를 변경하지 않는다. 수정이 필요하면 새 스키마 버전을 정의한다.
- `evaluation_history` 에 적재된 객체는 불변 데이터로 취급한다.

## 협업 포인트

### 2번 담당과 연결

- `tech_analysis`, `market_analysis` 는 retriever 출력 형식에 직접 의존한다.
- `tech_references`, `market_references` 는 문자열 리스트가 아니라, 향후 확장 가능성을 고려해 동일 포맷을 유지해야 한다.

### 3번 담당과 연결

- `investment_decision` 입력으로 들어가는 `tech_analysis`, `market_analysis`, `competitor_analysis` 는 구조가 고정되어야 한다.
- 점수표 계산 로직은 스키마 필드명에 의존하므로 임의 필드명 변경 금지.

### 4번 담당과 연결

- `report_writer` 는 `evaluation_history` 와 `references` 를 사용한다.
- 최종 보고서 포맷 변경 시 `docs/report_format.md` 와 함께 수정해야 한다.

## 파일 책임

| 역할 | 주 담당 파일 | 수정 가능 범위 | 가능하면 건드리지 말아야 할 파일 |
| --- | --- | --- | --- |
| 1번 | `src/graph.py`, `src/state.py`, `src/agents/startup_search.py`, `src/agents/company_summary.py`, `docs/orchestration.md` | 그래프 연결, 라우터, 공통 상태, 스타트업 탐색 시작부, 기업 프로필 생성 연결 | 분석 agent 내부 로직 세부 구현 |
| 2번 | `src/rag/index_builder.py`, `src/rag/retriever.py`, `docs/rag_rules.md` | 문서 인덱싱, chunking, metadata, 검색 출력 | 투자 판단 스키마 |
| 3번 | `src/agents/tech_analysis.py`, `src/agents/market_analysis.py`, `src/agents/competitor_analysis.py`, `src/agents/investment_decision.py` | 분석 구조, 점수 로직 | 그래프 상태 필드 계약 |
| 4번 | `src/agents/report_writer.py`, `docs/report_format.md`, `docs/demo_scenarios.md` | 최종 보고서 형식, 데모 흐름 | RAG 전처리 규칙 |

## 변경 공유 규칙

### 공통 스키마 수정

- `src/schemas.py` 변경 시 팀원 전원에게 공유한다.
- 필드 삭제 또는 이름 변경은 금지하고, 필요 시 새 필드를 추가한다.

### 상태 필드 추가

- `src/state.py` 에 필드를 추가하면 작성자, 사용자, 초기화 규칙을 `docs/orchestration.md` 에 바로 반영한다.

### 출력 포맷 변경

- `tech_references`, `market_references`, `evaluation_history`, `final_report_markdown` 포맷 변경은 단독 변경 금지다.
- 변경 전 영향 대상:
  - `investment_decision`
  - `report_writer`
  - 데모 스크립트

### PR 체크

- 그래프 변경 PR 에는 최소 아래 항목이 포함되어야 한다.
  - 변경된 노드 연결
  - 상태 필드 변경 여부
  - downstream 영향 파일
  - 테스트 또는 수동 검증 결과
