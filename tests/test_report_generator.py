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

# 상위 디렉토리를 모듈 경로에 추가
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.report_generator.generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):
    """ReportGenerator 클래스 테스트"""
    
    def setUp(self):
        """테스트 전 설정"""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        
        # 모의 저장소 관리자 생성
        self.mock_storage = MagicMock()
        self.mock_storage.get_document.side_effect = self._mock_get_document
        
        # 테스트용 검색 결과 데이터
        self.test_results = {
            'id': 'test_search_123',
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
                {
                    'documentId': 'doc2',
                    'fieldName': 'title',
                    'matchedText': '제목 테스트',
                    'score': 0.85,
                    'context': '테스트 제목이 포함된 문서입니다.'
                }
            ]
        }
        
        # 테스트용 문서 데이터
        self.test_documents = {
            'doc1': {
                'id': 'doc1',
                'title': '테스트 문서 1',
                'filename': 'test1.txt',
                'fileType': 'text/plain',
                'createdAt': '2023-01-01T00:00:00',
                'updatedAt': '2023-01-01T00:00:00',
                'content': '이 문서는 테스트를 위한 문서입니다.\n여기에는 테스트 텍스트가 포함되어 있습니다.'
            },
            'doc2': {
                'id': 'doc2',
                'title': '제목 테스트 문서',
                'filename': 'test2.txt',
                'fileType': 'text/plain',
                'createdAt': '2023-01-02T00:00:00',
                'updatedAt': '2023-01-02T00:00:00',
                'content': '이 문서는 두 번째 테스트 문서입니다.\n제목에서 일치하는 항목이 있습니다.'
            }
        }
        
        # ReportGenerator 인스턴스 생성
        self.report_generator = ReportGenerator(self.test_dir, self.mock_storage)
    
    def _mock_get_document(self, doc_id):
        """문서 조회 모의 메서드"""
        return self.test_documents.get(doc_id)
    
    def tearDown(self):
        """테스트 후 정리"""
        # 임시 디렉토리 삭제
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_generate_html_report(self):
        """HTML 보고서 생성 테스트"""
        # 보고서 생성
        report_metadata = self.report_generator.generate_report(
            self.test_results, 'html'
        )
        
        # 메타데이터 검증
        self.assertIn('id', report_metadata)
        self.assertEqual(report_metadata['format'], 'html')
        self.assertEqual(report_metadata['matchCount'], 2)
        
        # 보고서 파일 존재 확인
        report_path = report_metadata.get('path')
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))
        self.assertTrue(report_path.endswith('.html'))
        
        # 보고서 내용 확인
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('문서 검색 결과 보고서', content)
            self.assertIn('테스트 텍스트', content)
            self.assertIn('제목 테스트', content)
    
    def test_generate_json_report(self):
        """JSON 보고서 생성 테스트"""
        # 보고서 생성
        report_metadata = self.report_generator.generate_report(
            self.test_results, 'json'
        )
        
        # 메타데이터 검증
        self.assertIn('id', report_metadata)
        self.assertEqual(report_metadata['format'], 'json')
        self.assertEqual(report_metadata['matchCount'], 2)
        
        # 보고서 파일 존재 확인
        report_path = report_metadata.get('path')
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))
        self.assertTrue(report_path.endswith('.json'))
        
        # JSON 파일 로드 및 검증
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
            
            self.assertEqual(report_data['report_id'], report_metadata['id'])
            self.assertEqual(len(report_data['results']['matches']), 2)
            self.assertEqual(len(report_data['documents']), 2)
    
    def test_invalid_report_format(self):
        """잘못된 보고서 형식 테스트"""
        with self.assertRaises(ValueError):
            self.report_generator.generate_report(self.test_results, 'invalid_format')
    
    def test_empty_search_results(self):
        """빈 검색 결과 테스트"""
        empty_results = {'id': 'empty_search', 'query': 'no results', 'matchCount': 0, 'matches': []}
        
        # HTML 보고서 생성
        html_metadata = self.report_generator.generate_report(empty_results, 'html')
        self.assertEqual(html_metadata['matchCount'], 0)
        
        # JSON 보고서 생성
        json_metadata = self.report_generator.generate_report(empty_results, 'json')
        self.assertEqual(json_metadata['matchCount'], 0)

if __name__ == '__main__':
    unittest.main()
