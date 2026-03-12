# Report Format

## 목적

이 문서는 최종 투자 보고서의 목차, 입력 JSON, 작성 규칙, 점수표 형식, decision 표현, reference 표기 방식, 예시를 통일하기 위한 기준서다.  
목표는 발표용 산출물과 평가 문서의 스타일을 고정하고, 어떤 agent 가 리포트를 쓰더라도 동일한 구조를 유지하도록 만드는 것이다.

## 기본 보고서 목차

최종 보고서는 아래 구조를 기본으로 한다.

```markdown
# SUMMARY
## Startup Overview
## Tech Analysis
## Market Analysis
## Competitor Analysis
## Investment Decision
## References
```

참고: 현재 구현된 `report_writer` 는 한국어 섹션명을 사용하고 있다. 본 문서는 팀 공용 출력 계약 기준이며, 실제 코드가 이 규격으로 맞춰질 수 있도록 유지한다.

## 섹션별 입력 데이터

| 섹션 | 입력 JSON 필드 | 설명 |
| --- | --- | --- |
| `# SUMMARY` | `startup_profile`, `investment_decision`, `tech_analysis`, `market_analysis` | 한 페이지 요약 |
| `## Startup Overview` | `startup_profile` | 회사/제품/고객/문제 정의 |
| `## Tech Analysis` | `tech_analysis`, `tech_references` | 기술 구조, 배포성, 제약 |
| `## Market Analysis` | `market_analysis`, `market_references` | 시장성, 성장, 수요, ROI |
| `## Competitor Analysis` | `competitor_analysis`, `competitor_references` | 경쟁사 구도, 차별화, 리스크 |
| `## Investment Decision` | `investment_decision` | 점수표, pros/cons, 조건부 검토 내용 |
| `## References` | `references` | 전체 출처 목록 |

## 작성 규칙

### 공통 규칙

- 톤은 투자 검토 메모 스타일로 유지한다.
- 과장 표현, 홍보 문구, 추측성 단정은 금지한다.
- 모든 핵심 주장에는 근거가 있어야 한다.
- 가능하면 정성 평가와 정량 포인트를 함께 제시한다.
- 같은 문장을 반복하지 않는다.

### 길이 기준

- `# SUMMARY`: 5~8문장
- `## Startup Overview`: 1~2개 짧은 문단
- `## Tech Analysis`: 4~8개 핵심 포인트
- `## Market Analysis`: 4~8개 핵심 포인트
- `## Competitor Analysis`: 3~6개 핵심 포인트
- `## Investment Decision`: 판정 요약 + 점수표 + 제언
- `## References`: 불릿 또는 표

## 섹션별 필수 요소

### `# SUMMARY`

- 회사명
- 무엇을 해결하는지
- 핵심 기술/제품
- 시장성 핵심 요약
- 최종 decision
- decision 에 대한 핵심 이유 2~3개

### `## Startup Overview`

- 회사명, 국가, 웹사이트
- 핵심 제품
- 해결하려는 문제
- 타겟 산업
- 고객 유형
- 사용 사례

### `## Tech Analysis`

- 핵심 기술
- 필요한 데이터
- 배포 방식
- 강점
- 한계
- 현장 통합 제약
- 제조 현장 적용성 요약

### `## Market Analysis`

- 타겟 산업
- 시장 크기 또는 시장 기회 설명
- 성장률 또는 수요 확산 근거
- 고객 pain point
- ROI 포인트
- 상용화 관점의 매력도

### `## Competitor Analysis`

- direct / indirect / alternative 구분
- 차별화 포인트
- 경쟁 리스크
- 고객 확보 또는 배포 측면 우위/열위

### `## Investment Decision`

- 최종 decision
- 총점
- 점수표
- pros
- cons
- conditions

### `## References`

- 웹 출처와 RAG 출처를 함께 표기
- 중복 제거
- 페이지 정보가 있으면 포함

## 점수표 형식

점수표는 아래 컬럼을 유지한다.

| criterion | raw score | weighted score | reason |
| --- | ---: | ---: | --- |
| problem_fit | 1-5 | float | 근거 설명 |
| market_opportunity | 1-5 | float | 근거 설명 |
| technology | 1-5 | float | 근거 설명 |
| deployability | 1-5 | float | 근거 설명 |
| data_availability | 1-5 | float | 근거 설명 |
| integration | 1-5 | float | 근거 설명 |
| scalability | 1-5 | float | 근거 설명 |
| team_capability | 1-5 | float | 근거 설명 |
| risk_assessment | 1-5 | float | 근거 설명 |

### 표기 원칙

- `raw score` 는 1~5 정수다.
- `weighted score` 는 계산 결과를 소수점 1~2자리로 표기한다.
- `reason` 은 1문장 또는 최대 2문장으로 짧고 명확하게 쓴다.

## decision 표현 규칙

### `recommend`

아래 조건이 충족될 때 사용한다.

- 기술 적용성이 비교적 명확함
- 제조 현장 도입 장벽이 관리 가능함
- 시장 수요와 ROI 논리가 설득력 있음
- 경쟁 대비 차별점이 존재함

표현 예시:

- `recommend: 기술 적용성과 시장 타당성이 모두 확인되어 우선 검토 대상으로 추천한다.`

### `conditional_review`

아래와 같은 경우 사용한다.

- 시장성은 있으나 기술 검증이 부족함
- 기술은 매력적이나 데이터/통합 리스크가 큼
- 고객 확보나 배포 모델에 추가 검증이 필요함

표현 예시:

- `conditional_review: 투자 검토는 가능하나, 데이터 확보와 현장 통합성 검증이 선행되어야 한다.`

### `hold`

아래와 같은 경우 사용한다.

- 근거가 부족함
- 기술 차별성이 불충분함
- 시장 타당성 또는 배포 가능성이 낮음
- 경쟁 우위가 약함

표현 예시:

- `hold: 현재 공개 정보 기준으로는 투자 우선순위를 높게 두기 어렵다.`

## references 표기 방식

### 표기 원칙

- 웹과 RAG 출처를 한 목록으로 합친다.
- 중복은 제거한다.
- 발행기관, 제목, 연도, URL 또는 파일명, 페이지를 최대한 포함한다.

### 권장 형식

```text
- OECD (2021). Artificial Intelligence Diffusion and Applications in Manufacturing. doc1_oecd_ai_manufacturing.pdf, p.12
- Company website. Product overview. https://example.com/product
```

## 예시 출력

```markdown
# SUMMARY
이 스타트업은 제조 라인의 비전 검사 자동화를 제공하며, 초기 고객군과 적용 시나리오가 비교적 명확하다. 다만 현장 데이터 품질과 통합 복잡도는 검증이 더 필요하다. 종합 판단은 `conditional_review` 이다.

## Startup Overview
- Name: Example Vision AI
- Core Product: Computer vision inspection software for electronics assembly lines
- Target Industry: Electronics, automotive suppliers

## Tech Analysis
- 핵심 기술은 비전 검사 모델과 결함 분류 파이프라인이다.
- 배포는 엣지 또는 온프레미스 요구가 높을 가능성이 있다.
- 고객별 데이터 편차가 커서 초기 셋업 비용이 발생할 수 있다.

## Market Analysis
- 인력 부족과 불량률 절감 수요가 시장 진입 논리를 뒷받침한다.
- ROI 논리는 있으나 고객별 구축 비용 변동성이 크다.

## Competitor Analysis
- direct 경쟁사는 기존 비전 검사 자동화 업체들이다.
- 대체 솔루션으로는 룰 기반 검사와 인력 검사 프로세스가 있다.

## Investment Decision
Decision: conditional_review
Total Score: 3.4

| criterion | raw score | weighted score | reason |
| --- | ---: | ---: | --- |
| technology | 4 | 0.6 | 모델 적용 영역은 명확하나 고객별 데이터 편차가 크다. |

## References
- OECD (2021). Artificial Intelligence Diffusion and Applications in Manufacturing. doc1.pdf, p.12
- Company website. https://example.com
```

## 문체 기준

- 투자 심사역 메모처럼 쓴다.
- 확정적 표현보다 근거 기반 판단 표현을 쓴다.
- `좋다`, `훌륭하다` 같은 추상 형용사는 피한다.
- `~로 보인다`, `~가 확인된다`, `~가 필요하다` 같은 검토형 문장을 사용한다.
