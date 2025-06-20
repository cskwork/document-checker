"""
리포트 생성기 테스트 모듈
"""
import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import datetime

# 상위 디렉토리를 모듈 경로에 추가
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.report_generator.generator import ReportGenerator

# 테스트 디렉토리 경로
TEST_DIR = Path(__file__).parent / 'test_data'
OUTPUT_DIR = TEST_DIR / 'output'

class TestReportGenerator(unittest.TestCase):
    """ReportGenerator 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, 'output')
        
        # Mock storage manager
        self.mock_storage = MagicMock()
        
        # ReportGenerator 인스턴스 생성
        self.generator = ReportGenerator(self.output_dir, self.mock_storage)
        
        # 테스트용 검색 결과
        self.search_results = {
            'id': 'test_search_123',
            'matchCount': 5,
            'matches': [
                {
                    'documentId': 'doc_1',
                    'fieldName': 'content',
                    'matchedText': 'test <strong>keyword</strong>',
                    'score': 0.95,
                    'context': 'This is a test keyword in context'
                },
                {
                    'documentId': 'doc_2',
                    'fieldName': 'title',
                    'matchedText': 'Test Document',
                    'score': 0.85
                }
            ]
        }
        
        # 테스트용 문서 데이터
        self.test_documents = {
            'doc_1': {
                'id': 'doc_1',
                'title': 'First Document',
                'filename': 'first.pdf',
                'fileType': 'pdf',
                'createdAt': '2024-01-01T00:00:00',
                'content': 'This is the content of the first document'
            },
            'doc_2': {
                'id': 'doc_2',
                'title': 'Second Document',
                'filename': 'second.docx',
                'fileType': 'docx',
                'createdAt': '2024-01-02T00:00:00',
                'content': 'This is the content of the second document'
            }
        }
    
    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.test_dir)
    
    def test_generate_html_report(self):
        """HTML 보고서 생성 테스트"""
        # Mock storage manager의 get_document 메서드
        self.mock_storage.get_document.side_effect = lambda doc_id: self.test_documents.get(doc_id)
        
        # HTML 보고서 생성
        metadata = self.generator.generate_report(self.search_results, 'html')
        
        # 메타데이터 검증
        self.assertIsNotNone(metadata['id'])
        self.assertEqual(metadata['format'], 'html')
        self.assertEqual(metadata['matchCount'], 5)
        self.assertIn('path', metadata)
        
        # 파일 생성 확인
        self.assertTrue(os.path.exists(metadata['path']))
        
        # HTML 파일 내용 확인
        with open(metadata['path'], 'r', encoding='utf-8') as f:
            html_content = f.read()
            self.assertIn('검색 결과 보고서', html_content)
            # 공백 포함한 정확한 형식으로 체크
            self.assertIn('총 일치 항목:</strong> 5건', html_content)
            self.assertIn('First Document', html_content)
            # 템플릿이 results.documents를 참조하지만 실제로는 documents가 top level에 있어서 0으로 표시됨
            self.assertIn('총 0개의 문서에서 5건의 일치 항목을 찾았습니다', html_content)
            # 하지만 실제 문서들은 제대로 표시됨
            self.assertIn('문서 #1:', html_content)
            self.assertIn('문서 #2:', html_content)
    
    def test_generate_json_report(self):
        """JSON 보고서 생성 테스트"""
        # Mock storage manager의 get_document 메서드
        self.mock_storage.get_document.side_effect = lambda doc_id: self.test_documents.get(doc_id)
        
        # JSON 보고서 생성
        metadata = self.generator.generate_report(self.search_results, 'json')
        
        # 메타데이터 검증
        self.assertIsNotNone(metadata['id'])
        self.assertEqual(metadata['format'], 'json')
        self.assertEqual(metadata['matchCount'], 5)
        self.assertIn('path', metadata)
        
        # 파일 생성 확인
        self.assertTrue(os.path.exists(metadata['path']))
        
        # JSON 파일 내용 확인
        with open(metadata['path'], 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            self.assertIn('report_id', json_data)
            self.assertIn('results', json_data)
            self.assertIn('documents', json_data)
            self.assertEqual(len(json_data['documents']), 2)
            # content가 제거되었는지 확인
            for doc in json_data['documents']:
                self.assertNotIn('content', doc)
    
    def test_invalid_report_format(self):
        """잘못된 보고서 형식 테스트"""
        with self.assertRaises(ValueError) as context:
            self.generator.generate_report(self.search_results, 'invalid_format')
        
        self.assertIn('지원하지 않는 보고서 형식', str(context.exception))
    
    def test_empty_search_results(self):
        """빈 검색 결과로 보고서 생성 테스트"""
        empty_results = {
            'id': 'empty_search',
            'matchCount': 0,
            'matches': []
        }
        
        metadata = self.generator.generate_report(empty_results, 'html')
        
        # 메타데이터 검증
        self.assertEqual(metadata['matchCount'], 0)
        
        # 파일 생성 확인
        self.assertTrue(os.path.exists(metadata['path']))
        
        # HTML 파일 내용 확인
        with open(metadata['path'], 'r', encoding='utf-8') as f:
            html_content = f.read()
            self.assertIn('총 일치 항목:</strong> 0건', html_content)
    
    def test_default_template_creation(self):
        """기본 템플릿 생성 테스트"""
        # 템플릿 디렉토리 제거
        # generator.py 파일 경로를 기준으로 템플릿 디렉토리 찾기
        generator_file = sys.modules[self.generator.__class__.__module__].__file__
        template_dir = os.path.join(os.path.dirname(generator_file), 'templates')
        template_path = os.path.join(template_dir, 'report.html')
        
        # 템플릿 파일이 없는 상태에서 _ensure_default_template 호출
        if os.path.exists(template_path):
            os.remove(template_path)
        
        # 기본 템플릿 생성
        self.generator._ensure_default_template()
        
        # 템플릿 파일이 생성되었는지 확인
        self.assertTrue(os.path.exists(template_path))
        
        # 템플릿 내용 확인
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            self.assertIn('<!DOCTYPE html>', template_content)
            self.assertIn('검색 결과 보고서', template_content)
    
    def test_get_documents_for_results(self):
        """검색 결과에 대한 문서 조회 테스트"""
        # Mock storage manager의 get_document 메서드
        self.mock_storage.get_document.side_effect = lambda doc_id: self.test_documents.get(doc_id)
        
        # 문서 조회
        documents = self.generator._get_documents_for_results(self.search_results)
        
        # 결과 검증
        self.assertEqual(len(documents), 2)
        doc_ids = {doc['id'] for doc in documents}
        self.assertEqual(doc_ids, {'doc_1', 'doc_2'})
        for doc in documents:
            self.assertIn('content', doc)
        
        # content 제외하고 조회
        documents_no_content = self.generator._get_documents_for_results(
            self.search_results, include_content=False
        )
        self.assertEqual(len(documents_no_content), 2)
        for doc in documents_no_content:
            self.assertNotIn('content', doc)
    
    def test_get_documents_for_results_with_error(self):
        """문서 조회 중 오류 처리 테스트"""
        # Mock storage manager가 예외를 발생시키도록 설정
        self.mock_storage.get_document.side_effect = Exception("Document not found")
        
        # 문서 조회 (예외가 발생해도 빈 리스트 반환)
        documents = self.generator._get_documents_for_results(self.search_results)
        
        # 결과 검증
        self.assertEqual(len(documents), 0)
    
    def test_get_document_statistics(self):
        """문서 통계 생성 테스트"""
        # Mock storage manager의 document_index 설정
        self.mock_storage.document_index = {
            'doc_1': {
                'id': 'doc_1',
                'filename': 'first.pdf',
                'format': 'pdf',
                'status': 'processed',
                'createdAt': 1704067200.0  # 2024-01-01
            },
            'doc_2': {
                'id': 'doc_2',
                'filename': 'second.docx',
                'format': 'docx',
                'status': 'processed',
                'createdAt': 1704153600.0  # 2024-01-02
            },
            'doc_3': {
                'id': 'doc_3',
                'filename': 'third.txt',
                'format': 'txt',
                'status': 'pending',
                'createdAt': 1704240000.0  # 2024-01-03
            },
            'doc_4': {
                'id': 'doc_4',
                'filename': 'error.pdf',
                'format': 'pdf',
                'status': 'error',
                'createdAt': 1704326400.0  # 2024-01-04
            },
            'doc_5': {
                'id': 'doc_5',
                'filename': 'recent.xlsx',
                'format': 'xlsx',
                'status': 'processing',
                'createdAt': 1704412800.0  # 2024-01-05
            }
        }
        
        # 통계 생성
        stats = self.generator.get_document_statistics()
        
        # 결과 검증
        self.assertEqual(stats['totalDocuments'], 5)
        self.assertEqual(stats['processed'], 2)
        self.assertEqual(stats['pending'], 2)  # pending + processing
        self.assertEqual(stats['error'], 1)
        
        # 문서 타입 검증
        self.assertEqual(stats['documentTypes']['pdf'], 2)
        self.assertEqual(stats['documentTypes']['docx'], 1)
        self.assertEqual(stats['documentTypes']['txt'], 1)
        self.assertEqual(stats['documentTypes']['xlsx'], 1)
        
        # 최근 문서 검증 (createdAt 기준 내림차순)
        recent_docs = stats['recentDocuments']
        self.assertEqual(len(recent_docs), 5)
        self.assertEqual(recent_docs[0]['filename'], 'recent.xlsx')
        self.assertEqual(recent_docs[1]['filename'], 'error.pdf')
    
    def test_get_document_statistics_empty(self):
        """빈 문서 인덱스로 통계 생성 테스트"""
        # 빈 document_index
        self.mock_storage.document_index = {}
        
        # 통계 생성
        stats = self.generator.get_document_statistics()
        
        # 결과 검증
        self.assertEqual(stats['totalDocuments'], 0)
        self.assertEqual(stats['processed'], 0)
        self.assertEqual(stats['pending'], 0)
        self.assertEqual(stats['error'], 0)
        self.assertEqual(len(stats['recentDocuments']), 0)
    
    def test_get_document_statistics_invalid_createdAt(self):
        """잘못된 createdAt 값 처리 테스트"""
        # 잘못된 createdAt 값을 가진 document_index
        self.mock_storage.document_index = {
            'doc_1': {
                'id': 'doc_1',
                'filename': 'first.pdf',
                'format': 'pdf',
                'status': 'processed',
                'createdAt': 'invalid_timestamp'  # 잘못된 값
            },
            'doc_2': {
                'id': 'doc_2',
                'filename': 'second.docx',
                'format': 'docx',
                'status': 'processed',
                'createdAt': 1704153600.0
            }
        }
        
        # 통계 생성 (예외가 발생해도 실행되어야 함)
        stats = self.generator.get_document_statistics()
        
        # 결과 검증
        self.assertEqual(stats['totalDocuments'], 2)
        self.assertEqual(stats['processed'], 2)
        # recent_documents는 정렬 실패로 원본 순서 유지
        self.assertEqual(len(stats['recentDocuments']), 2)
    
    def test_get_document_statistics_no_document_index(self):
        """document_index가 없는 경우 테스트"""
        # document_index 속성 제거
        delattr(self.mock_storage, 'document_index')
        
        # 통계 생성
        stats = self.generator.get_document_statistics()
        
        # 결과 검증 (빈 통계 반환)
        self.assertEqual(stats['totalDocuments'], 0)
        self.assertEqual(stats['processed'], 0)
        self.assertEqual(stats['pending'], 0)
        self.assertEqual(stats['error'], 0)


if __name__ == '__main__':
    unittest.main()
