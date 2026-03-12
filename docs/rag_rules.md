# RAG Rules

## 목적

이 문서는 제조업 투자 평가용 RAG 파이프라인의 문서 범위, chunking, metadata, indexing, retriever 출력 형식, 품질 기준을 표준화하기 위한 기준서다.  
목표는 기술 분석과 시장 분석에서 같은 문서를 보더라도 동일한 품질 기준과 동일한 참조 포맷을 유지하도록 만드는 것이다.

## 대상 문서 범위

RAG 코퍼스는 `data/rag_docs/` 아래 PDF 문서로 구성한다. 기본적으로 4개 문서를 가정하며, 팀 내에서는 `DOC1 ~ DOC4` 로 부른다.

| 문서 | 권장 성격 | 활용 중심 |
| --- | --- | --- |
| `DOC1` | 제조업 내 AI 도입, 확산, 적용 사례 리포트 | 기술 분석, 도입 장벽 |
| `DOC2` | 산업 현장 구현 전략, 데이터 준비, 운영 고려사항 문서 | 기술 분석, 배포 가능성 |
| `DOC3` | 글로벌 제조업 트렌드, 시장 전망, 산업 구조 변화 리포트 | 시장 분석 |
| `DOC4` | 제조업 AI 기회/위험, ROI, 채택 패턴 리포트 | 시장 분석, 투자 리스크 |

### 파일 범위

- 실제 파일 위치: `data/rag_docs/*.pdf`
- 메타데이터 등록 파일: `data/rag_docs/manifest.json`
- 샘플 참고: `data/rag_docs/manifest.sample.json`

## 문서별 활용도

### 기술 분석 중심

- 제조 현장 적용성
- 배포 방식
- 데이터 수집 조건
- MES/ERP/PLC 연동
- 엣지 추론, 온프레미스 제약
- 모델 운영 및 유지보수 부담

주 사용 문서:

- `DOC1`
- `DOC2`

### 시장 분석 중심

- 제조업 자동화 수요
- 인력 부족/품질 비용/다운타임 비용
- 시장 성장률
- ROI 포인트
- 고객 pain point

주 사용 문서:

- `DOC3`
- `DOC4`

## chunking 규칙

현재 구현 기본값은 아래와 같다.

- `chunk_size`: `1200`
- `chunk_overlap`: `200`
- splitter: `RecursiveCharacterTextSplitter`

### 분할 기준

- 1차 단위는 PDF 페이지다.
- 페이지에서 텍스트를 추출한 뒤 whitespace 를 정리한다.
- 텍스트가 비어 있는 페이지는 인덱싱하지 않는다.
- 이후 character 기반 splitter 로 chunk 를 생성한다.

### 운영 규칙

- chunk 는 문장 중간 절단이 일부 발생할 수 있으므로, retrieval 후 LLM 이 문맥을 재구성할 수 있을 정도의 길이를 유지한다.
- 지나치게 작은 chunk 를 늘리지 않는다. 1개 chunk 가 너무 짧으면 근거성이 약해진다.
- 표나 도표 설명이 깨진 경우에는 해당 페이지 chunk 를 낮은 신뢰도로 본다.

## metadata 규칙

모든 chunk 는 아래 metadata 를 가져야 한다.

| 키 | 설명 | 필수 여부 |
| --- | --- | --- |
| `doc_id` | 문서 식별자 | 필수 |
| `filename` | PDF 파일명 | 필수 |
| `title` | 문서 제목 | 필수 |
| `issuer` | 발행 기관 | 필수 |
| `year` | 발행 연도 | 권장 |
| `source_type` | 문서 유형 | 권장 |
| `source_url` | 원문 URL | 권장 |
| `authors` | 저자 또는 작성 주체 | 선택 |
| `tags_text` | 검색 필터용 태그 문자열 | 필수 |
| `page` | 페이지 번호 | 필수 |

### 권장 추가 필드

현재 구현에는 아직 없지만 팀 합의 기준으로 아래 필드 추가를 권장한다.

- `section`: 문서 내 섹션명
- `topic`: `inspection`, `predictive_maintenance`, `roi`, `deployment` 등

추가 시 backward compatibility 를 위해 기존 필드는 유지한다.

## 인덱싱 기준

현재 구현 기준:

- 임베딩 모델: `BAAI/bge-m3`
- 벡터스토어: `Chroma`
- 저장 위치: `data/chroma/`
- 컬렉션명: `manufacturing_startup_eval`

### 인덱스 재생성 기준

아래 경우에는 인덱스를 재생성한다.

- `manifest.json` 내용이 바뀐 경우
- PDF 파일이 추가/삭제/교체된 경우
- `chunk_size`, `chunk_overlap` 이 바뀐 경우
- 임베딩 모델이 바뀐 경우
- metadata 구조가 바뀐 경우

### 재생성 원칙

- 재생성 시 기존 `data/chroma/` 는 새로 만든다.
- 동일한 문서라도 metadata 구조가 바뀌면 재사용하지 않는다.

## retriever 동작 규칙

### Query Planning

- LLM 이 task 별로 3~4개의 retrieval query 를 만든다.
- 비어 있는 경우 fallback query 를 사용한다.

### Tag Filtering

- `tech_analysis` 는 `["tech", "manufacturing"]` 태그를 우선 사용한다.
- `market_analysis` 는 `["market", "manufacturing"]` 태그를 우선 사용한다.
- 태그 교집합이 없는 chunk 는 제외한다.

### Top-K

- 기본적으로 task 별 `top_k` 설정값을 따른다.
- 기술 분석: `TOP_K_TECH`
- 시장 분석: `TOP_K_MARKET`

## retriever 반환 형식

### 내부 chunk 객체

retriever 는 최소 아래 정보를 가진 chunk 목록을 반환해야 한다.

```json
[
  {
    "content": "제조 현장 AI 도입 시 데이터 정합성이 핵심이다.",
    "metadata": {
      "doc_id": "doc1",
      "title": "Artificial Intelligence Diffusion and Applications in Manufacturing",
      "issuer": "OECD",
      "year": "2021",
      "page": 12,
      "filename": "doc1_oecd_ai_manufacturing.pdf",
      "source_url": "https://example.com/report.pdf",
      "tags_text": "tech,manufacturing"
    }
  }
]
```

### LLM 컨텍스트 포맷

LLM 에 넣는 컨텍스트 블록은 아래 순서를 유지한다.

- `doc_id`
- `title`
- `issuer`
- `year`
- `page`
- `content`

### reference 문자열 포맷

최종 reference 는 사람이 읽을 수 있는 citation 문자열이어야 한다.

권장 포함 요소:

- 발행기관
- 연도
- 문서 제목
- 파일명 또는 URL
- 페이지

## `tech_references` 규칙

- `tech_references` 는 기술 분석에서 사용한 웹 근거와 RAG 근거를 합쳐서 만든다.
- 중복은 제거하되 순서는 최대한 유지한다.
- 기술 배포성, 데이터 요구조건, 현장 통합성에 직접 연결되는 근거를 우선 남긴다.
- 일반적인 AI 개론 문장은 제외한다.

## `market_references` 규칙

- `market_references` 는 시장 분석에서 사용한 웹 근거와 RAG 근거를 합쳐서 만든다.
- 시장 성장, 고객 pain point, ROI, 채택 확산에 직접 연결되는 근거를 우선 남긴다.
- 너무 넓은 범주의 거시경제 설명만 있는 근거는 후순위로 둔다.

## 검색 품질 기준

### 우선 규칙

- 같은 내용을 반복하는 chunk 는 1개만 남긴다.
- 스타트업 분석 문맥과 직접 연결되는 chunk 를 우선한다.
- 수치, 제약, 사례, 구현 조건이 포함된 chunk 를 우선한다.
- 발행기관이 명확한 문서를 우선한다.

### 제외 규칙

아래 chunk 는 제외하거나 낮은 우선순위로 둔다.

- 정의 수준의 너무 일반적인 설명
- 페이지 추출 오류로 문장이 심하게 깨진 텍스트
- 표만 남고 문맥이 사라진 텍스트
- 동일 페이지에서 의미가 거의 같은 중복 chunk
- 스타트업 투자 판단과 직접 연결되지 않는 일반 제조업 동향 문장

## 한계

- PDF 텍스트 추출 품질이 낮을 수 있다.
- 표 데이터는 셀 순서가 깨져 의미가 왜곡될 수 있다.
- 보고서 발행 연도가 오래되면 최신 시장 상황과 다를 수 있다.
- 벡터 검색은 의미 유사도 기반이므로 정확한 숫자 문장을 놓칠 수 있다.
- RAG 문서는 제조업 일반론이 많아 특정 스타트업 직접 정보는 부족할 수 있다.

## 품질 검수 체크리스트

- `manifest.json` 의 문서 제목과 실제 PDF 가 일치하는가
- 태그가 `tech`, `market`, `manufacturing` 의도에 맞게 들어갔는가
- 검색 결과에 중복 chunk 가 과도하게 포함되지 않는가
- reference 문자열만 보고도 출처를 추적할 수 있는가
- `tech_references`, `market_references` 가 분석 내용과 실제로 연결되는가
