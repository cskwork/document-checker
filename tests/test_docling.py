#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docling 라이브러리 테스트 스크립트
PDF 파일을 마크다운으로 변환하는 기능 테스트
"""

import os
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Docling 라이브러리 import 확인
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

class TestDoclingConversion(unittest.TestCase):
    """Docling 변환 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 테스트용 PDF 파일 생성 (최소 PDF 구조)
        self.test_pdf = os.path.join(self.test_dir, "test.pdf")
        with open(self.test_pdf, 'wb') as f:
            # 최소 PDF 헤더와 구조
            f.write(b"%PDF-1.4\n")
            f.write(b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n")
            f.write(b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n")
            f.write(b"3 0 obj<</Type/Page/Parent 2 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n")
            f.write(b"4 0 obj<</Length 44>>stream\n")
            f.write(b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n")
            f.write(b"endstream\nendobj\n")
            f.write(b"xref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000260 00000 n\n")
            f.write(b"trailer<</Size 5/Root 1 0 R>>\n")
            f.write(b"startxref\n349\n%%EOF")
    
    def tearDown(self):
        """테스트 후 정리"""
        shutil.rmtree(self.test_dir)
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "docling 라이브러리를 사용할 수 없습니다")
    def test_docling_conversion(self):
        """
        Docling을 사용하여 PDF 파일을 마크다운으로 변환하는 테스트
        """
        # DocumentConverter 인스턴스 생성
        converter = DocumentConverter()
        
        # 변환 실행
        result = converter.convert(self.test_pdf)
        
        # 결과 검증
        self.assertIsNotNone(result, "변환 결과가 None이 아니어야 합니다")
        self.assertIsNotNone(result.document, "document 객체가 존재해야 합니다")
        
        docling_doc = result.document
        
        # 텍스트 추출 검증
        if hasattr(docling_doc, 'text'):
            self.assertIsInstance(docling_doc.text, str, "추출된 텍스트는 문자열이어야 합니다")
        
        # export_to_text 메서드 테스트
        if hasattr(docling_doc, 'export_to_text'):
            text = docling_doc.export_to_text()
            self.assertIsInstance(text, str, "export_to_text 결과는 문자열이어야 합니다")
            
            # 출력 파일 저장
            output_path = os.path.join(self.output_dir, "test_output.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.assertTrue(os.path.exists(output_path), "출력 파일이 생성되어야 합니다")
            self.assertGreater(os.path.getsize(output_path), 0, "출력 파일에 내용이 있어야 합니다")
    
    @patch('docling.document_converter.DocumentConverter')
    def test_docling_conversion_mocked(self, mock_converter_class):
        """모의 객체를 사용한 Docling 변환 테스트"""
        # Skip this test if docling is not available
        if not DOCLING_AVAILABLE:
            self.skipTest("docling 라이브러리를 사용할 수 없어 모의 테스트를 건너뜁니다")
            
        # 모의 객체 설정
        mock_converter = MagicMock()
        mock_converter_class.return_value = mock_converter
        
        mock_result = MagicMock()
        mock_doc = MagicMock()
        mock_doc.text = "Test content"
        mock_doc.export_to_text.return_value = "Test content exported"
        mock_result.document = mock_doc
        
        mock_converter.convert.return_value = mock_result
        
        # 변환 실행
        converter = DocumentConverter()
        result = converter.convert(self.test_pdf)
        
        # 검증
        mock_converter.convert.assert_called_once_with(self.test_pdf)
        self.assertEqual(result.document.text, "Test content")
        self.assertEqual(result.document.export_to_text(), "Test content exported")

if __name__ == "__main__":
    unittest.main()
