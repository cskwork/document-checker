"""
ContentAnalyzer 테스트 모듈

이 모듈은 ContentAnalyzer 클래스의 기능을 테스트합니다.
"""

import unittest
import os
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# 테스트를 위해 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.content_analyzer.analyzer import ContentAnalyzer


class MockStorageManager:
    """ContentAnalyzer 테스트를 위한 Mock StorageManager 클래스"""
    
    def __init__(self):
        self.documents = {}
    
    def add_document(self, doc_id, content, created_at=None):
        """테스트용 문서 추가"""
        if created_at is None:
            created_at = datetime.now().isoformat()
            
        self.documents[doc_id] = {
            'id': doc_id,
            'content': {'text': content},
            'createdAt': created_at,
            'sections': [
                {'title': 'Introduction', 'start': 0, 'end': 100},
                {'title': 'Main Content', 'start': 101, 'end': 500},
                {'title': 'Conclusion', 'start': 501, 'end': 600}
            ]
        }
    
    def get_document(self, doc_id):
        """문서 ID로 문서 조회"""
        return self.documents.get(doc_id)
    
    def list_documents(self):
        """모든 문서 목록 반환"""
        return list(self.documents.values())


class TestContentAnalyzer(unittest.TestCase):
    """ContentAnalyzer 테스트 케이스"""
    
    def setUp(self):
        """테스트 전 설정"""
        self.storage_manager = MockStorageManager()
        self.analyzer = ContentAnalyzer(self.storage_manager)
        
        # 테스트용 문서 추가
        self.doc1_id = "doc1"
        self.doc1_content = """
        This is a test document containing some sample text.
        It includes keywords like 'test', 'sample', and 'document'.
        There are also some numbers like 123 and 456.
        And a formula: E = mc^2
        """
        self.storage_manager.add_document(self.doc1_id, self.doc1_content)
        
        # 두 번째 문서 (날짜 범위 테스트용)
        self.doc2_id = "doc2"
        self.doc2_content = "Another document with different content and keywords."
        past_date = (datetime.now() - timedelta(days=10)).isoformat()
        self.storage_manager.add_document(self.doc2_id, self.doc2_content, past_date)
    
    def test_create_search_query_default(self):
        """기본 검색 쿼리 생성 테스트"""
        query = self.analyzer.create_search_query("test")
        
        self.assertIn('id', query)
        self.assertEqual(query['patterns'], ["test"])
        self.assertFalse(query['options']['caseSensitive'])
        self.assertFalse(query['options']['regex'])
        self.assertEqual(query['scope']['documentIds'], [])
    
    def test_search_simple_text(self):
        """단순 텍스트 검색 테스트"""
        query = self.analyzer.create_search_query("test")
        results = self.analyzer.execute_search(query)
        
        self.assertEqual(results['matchCount'], 1)
        self.assertEqual(len(results['matches']), 1)
        self.assertEqual(results['matches'][0]['documentId'], self.doc1_id)
    
    def test_case_sensitive_search(self):
        """대소문자 구분 검색 테스트"""
        # 대소문자 구분 없이 검색 (기본값)
        query = self.analyzer.create_search_query("Test", options={'caseSensitive': False})
        results = self.analyzer.execute_search(query)
        self.assertGreater(results['matchCount'], 0)
        
        # 대소문자 구분하여 검색
        query = self.analyzer.create_search_query("Test", options={'caseSensitive': True})
        results = self.analyzer.execute_search(query)
        self.assertEqual(results['matchCount'], 0)  # 'Test'는 문서에 없음
    
    def test_whole_word_search(self):
        """전체 단어 일치 검색 테스트"""
        # 'tes'로 검색 (부분 일치)
        query = self.analyzer.create_search_query("tes", options={'wholeWord': False})
        results = self.analyzer.execute_search(query)
        self.assertGreater(results['matchCount'], 0)
        
        # 'tes'로 전체 단어 일치 검색
        query = self.analyzer.create_search_query("tes", options={'wholeWord': True})
        results = self.analyzer.execute_search(query)
        self.assertEqual(results['matchCount'], 0)  # 'tes'로 시작하는 단어만 있음
    
    def test_regex_search(self):
        """정규식 검색 테스트"""
        # 숫자 3자리 패턴 검색
        query = self.analyzer.create_search_query("\\d{3}", options={'regex': True})
        results = self.analyzer.execute_search(query)
        
        # 문서에는 123과 456이 있으므로 2개가 일치해야 함
        self.assertEqual(results['matchCount'], 2)
    
    def test_search_by_document_id(self):
        """문서 ID로 검색 범위 제한 테스트"""
        query = self.analyzer.create_search_query(
            "test", 
            scope={'documentIds': [self.doc1_id]}
        )
        results = self.analyzer.execute_search(query)
        
        # doc1에서만 검색했으므로 1개만 일치해야 함
        self.assertEqual(results['matchCount'], 1)
        self.assertEqual(results['matches'][0]['documentId'], self.doc1_id)
    
    def test_search_by_date_range(self):
        """날짜 범위로 검색 테스트"""
        # 오늘 날짜 범위로 검색 (doc1만 포함)
        today = datetime.now().date().isoformat()
        query = self.analyzer.create_search_query(
            "test",
            scope={
                'dateRange': {
                    'start': today,
                    'end': today
                }
            }
        )
        results = self.analyzer.execute_search(query)
        
        # doc1만 일치해야 함 (오늘 생성됨)
        self.assertEqual(results['matchCount'], 1)
        self.assertEqual(results['matches'][0]['documentId'], self.doc1_id)
    
    def test_find_section(self):
        """문서 섹션 찾기 테스트"""
        doc = self.storage_manager.get_document(self.doc1_id)
        
        # Introduction 섹션 (0-100)
        section = self.analyzer._find_section(doc, 50)
        self.assertEqual(section, 'Introduction')
        
        # Main Content 섹션 (101-500)
        section = self.analyzer._find_section(doc, 200)
        self.assertEqual(section, 'Main Content')
        
        # Conclusion 섹션 (501-600)
        section = self.analyzer._find_section(doc, 550)
        self.assertEqual(section, 'Conclusion')
        
        # 범위 밖의 위치
        section = self.analyzer._find_section(doc, 1000)
        self.assertEqual(section, 'Unknown section')


if __name__ == '__main__':
    unittest.main()
