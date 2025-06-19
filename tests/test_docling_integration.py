import unittest
import os
import json
import subprocess
import json
import os
from pathlib import Path
import tempfile

class TestDoclingIntegration(unittest.TestCase):
    """Docling 통합 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정: 테스트용 PDF 파일 생성"""
        # 테스트용 PDF 파일 경로
        cls.test_data_dir = Path(__file__).parent / "test_data"
        cls.test_data_dir.mkdir(exist_ok=True)
        cls.test_pdf = cls.test_data_dir / "test_document.pdf"
        
        # 테스트용 PDF가 없으면 생성
        if not cls.test_pdf.exists():
            print("테스트용 PDF 파일을 생성 중...")
            subprocess.run(
                ["python", "tests/create_test_pdf.py", str(cls.test_pdf)],
                check=True
            )
    
    def setUp(self):
        """테스트 전 설정"""
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.test_dir.name)
    
    def tearDown(self):
        """테스트 후 정리"""
        self.test_dir.cleanup()
    
    def test_docling_cli_available(self):
        """Docling CLI가 사용 가능한지 테스트"""
        try:
            result = subprocess.run(
                ["docling", "--version"],
                capture_output=True,
                text=True
            )
            self.assertEqual(result.returncode, 0, "Docling CLI is not available")
            print(f"Docling version: {result.stdout.strip()}")
        except Exception as e:
            self.fail(f"Failed to run Docling CLI: {e}")
    
    def test_docling_process_pdf(self):
        """Docling을 사용한 PDF 문서 처리 테스트"""
        try:
            # Docling CLI를 사용하여 PDF 문서 처리
            cmd = [
                "docling",
                str(self.test_pdf),  # 입력 PDF 파일
                "--output", str(self.output_dir),  # 출력 디렉토리
                "--verbose"  # 자세한 로그 출력
            ]
            
            print(f"실행 명령어: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # 명령어 실행 결과 출력 (디버깅용)
            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # 명령어 실행 성공 확인
            self.assertEqual(result.returncode, 0, 
                           f"Docling CLI failed with error: {result.stderr}")
            
            # 출력 파일이 생성되었는지 확인 (기본 출력 파일명은 입력 파일명과 동일하게 생성됨)
            expected_output_file = self.output_dir / f"{self.test_pdf.stem}.md"
            self.assertTrue(
                expected_output_file.exists(), 
                f"Output file {expected_output_file} was not created"
            )
            
            # 출력 파일 내용 확인
            try:
                with open(expected_output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 출력 내용이 비어있지 않은지 확인
                self.assertTrue(len(content) > 0, "Output file is empty")
                print(f"Successfully processed document. Output size: {len(content)} bytes")
                
                # 주요 영어 내용이 포함되어 있는지 확인
                expected_contents = [
                    "This is a test document",  # 문서 제목
                    "Docling integration testing"  # 문서 본문 일부
                ]
                for expected in expected_contents:
                    self.assertIn(expected, content, f"Expected content not found: {expected}")
                
            except json.JSONDecodeError as e:
                self.fail(f"Output file is not valid JSON: {e}")
                
        except Exception as e:
            self.fail(f"Error processing document with Docling: {e}")

if __name__ == "__main__":
    unittest.main()