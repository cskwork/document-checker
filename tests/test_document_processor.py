import os
import unittest
import tempfile
import shutil
import sys
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# docling 모듈 모킹 설정
mock_docling = MagicMock()
mock_converter_class = MagicMock()
mock_docling.document_converter = MagicMock()
mock_docling.document_converter.DocumentConverter = mock_converter_class
sys.modules['docling'] = mock_docling
sys.modules['docling.document_converter'] = mock_docling.document_converter

# Now import after mocking
from document_processor.processor import DocumentProcessor

class TestDocumentProcessor(unittest.TestCase):
    """DocumentProcessor 클래스의 단위 테스트"""
    
    def setUp(self):
        """테스트 전 설정"""
        self.test_dir = tempfile.mkdtemp()
        # Patch DOCLING_AVAILABLE to True for tests that need it
        self.docling_patch = patch('document_processor.processor.DOCLING_AVAILABLE', True)
        self.docling_patch.start()
        
        self.processor = DocumentProcessor()
        
        # 테스트용 파일 생성
        self.txt_file = os.path.join(self.test_dir, 'test.txt')
        with open(self.txt_file, 'w', encoding='utf-8') as f:
            f.write("This is a test document.\nIt has multiple lines.")
    
    def tearDown(self):
        """테스트 후 정리"""
        self.docling_patch.stop()
        shutil.rmtree(self.test_dir)
    
    def test_process_document_success(self):
        """문서 처리 성공 테스트"""
        # 모의 객체 설정
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        
        # 변환 결과 모의 객체
        mock_result = MagicMock()
        mock_doc = MagicMock()
        mock_doc.export_to_text.return_value = "This is a test document."
        mock_doc.export_to_markdown.return_value = ""  # No markdown
        mock_doc.sections = []
        mock_doc.metadata = {'author': 'Test User', 'created': '2023-01-01'}
        # text 속성도 추가
        mock_doc.text = None
        mock_result.document = mock_doc
        
        mock_converter.convert.return_value = mock_result
        
        # PDF 파일 테스트
        pdf_file = os.path.join(self.test_dir, 'test.pdf')
        with open(pdf_file, 'wb') as f:
            f.write(b'%PDF-1.4')  # 최소 PDF 헤더
        
        # 문서 처리 실행
        result = self.processor.process_document(pdf_file)
        
        # 결과 검증
        self.assertEqual(result['processingStatus'], 'processed')
        self.assertEqual(result['format'], 'pdf')
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
    
    def test_corrupted_document(self):
        """손상된 문서 처리 테스트"""
        # 모의 예외 발생
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        mock_converter.convert.side_effect = Exception("Corrupted document")
        
        # PDF 파일 테스트
        pdf_file = os.path.join(self.test_dir, 'test.pdf')
        with open(pdf_file, 'wb') as f:
            f.write(b'%PDF-1.4')
        
        result = self.processor.process_document(pdf_file)
        self.assertEqual(result['processingStatus'], 'error')
        self.assertEqual(result['error'], 'Corrupted document')

if __name__ == '__main__':
    unittest.main()
