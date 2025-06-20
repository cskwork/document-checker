import unittest
import tempfile
import os
from pathlib import Path

# Try to import from the correct location based on the library structure
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

class TestDoclingLibraryIntegration(unittest.TestCase):
    """Docling 라이브러리 통합 테스트"""

    def setUp(self):
        """테스트에 필요한 임시 파일 생성"""
        if not DOCLING_AVAILABLE:
            self.skipTest("docling 라이브러리를 찾을 수 없어 테스트를 건너뜁니다.")
        
        # 임시 텍스트 파일을 .md 확장자로 생성하여 Markdown으로 처리되도록 합니다.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = Path(self.temp_dir.name) / "test_doc.md"
        self.test_content = "This is a test document from the library integration test."
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.test_content)

    def tearDown(self):
        """임시 디렉토리 정리"""
        self.temp_dir.cleanup()

    def test_docling_converts_text_file(self):
        """Docling 라이브러리가 텍스트 파일을 처리할 수 있는지 테스트"""
        # 'md' (Markdown) 포맷을 허용하여 .md 파일 처리를 활성화합니다.
        converter = DocumentConverter(allowed_formats=[InputFormat.MD])
        
        # 파일 변환
        result = converter.convert(str(self.test_file_path))
        
        # 결과 확인
        self.assertIsNotNone(result, "변환 결과가 None이 아니어야 합니다.")
        
        doc = result.document
        self.assertIsNotNone(doc, "결과에서 document 객체를 찾을 수 없습니다.")
        
        # 텍스트 내용 확인
        # export_to_text() 또는 text 속성을 사용하여 텍스트 추출
        extracted_text = ""
        if hasattr(doc, 'export_to_text'):
            extracted_text = doc.export_to_text()
        elif hasattr(doc, 'text'):
            extracted_text = doc.text
        
        self.assertIn(self.test_content, extracted_text, "추출된 텍스트에 원본 내용이 포함되어야 합니다.")
        
        print("\nDocling library integration test passed successfully!")

if __name__ == "__main__":
    unittest.main() 