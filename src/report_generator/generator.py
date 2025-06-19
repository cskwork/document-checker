"""
리포트 생성 모듈

검색 결과를 바탕으로 다양한 형식의 보고서를 생성하는 기능을 제공합니다.
"""
import os
import json
import datetime
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader
from collections import Counter # 통계 생성을 위해 Counter 추가
import logging # 로깅 사용을 위해 추가

class ReportGenerator:
    """
    검색 결과를 다양한 형식의 보고서로 변환하는 클래스
    
    속성:
        output_dir (str): 보고서가 저장될 디렉토리 경로
        storage_manager: 저장소 관리자 인스턴스
        reports_dir (str): 보고서가 저장될 전체 경로
        jinja_env: Jinja2 템플릿 환경
    """
    
    def __init__(self, output_dir: str, storage_manager: Any):
        """
        ReportGenerator 초기화
        
        Args:
            output_dir (str): 출력 디렉토리 경로
            storage_manager: 저장소 관리자 인스턴스
        """
        self.output_dir = output_dir
        self.storage_manager = storage_manager
        self.reports_dir = os.path.join(output_dir, 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Jinja2 템플릿 환경 설정
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        os.makedirs(template_dir, exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    def generate_report(self, search_results: Dict[str, Any], report_format: str = 'html') -> Dict[str, Any]:
        """
        검색 결과를 바탕으로 보고서 생성
        
        Args:
            search_results (dict): 검색 결과 딕셔너리
            report_format (str): 보고서 형식 ('html' 또는 'json')
            
        Returns:
            dict: 생성된 보고서의 메타데이터
            
        Raises:
            ValueError: 지원하지 않는 형식일 경우
        """
        report_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 보고서 메타데이터 생성
        report_metadata = {
            'id': report_id,
            'resultsId': search_results.get('id', ''),
            'format': report_format,
            'generatedAt': datetime.datetime.now().isoformat(),
            'matchCount': search_results.get('matchCount', 0)
        }
        
        # 형식에 따른 보고서 생성
        if report_format == 'html':
            report_path = self._generate_html_report(search_results, report_id, timestamp)
        elif report_format == 'json':
            report_path = self._generate_json_report(search_results, report_id, timestamp)
        else:
            raise ValueError(f"지원하지 않는 보고서 형식: {report_format}")
        
        # 보고서 메타데이터에 경로 추가
        report_metadata['path'] = report_path
        
        # 보고서 메타데이터 저장
        metadata_path = os.path.join(self.reports_dir, f"{report_id}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(report_metadata, f, ensure_ascii=False, indent=2)
        
        # 검색 결과에 보고서 URL 추가
        search_results['reportUrl'] = report_path
        
        return report_metadata
    
    def _generate_html_report(self, search_results: Dict[str, Any], report_id: str, timestamp: str) -> str:
        """
        HTML 형식의 보고서 생성
        
        Args:
            search_results (dict): 검색 결과
            report_id (str): 보고서 ID
            timestamp (str): 타임스탬프
            
        Returns:
            str: 생성된 보고서 파일 경로
        """
        # HTML 템플릿이 없으면 기본 템플릿 생성
        self._ensure_default_template()
        
        # 템플릿 로드
        template = self.jinja_env.get_template('report.html')
        
        # 템플릿에 전달할 데이터 준비
        template_data = {
            'report_id': report_id,
            'generated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'results': search_results,
            'documents': self._get_documents_for_results(search_results)
        }
        
        # 템플릿 렌더링
        html_content = template.render(**template_data)
        
        # 파일로 저장
        report_filename = f"report_{timestamp}.html"
        report_path = os.path.join(self.reports_dir, report_filename)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    def _generate_json_report(self, search_results: Dict[str, Any], report_id: str, timestamp: str) -> str:
        """
        JSON 형식의 보고서 생성
        
        Args:
            search_results (dict): 검색 결과
            report_id (str): 보고서 ID
            timestamp (str): 타임스탬프
            
        Returns:
            str: 생성된 보고서 파일 경로
        """
        # 보고서 데이터 준비
        report_data = {
            'report_id': report_id,
            'generated_at': datetime.datetime.now().isoformat(),
            'results': search_results,
            'documents': self._get_documents_for_results(search_results, include_content=False)
        }
        
        # 파일로 저장
        report_filename = f"report_{timestamp}.json"
        report_path = os.path.join(self.reports_dir, report_filename)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return report_path
    
    def _get_documents_for_results(self, search_results: Dict[str, Any], include_content: bool = True) -> List[Dict[str, Any]]:
        """
        검색 결과에 해당하는 문서 목록 조회
        
        Args:
            search_results (dict): 검색 결과
            include_content (bool): 문서 내용 포함 여부
            
        Returns:
            list: 문서 목록
        """
        documents = []
        
        # 검색 결과에서 문서 ID 목록 추출
        doc_ids = set()
        for match in search_results.get('matches', []):
            doc_id = match.get('documentId')
            if doc_id:
                doc_ids.add(doc_id)
        
        # 저장소에서 문서 조회
        for doc_id in doc_ids:
            try:
                doc = self.storage_manager.get_document(doc_id)
                if doc:
                    if not include_content and 'content' in doc:
                        doc = doc.copy()
                        doc.pop('content', None)
                    documents.append(doc)
            except Exception as e:
                print(f"문서 조회 중 오류 발생 (ID: {doc_id}): {str(e)}")
        
        return documents
    
    def _ensure_default_template(self) -> None:
        """기본 HTML 템플릿이 없으면 생성"""
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        os.makedirs(template_dir, exist_ok=True)
        
        template_path = os.path.join(template_dir, 'report.html')
        if not os.path.exists(template_path):
            self._create_default_template(template_path)
    
    def _create_default_template(self, template_path: str) -> None:
        """기본 HTML 템플릿 생성
        
        Args:
            template_path (str): 템플릿 파일 경로
        """
        template_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>검색 결과 보고서 - {{ report_id }}</title>
    <style>
        body {
            font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .report-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .summary {
            font-size: 1.1em;
            margin-bottom: 20px;
        }
        .match {
            background-color: #fffde7;
            border-left: 4px solid #ffd600;
            padding: 10px 15px;
            margin-bottom: 15px;
            border-radius: 0 4px 4px 0;
        }
        .document {
            margin-top: 30px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        .document h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .metadata {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        .highlight {
            background-color: #fff59d;
            padding: 0 2px;
            border-radius: 2px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>문서 검색 결과 보고서</h1>
    </div>
    
    <div class="report-info">
        <p><strong>보고서 ID:</strong> {{ report_id }}</p>
        <p><strong>생성 일시:</strong> {{ generated_at }}</p>
        <p><strong>총 일치 항목:</strong> {{ results.matchCount }}건</p>
    </div>
    
    <div class="summary">
        <h2>검색 결과 요약</h2>
        <p>총 {{ results.documents|length }}개의 문서에서 {{ results.matchCount }}건의 일치 항목을 찾았습니다.</p>
    </div>
    
    <div class="matches">
        <h2>일치 항목 상세</h2>
        {% for match in results.matches %}
        <div class="match">
            <p><strong>문서 ID:</strong> {{ match.documentId }}</p>
            <p><strong>일치한 필드:</strong> {{ match.fieldName }}</p>
            <p><strong>일치한 텍스트:</strong> {{ match.matchedText|safe }}</p>
            <p><strong>점수:</strong> {{ "%.2f"|format(match.score * 100) }}%</p>
            {% if match.context %}
            <p><strong>주변 맥락:</strong> {{ match.context|safe }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    
    <div class="documents">
        <h2>문서 정보</h2>
        {% for doc in documents %}
        <div class="document">
            <h3>문서 #{{ loop.index }}: {{ doc.title or '제목 없음' }}</h3>
            <div class="metadata">
                <p><strong>문서 ID:</strong> {{ doc.id }}</p>
                <p><strong>파일명:</strong> {{ doc.filename or '알 수 없음' }}</p>
                <p><strong>파일 형식:</strong> {{ doc.fileType or '알 수 없음' }}</p>
                <p><strong>생성 일시:</strong> {{ doc.createdAt or '알 수 없음' }}</p>
                <p><strong>수정 일시:</strong> {{ doc.updatedAt or '알 수 없음' }}</p>
            </div>
            {% if doc.content %}
            <div class="content">
                <h4>내용 요약</h4>
                <p>{{ doc.content|truncate(500) }}</p>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    
    <footer style="margin-top: 40px; text-align: center; color: #666; font-size: 0.9em;">
        <p>이 보고서는 Document Checker에 의해 자동 생성되었습니다. - {{ generated_at }}</p>
    </footer>
</body>
</html>
"""
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

    def get_document_statistics(self) -> Dict[str, Any]:
        """
        시스템에 저장된 문서에 대한 통계를 생성합니다.

        Returns:
            Dict[str, Any]: 문서 통계 정보.
                            포함 정보: totalDocuments, documentTypes, processed, pending, error, recentDocuments
        """
        logger = logging.getLogger(__name__) # 로거 가져오기
        all_documents_metadata = []
        
        if hasattr(self.storage_manager, 'document_index') and isinstance(self.storage_manager.document_index, dict):
            all_documents_metadata = list(self.storage_manager.document_index.values())
        else:
            logger.warning("StorageManager에서 document_index를 찾을 수 없거나 형식이 올바르지 않습니다. 통계가 정확하지 않을 수 있습니다.")

        total_documents = len(all_documents_metadata)
        
        type_counts = Counter()
        status_counts = Counter()
        
        for doc_meta in all_documents_metadata:
            file_type = doc_meta.get('format', 'unknown')
            type_counts[file_type.lower()] += 1
            
            status = doc_meta.get('status', 'unknown').lower()
            if status == 'processed':
                status_counts['processed'] += 1
            elif status in ['pending', 'processing']: # 'pending'과 'processing'을 합쳐서 'pending'으로 간주
                status_counts['pending'] += 1
            elif status == 'error':
                status_counts['error'] += 1
            else:
                status_counts['unknown_status'] +=1


        # 최근 문서를 위해 createdAt 기준으로 정렬 (내림차순)
        # createdAt 필드가 타임스탬프(숫자) 또는 ISO 형식 문자열일 수 있으므로, 적절히 처리해야 합니다.
        # 여기서는 float으로 변환 가능한 숫자형 타임스탬프라고 가정합니다.
        # 만약 ISO 문자열이라면 datetime.fromisoformat을 사용해야 합니다.
        try:
            sorted_documents = sorted(
                all_documents_metadata,
                # storage_manager에서 createdAt은 float 타임스탬프로 저장됨
                key=lambda x: float(x.get('createdAt', 0)), 
                reverse=True
            )
        except (TypeError, ValueError) as e:
            logger.error(f"최근 문서 정렬 중 createdAt 필드 처리 오류: {e}. 'createdAt' 필드가 숫자 타임스탬프인지 확인하세요.")
            sorted_documents = all_documents_metadata # 정렬 실패 시 원본 사용


        recent_documents_list = []
        for doc_meta in sorted_documents[:5]: # 최근 5개 문서
            recent_documents_list.append({
                'id': doc_meta.get('id'),
                'filename': doc_meta.get('filename', 'N/A'),
                'status': doc_meta.get('status', 'unknown'),
                'uploaded_at': doc_meta.get('createdAt') # HTML에서는 uploaded_at으로 사용
            })
            
        return {
            'totalDocuments': total_documents,
            'documentTypes': dict(type_counts),
            'processed': status_counts['processed'],
            'pending': status_counts['pending'], # 'pending'과 'processing' 상태를 합산
            'error': status_counts['error'],
            'recentDocuments': recent_documents_list
        }
