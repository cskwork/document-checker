"""
User Interface 테스트 모듈

Flask 애플리케이션의 기능을 테스트합니다.
"""

import os
import json
import tempfile
import shutil
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.user_interface.app import app


class TestUserInterface(unittest.TestCase):
    """Flask 애플리케이션 테스트 클래스"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 테스트용 문서 인덱스 파일 생성
        self.index_file = os.path.join(self.output_dir, 'document_index.json')
        self.test_documents = {
            "test_doc_1": {
                "id": "test_doc_1",
                "filename": "test1.pdf",
                "format": "pdf",
                "createdAt": "2024-01-01T00:00:00",
                "path": "/path/to/test1.json"
            },
            "test_doc_2": {
                "id": "test_doc_2",
                "filename": "test2.docx",
                "format": "docx",
                "createdAt": "2024-01-02T00:00:00",
                "path": "/path/to/test2.json"
            }
        }
        with open(self.index_file, 'w') as f:
            json.dump(self.test_documents, f)
    
    def tearDown(self):
        """테스트 후 정리"""
        shutil.rmtree(self.test_dir)
    
    def test_index_page(self):
        """메인 페이지 테스트"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Document Checker', response.data)
    
    @patch('src.user_interface.app.storage_manager')
    def test_upload_file_success(self, mock_storage):
        """파일 업로드 성공 테스트"""
        # Mock 설정
        mock_storage.process_new_document.return_value = "test_doc_id"
        
        # 테스트 파일 생성
        data = {
            'file': (tempfile.NamedTemporaryFile(suffix='.pdf'), 'test.pdf')
        }
        
        response = self.client.post('/upload', 
                                  data=data, 
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['document_id'], 'test_doc_id')
    
    def test_upload_file_no_file(self):
        """파일 없이 업로드 시도 테스트"""
        response = self.client.post('/upload')
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'error')
    
    @patch('src.user_interface.app.storage_manager')
    def test_search_documents(self, mock_storage):
        """문서 검색 테스트"""
        # Mock 설정
        mock_analyzer = MagicMock()
        mock_analyzer.search.return_value = {
            'results': [
                {
                    'documentId': 'test_doc_1',
                    'filename': 'test1.pdf',
                    'matches': [{'text': 'test match', 'section': 'Section 1'}]
                }
            ],
            'total': 1
        }
        mock_storage.analyzer = mock_analyzer
        
        response = self.client.post('/search',
                                  json={'query': 'test', 'options': {}})
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(len(json_data['results']), 1)
    
    @patch('src.user_interface.app.storage_manager')
    def test_get_document(self, mock_storage):
        """문서 조회 테스트"""
        # Mock 설정
        mock_document = {
            'id': 'test_doc_1',
            'filename': 'test.pdf',
            'content': {
                'text': 'Test document content',
                'sections': [{'title': 'Section 1', 'content': 'Content 1'}]
            }
        }
        mock_storage.get_document.return_value = mock_document
        
        response = self.client.get('/document/test_doc_1')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['id'], 'test_doc_1')
        self.assertEqual(json_data['filename'], 'test.pdf')
    
    @patch('src.user_interface.app.storage_manager')
    def test_get_document_not_found(self, mock_storage):
        """존재하지 않는 문서 조회 테스트"""
        mock_storage.get_document.return_value = None
        
        response = self.client.get('/document/nonexistent')
        
        self.assertEqual(response.status_code, 404)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['error'], '문서를 찾을 수 없습니다')
    
    @patch('src.user_interface.app.storage_manager')
    def test_list_documents(self, mock_storage):
        """문서 목록 조회 테스트"""
        mock_storage.list_documents.return_value = list(self.test_documents.values())
        
        response = self.client.get('/documents')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(len(json_data), 2)
        self.assertEqual(json_data[0]['id'], 'test_doc_1')
    
    @patch('src.user_interface.app.batch_processor')
    def test_batch_upload_success(self, mock_batch):
        """배치 업로드 성공 테스트"""
        mock_batch.start_batch_job.return_value = 'batch_job_123'
        
        # 여러 파일 업로드
        data = {
            'files': [
                (tempfile.NamedTemporaryFile(suffix='.pdf'), 'test1.pdf'),
                (tempfile.NamedTemporaryFile(suffix='.docx'), 'test2.docx')
            ]
        }
        
        response = self.client.post('/batch/upload',
                                  data=data,
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['job_id'], 'batch_job_123')
    
    @patch('src.user_interface.app.batch_processor')
    def test_batch_status(self, mock_batch):
        """배치 작업 상태 조회 테스트"""
        mock_batch.get_job_status.return_value = {
            'job_id': 'batch_job_123',
            'status': 'processing',
            'progress': 0.5,
            'total_files': 10,
            'processed_files': 5
        }
        
        response = self.client.get('/batch/status/batch_job_123')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'processing')
        self.assertEqual(json_data['progress'], 0.5)
    
    def test_search_page(self):
        """검색 페이지 테스트"""
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'search', response.data)
    
    def test_document_viewer_page(self):
        """문서 뷰어 페이지 테스트"""
        response = self.client.get('/document/viewer/test_doc_1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'document_viewer', response.data)
    
    def test_error_handling(self):
        """에러 핸들링 테스트"""
        # 404 에러 테스트
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main() 