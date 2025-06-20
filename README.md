# Document Checker

**Document Checker**는 다양한 형식의 문서를 자동으로 처리하고 분석하는 종합적인 문서 관리 시스템입니다. 실시간 파일 모니터링, 지능형 텍스트 분석, 고급 검색 및 리포팅 기능을 통해 효율적인 문서 관리 환경을 제공합니다.

## ⚡ 빠른 시작

```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd document-checker

# 2. 가상 환경 설정
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 애플리케이션 실행
sh run_servers.sh

# 5. 브라우저에서 접속
# http://localhost:5002
```

**지원 형식**: PDF, DOCX, TXT, DOC | **Python**: 3.8+ | **플랫폼**: Windows, macOS, Linux

## 주요 기능

### 🔍 자동 문서 처리
- **실시간 파일 모니터링**: `input/` 디렉토리에 추가된 문서를 자동으로 감지하고 처리
- **다양한 문서 형식 지원**: PDF, DOCX, TXT, DOC 등 일반적인 문서 형식 처리
- **지능형 콘텐츠 추출**: Docling 라이브러리를 활용한 고품질 텍스트 추출
- **메타데이터 자동 생성**: 파일 정보, 처리 시간, 문서 구조 등 자동 수집

### 🔎 고급 검색 기능
- **패턴 기반 검색**: 정규식, 대소문자 구분, 전체 단어 매칭 등 다양한 검색 옵션
- **수식 인식 및 검색**: 수학 공식과 과학 기호 검색 지원
- **문맥 기반 결과 제공**: 검색 결과에 대한 전후 문맥 정보 제공
- **실시간 검색**: 빠른 인덱싱을 통한 즉시 검색 결과 제공

### 📊 대시보드 및 리포팅
- **문서 상태 대시보드**: 처리 완료, 대기 중, 오류 상태별 통계
- **최근 활동 모니터링**: 최근 업로드된 문서 목록 및 상태 추적
- **HTML/JSON 리포트 생성**: 검색 결과를 다양한 형식으로 저장 및 공유
- **사용자 정의 템플릿**: 보고서 형식 개인화 가능

### 🌐 웹 인터페이스
- **직관적인 파일 업로드**: 드래그 앤 드롭 방식의 파일 업로드
- **실시간 검색 인터페이스**: 검색 옵션과 결과를 실시간으로 확인
- **반응형 디자인**: 다양한 화면 크기에 최적화된 UI

## 시스템 아키텍처

### 핵심 컴포넌트

```text
Document Checker Architecture
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│   Web UI        │  │   REST API       │  │   File Monitor  │
│   (Flask)       │←→│   (Flask)        │  │   (Watchdog)    │
│   Port: 5002    │  │   Port: 5001     │  │                 │
└─────────────────┘  └──────────────────┘  └─────────────────┘
         │                       │                    │
         └───────────────────────┼────────────────────┘
                                 │
         ┌───────────────────────────────────────────────────┐
         │              Core Processing Engine               │
         └───────────────────────────────────────────────────┘
         │                       │                          │
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ DocumentProcessor│  │ ContentAnalyzer  │  │ StorageManager  │
│ (Docling 통합)   │  │ (검색 & 분석)     │  │ (저장 & 인덱싱) │
└─────────────────┘  └──────────────────┘  └─────────────────┘
         │                       │                          │
         └───────────────────────┼──────────────────────────┘
                                 │
         ┌───────────────────────────────────────────────────┐
         │             ReportGenerator                       │
         │         (HTML/JSON 리포트 생성)                   │
         └───────────────────────────────────────────────────┘
```

### 데이터 흐름

1. **문서 입력**: `input/` 디렉토리에 문서 추가
2. **자동 감지**: FileMonitor가 새 파일을 감지
3. **문서 처리**: DocumentProcessor가 Docling을 통해 텍스트 추출
4. **저장 및 인덱싱**: StorageManager가 문서를 저장하고 검색 인덱스 구축
5. **검색 및 분석**: ContentAnalyzer가 사용자 쿼리에 대한 검색 수행
6. **결과 제공**: 웹 인터페이스를 통해 결과 표시 및 리포트 생성

## 🔌 API 참조

### REST API 엔드포인트

#### 문서 관리
```http
POST /api/upload          # 파일 업로드
GET  /api/documents       # 문서 목록 조회
GET  /api/documents/{id}  # 특정 문서 조회
DELETE /api/documents/{id} # 문서 삭제
```

#### 검색 기능
```http
POST /api/search          # 문서 검색 실행
GET  /api/search/history  # 검색 이력 조회
```

#### 리포트 생성
```http
POST /api/reports         # 리포트 생성
GET  /api/reports         # 리포트 목록
GET  /api/reports/{id}    # 특정 리포트 다운로드
```

#### 시스템 정보
```http
GET  /api/status          # 시스템 상태 확인
GET  /api/stats           # 통계 정보 조회
```

### Python API 사용 예제

#### 문서 처리
```python
from src.document_processor.processor import DocumentProcessor

# 문서 처리기 초기화
processor = DocumentProcessor()

# 문서 처리
document = processor.process_document("/path/to/file.pdf")
print(f"추출된 텍스트: {document['content'][:100]}...")
```

#### 검색 실행
```python
from src.content_analyzer.analyzer import ContentAnalyzer

# 검색기 초기화
analyzer = ContentAnalyzer()

# 검색 실행
results = analyzer.execute_search({
    'query': '찾을 텍스트',
    'caseSensitive': False,
    'wholeWord': True,
    'regex': False
})
```

#### 리포트 생성
```python
from src.report_generator.generator import ReportGenerator

# 리포트 생성기 초기화
generator = ReportGenerator(output_dir="./reports")

# HTML 리포트 생성
report = generator.generate_report(
    search_results=results,
    report_format='html'
)
```

## 🚀 빠른 시작 가이드

### 시스템 요구사항

- **Python**: 3.8 이상
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 2GB RAM (대용량 문서 처리 시 4GB 권장)
- **디스크 공간**: 최소 500MB (문서 저장용 추가 공간 필요)

### 1단계: 프로젝트 클론 및 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd document-checker

# 가상 환경 생성
python -m venv .venv

# 가상 환경 활성화
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: 디렉토리 구조 준비

```bash
# 필요한 디렉토리 생성 (자동으로 생성되지 않는 경우)
mkdir -p input output/documents output/reports
```

### 3단계: 애플리케이션 실행

```bash
# 권장: 두 서버 동시 실행
sh run_servers.sh

# 또는 개별 실행
python src/user_interface/app.py &    # API 서버 (백그라운드)
python main.py                        # 메인 애플리케이션
```

### 4단계: 웹 인터페이스 접속

- **메인 애플리케이션**: [http://localhost:5002](http://localhost:5002)
- **API 서버** (개발용): [http://localhost:5001](http://localhost:5001)

## 📖 사용법

### 문서 업로드 및 처리

1. **자동 처리**: `input/` 디렉토리에 문서 파일을 복사하면 자동으로 처리됩니다.
2. **웹 업로드**: 브라우저에서 파일을 드래그 앤 드롭하여 업로드할 수 있습니다.
3. **지원 형식**: PDF, DOCX, TXT, DOC 파일이 지원됩니다.

### 문서 검색

1. **기본 검색**: 검색창에 찾고자 하는 키워드를 입력합니다.
2. **고급 옵션**:
   - **대소문자 구분**: 정확한 대소문자 매칭
   - **전체 단어**: 완전한 단어만 매칭
   - **정규식**: 고급 패턴 매칭
   - **수식 검색**: 수학 공식 및 과학 기호 검색

### 리포트 생성

1. 검색 결과 페이지에서 "리포트 생성" 버튼 클릭
2. HTML 또는 JSON 형식 선택
3. 생성된 리포트는 `output/reports/` 디렉토리에 저장됩니다.

### 대시보드 활용

- **문서 상태**: 전체 문서 처리 현황을 한눈에 확인
- **최근 활동**: 최근 업로드된 문서들의 상태 모니터링
- **통계 정보**: 문서 형식별, 상태별 통계 확인

## 🔧 개발 및 테스트

### 테스트 실행

```bash
# 전체 테스트 실행
python -m unittest discover -s tests -v

# 개별 컴포넌트 테스트
python -m unittest tests.test_content_analyzer
python -m unittest tests.test_document_processor
python -m unittest tests.test_storage_manager
python -m unittest tests.test_report_generator

# 통합 테스트
python -m unittest tests.test_docling_integration
```

### 개발 환경 설정

```bash
# 개발용 의존성 설치 (필요시)
pip install -r requirements-dev.txt

# 코드 품질 검사
flake8 src/
black src/

# 의존성 업데이트
pip freeze > requirements.txt
```

## 🛠️ 문제 해결

### 일반적인 문제

#### 포트 충돌 오류
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :5001
lsof -i :5002

# 프로세스 종료
kill -9 <PID>
```

#### 의존성 충돌
```bash
# 가상 환경 재생성
deactivate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

#### 문서 처리 오류
- `output/` 디렉토리 권한 확인
- Docling 라이브러리 설치 확인
- 로그 파일 확인 (`logs/` 디렉토리)

### 성능 최적화

#### 대용량 문서 처리
- 시스템 메모리 4GB 이상 권장
- 문서 크기 제한: 50MB 이하 권장
- 배치 처리 크기 조정 가능

#### 검색 성능 향상
- 문서 인덱스 정기적 재구축
- 검색 캐시 활용
- 정규식 최적화

## 📝 라이센스 및 기여

### 라이센스
이 프로젝트는 MIT 라이센스 하에 배포됩니다.

### 기여 방법
1. 이슈 등록 및 버그 리포트
2. 기능 제안 및 개선 아이디어
3. 코드 기여 및 풀 리퀘스트
4. 문서 개선 및 번역

### 연락처
- 프로젝트 관리자: [이메일 주소]
- 이슈 추적: GitHub Issues
- 토론: GitHub Discussions

---

## 📋 개발 로그

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