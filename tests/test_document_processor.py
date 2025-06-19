import os
import unittest
import tempfile
import shutil
import sys
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# docling 모듈을 모의로 생성
sys.modules['docling'] = Mock()
from docling import Document

from document_processor.processor import DocumentProcessor

class TestDocumentProcessor(unittest.TestCase):
    """DocumentProcessor 클래스의 단위 테스트"""
    
    def setUp(self):
        """테스트 전 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.processor = DocumentProcessor()
        
        # 테스트용 파일 생성
        self.txt_file = os.path.join(self.test_dir, 'test.txt')
        with open(self.txt_file, 'w', encoding='utf-8') as f:
            f.write("This is a test document.\nIt has multiple lines.")
    
    def tearDown(self):
        """테스트 후 정리"""
        shutil.rmtree(self.test_dir)
    
    @patch('document_processor.processor.Document')
    def test_process_document_success(self, mock_document):
        """문서 처리 성공 테스트"""
        # 모의 객체 설정
        mock_doc = MagicMock()
        mock_doc.text = "This is a test document."
        mock_doc.get_sections.return_value = [{'title': 'Section 1', 'content': 'Content 1'}]
        mock_doc.metadata = {'author': 'Test User', 'created': '2023-01-01'}
        mock_document.from_file.return_value = mock_doc
        
        # 문서 처리 실행
        result = self.processor.process_document(self.txt_file)
        
        # 결과 검증
        self.assertEqual(result['processingStatus'], 'processed')
        self.assertEqual(result['format'], 'txt')
        self.assertEqual(result['content']['text'], "This is a test document.")
        self.assertIn('sections', result['content'])
        self.assertIn('metadata', result['content'])
    
    def test_unsupported_format(self):
        """지원하지 않는 형식의 문서 처리 테스트"""
        unsupported_file = os.path.join(self.test_dir, 'test.unsupported')
        with open(unsupported_file, 'w') as f:
            f.write("content")
            
        result = self.processor.process_document(unsupported_file)
        self.assertEqual(result['processingStatus'], 'error')
        self.assertIn('지원하지 않는 파일 형식입니다', result['error'])
    
    @patch('document_processor.processor.Document.from_file')
    def test_corrupted_document(self, mock_from_file):
        """손상된 문서 처리 테스트"""
        # 모의 예외 발생
        mock_from_file.side_effect = Exception("Corrupted document")
        
        result = self.processor.process_document(self.txt_file)
        self.assertEqual(result['processingStatus'], 'error')
        self.assertEqual(result['error'], 'Corrupted document')

if __name__ == '__main__':
    unittest.main()
