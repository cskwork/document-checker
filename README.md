# document-checker

## 프로젝트 개요

문서 처리 및 관리 시스템으로, 문서의 자동 수집, 처리, 저장, 검색 기능을 제공합니다.

## 주요 기능

- 문서 자동 수집 (파일 시스템 모니터링)
- 문서 처리 파이프라인: 다양한 문서 형식(PDF, DOCX, TXT, DOC)을 지원하며, 처리 중 발생하는 오류를 효과적으로 관리합니다.
- 문서 저장 및 인덱싱
- 빠른 검색 및 필터링:
  - 사용자가 지정한 패턴과 옵션에 따라 문서를 검색하고, 결과를 효율적으로 제공합니다.
  - 검색 실행 시, 백엔드(`app.py`)는 `ContentAnalyzer`를 통해 검색을 수행하고, `StorageManager`에서 각 문서의 상세 메타데이터를 조회합니다.
  - 조회된 결과는 프론트엔드 (`search.html`)가 효과적으로 표시할 수 있도록 문서별로 그룹화되고 필요한 모든 정보(파일명, 날짜, 개별 일치 항목의 상세 내용 등)를 포함하는 배열 형태로 가공되어 전달됩니다.
- 대시보드 기능 강화:
  - 문서 처리 상태별 통계 (처리 완료, 처리 중/대기, 오류) 제공
  - 최근 업로드된 문서 목록 표시 (문서명, 상태, 업로드 시간)

## 프로젝트 구조

```text
document-checker/
├── src/                                # 소스 코드
│   ├── content_analyzer/              # 콘텐츠 분석 모듈
│   │   ├── __init__.py
│   │   ├── analyzer.py                # ContentAnalyzer 구현체
│   │   └── formula_analyzer.py        # FormulaAnalyzer 구현체
│   ├── document_processor/            # 문서 처리 모듈
│   │   ├── __init__.py
│   │   └── processor.py               # DocumentProcessor 구현체
│   ├── report_generator/              # 리포트 생성 모듈
│   │   ├── __init__.py
│   │   ├── generator.py               # ReportGenerator 구현체
│   │   └── templates/                 # 리포트 템플릿
│   │       └── report.html            # HTML 보고서 템플릿
│   ├── storage_manager/               # 저장소 관리 모듈
│   │   ├── __init__.py
│   │   ├── manager.py                 # StorageManager 구현체
│   │   └── batch_processor.py         # BatchProcessor 구현체
│   └── user_interface/                # 사용자 인터페이스 모듈
│       ├── __init__.py
│       ├── app.py                     # Flask 애플리케이션
│       ├── static/                    # 정적 파일
│       │   ├── css/                   # CSS 파일
│       │   ├── js/                    # JavaScript 파일
│       │   └── images/                # 이미지 파일
│       └── templates/                 # HTML 템플릿
├── tests/                             # 테스트 코드
│   ├── test_content_analyzer.py       # ContentAnalyzer 테스트
│   ├── test_formula_analyzer.py       # FormulaAnalyzer 테스트
│   ├── test_document_processor.py     # DocumentProcessor 테스트
│   ├── test_report_generator.py       # ReportGenerator 테스트
│   ├── test_storage_manager.py        # StorageManager 테스트
│   ├── test_batch_processor.py        # BatchProcessor 테스트
│   ├── test_docling_integration.py    # Docling 통합 테스트
│   ├── mocks/                         # 목 객체
│   │   └── docling.py                 # Docling 목 구현
│   └── test_data/                     # 테스트용 데이터
│       ├── input/                     # 테스트 입력 데이터
│       └── output/                    # 테스트 출력 데이터
├── input/                             # 입력 문서 디렉토리
├── output/                            # 출력 문서 디렉토리
├── docs/                              # 문서화 파일
├── scripts/                           # 유틸리티 스크립트
├── main.py                            # 애플리케이션 진입점
├── requirements.txt                   # 의존성 패키지 목록
└── README.md                          # 프로젝트 문서
```

## ReportGenerator 사용법

### 초기화

```python
from src.report_generator.generator import ReportGenerator
from src.storage_manager.manager import StorageManager

# 저장소 관리자 초기화 (예시)
storage = StorageManager(input_dir="./input", output_dir="./output")

# ReportGenerator 초기화
report_generator = ReportGenerator(
    output_dir="./reports",  # 보고서 출력 디렉토리
    storage_manager=storage
)
```

### HTML 보고서 생성

```python
# 검색 결과 예시
search_results = {
    'id': 'search_123',
    'query': '테스트 쿼리',
    'matchCount': 2,
    'matches': [
        {
            'documentId': 'doc1',
            'fieldName': 'content',
            'matchedText': '테스트 텍스트',
            'score': 0.95,
            'context': '이것은 테스트 텍스트 예시입니다.'
        },
        # ... 더 많은 매칭 결과
    ]
}

# HTML 보고서 생성
report_metadata = report_generator.generate_report(
    search_results=search_results,
    report_format='html'  # 'html' 또는 'json' 지정 가능
)

print(f"생성된 보고서: {report_metadata['path']}")
```

### JSON 보고서 생성

```python
# JSON 보고서 생성
report_metadata = report_generator.generate_report(
    search_results=search_results,
    report_format='json'
)

print(f"생성된 JSON 보고서: {report_metadata['path']}")
```

### 사용자 정의 템플릿

1. `src/report_generator/templates/` 디렉토리에 `report.html` 파일을 생성하여 HTML 템플릿을 사용자 정의할 수 있습니다.
2. Jinja2 템플릿 엔진을 사용합니다.
3. 기본 템플릿이 제공되며, 파일이 없을 경우 자동으로 생성됩니다.

## StorageManager 사용법

### 초기화

```python
from src.storage_manager.manager import StorageManager
from document_processor.processor import DocumentProcessor

# 문서 처리기 초기화 (예시)
processor = DocumentProcessor()

# StorageManager 초기화
storage = StorageManager(
    input_dir="./input",     # 입력 디렉토리
    output_dir="./output",   # 출력 디렉토리
    document_processor=processor
)
```

### 문서 모니터링 시작/중지

```python
# 모니터링 시작
storage.start_monitoring()

# 모니터링 중지
storage.stop_monitoring()
```

### 문서 처리 및 저장

```python
# 새 문서 처리
file_path = "/path/to/document.pdf"
doc_id = storage.process_new_document(file_path)

# 문서 저장
doc = {
    'id': 'doc_123',
    'filename': 'example.pdf',
    'format': 'pdf',
    'content': '문서 내용',
    'createdAt': 1620000000
}
storage.store_document(doc)
```

### 문서 조회

```python
# 단일 문서 조회
document = storage.get_document('doc_123')

# 문서 목록 조회 (필터링 가능)
documents = storage.list_documents({
    'format': 'pdf',
    'days': 7  # 최근 7일 이내 문서
})
```

## 설치 및 실행

### 요구사항

- Python 3.8+
- 필요한 패키지는 requirements.txt에 명시되어 있습니다.

### 가상 환경 설정 및 활성화

```bash
# 가상 환경 생성 (프로젝트 루트 디렉토리에서 실행)
python -m venv .venv

# 가상 환경 활성화 (macOS/Linux)
source .venv/bin/activate

# 가상 환경 활성화 (Windows)
.venv\Scripts\activate

# 가상 환경이 활성화되면 프롬프트 앞에 (.venv)가 표시됩니다.
```

### 의존성 설치

```bash
# 가상 환경이 활성화된 상태에서 실행
pip install -r requirements.txt
```

### 가상 환경 비활성화

작업이 끝난 후 가상 환경을 비활성화하려면 다음 명령어를 실행하세요:

```bash
deactivate
```

### 의존성 업데이트

새로운 패키지를 설치한 경우 requirements.txt를 업데이트하려면:

```bash
pip freeze > requirements.txt
```

### 디버깅

#### `ImportError: cannot import name 'url_quote' from 'werkzeug.urls'`

- **문제 발생**: `python main.py` 실행 시 Werkzeug 라이브러리에서 `url_quote`를 가져올 수 없는 오류 발생.
- **원인**: Flask와 Werkzeug 라이브러리 간의 버전 호환성 문제로 추정.
- **해결 완료**: Flask (`2.0.1` -> `3.1.1`), Jinja2 (`3.0.1` -> `3.1.6`) 업그레이드를 통해 `ImportError` 해결.

#### `Address already in use` (Port 5000)

- **문제 발생**: Flask 업그레이드 후 `main.py` 실행 시 5000번 포트가 이미 사용 중이라는 오류 발생.
- **원인**: 다른 프로세스가 5000번 포트를 이미 점유하고 있음.
- **해결 방안**:
    1. Flask 애플리케이션이 다른 포트(5001)를 사용하도록 `src/user_interface/app.py` 파일의 `app.run()` 부분을 수정했으나, `main.py` 파일 내에서 `app.run(port=5000)`으로 포트가 하드코딩되어 있어 문제가 지속됨. `main.py` 파일의 해당 부분을 `port=5001`로 수정함.
    2. 5000번 포트를 사용 중인 프로세스를 찾아 종료.

### 실행

두 개의 서버(API 서버와 메인 애플리케이션)를 동시에 실행하려면 프로젝트 루트 디렉토리에서 다음 스크립트를 사용하세요:

```bash
# API 서버와 메인 애플리케이션 동시 실행
sh run_servers.sh
```

스크립트를 실행하면 다음 두 애플리케이션이 시작됩니다:

- **API 서버**: `src/user_interface/app.py` (포트: 5001)
- **메인 애플리케이션**: `main.py` (포트: 5002)

애플리케이션 접속:

- API 서버 UI (필요시): [http://localhost:5001](http://localhost:5001)
- 메인 애플리케이션 UI: [http://localhost:5002](http://localhost:5002)

개별적으로 실행하려면 다음 명령어를 사용하십시오:

```bash
# API 서버 실행 (src/user_interface/app.py)
python src/user_interface/app.py

# 메인 애플리케이션 실행 (main.py)
python main.py
```

## 테스트 실행

```bash
# 단위 테스트 실행
python -m unittest discover -s tests
```

## 업데이트 로그

### 2025-05-20

- 대시보드 기능 개선:
  - `ReportGenerator.get_document_statistics` 메소드 수정하여 처리 상태별(처리 완료, 대기 중, 오류) 문서 수 통계 추가
  - 최근 5개 문서 (ID, 파일명, 상태, 업로드 시간) 목록 기능 추가
  - 관련 로깅 기능 (`logging` 모듈) 추가 및 임포트 확인

### 2025-05-19

- ReportGenerator 구현 완료
  - HTML 및 JSON 형식의 보고서 생성
  - 사용자 정의 가능한 템플릿 시스템
  - 문서 메타데이터 통합
  - 단위 테스트 포함

### 2025-05-18

- 검색 기능 개선:
  - 백엔드에서 검색 결과를 문서별로 그룹화하고 프론트엔드 요구사항에 맞게 데이터 구조를 재가공하여 전달하도록 수정 (`app.py`).
  - `ContentAnalyzer`의 `execute_search`는 모든 일치 항목의 통합 리스트를, `_search_document`는 프론트엔드 표시에 필요한 상세 필드(text, context_before, context_after 등)를 포함한 개별 일치(match) 객체를 생성하도록 수정.
  - `StorageManager`에 문서 ID로 메타데이터를 조회하는 `get_document_metadata` 메소드 추가.
  - 이 변경으로 프론트엔드에서 발생하던 `results.forEach is not a function` JavaScript 오류 해결.

- 고급 수식 인식 기능 구현
  - 수식 인식 및 추출
  - 수식 정규화
  - 수식 변수 추출
  - 수식 유형 분류
  - 수식 검색 및 매칭
  - docling 모듈 통합 준비

- StorageManager 구현 완료
  - 파일 시스템 모니터링
  - 문서 저장 및 인덱싱
  - 캐싱 메커니즘
  - 문서 검색 및 필터링

### 2025-05-17

- 프로젝트 초기화
- Task Master 통합
- 기본 프로젝트 구조 설정 