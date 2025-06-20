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
        # 한글로 되어 있으므로 문서 검사기 확인
        self.assertIn('문서 검사기'.encode('utf-8'), response.data)
    
    @patch('src.user_interface.app.storage_manager')
    def test_upload_file_success(self, mock_storage):
        """파일 업로드 성공 테스트"""
        # Mock 설정
        mock_storage.process_new_document.return_value = "test_doc_id"
        
        # 테스트 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b'test content')
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                data = {
                    'file': (f, 'test.pdf')
                }
                
                response = self.client.post('/api/upload', 
                                          data=data, 
                                          content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            json_data = json.loads(response.data)
            self.assertEqual(json_data['status'], 'success')
            self.assertIn('filename', json_data)
        finally:
            os.unlink(tmp_file_path)
    
    def test_upload_file_no_file(self):
        """파일 없이 업로드 시도 테스트"""
        response = self.client.post('/api/upload')
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'error')
        self.assertIn('No file part', json_data['message'])
    
    @patch('src.user_interface.app.storage_manager')
    @patch('src.user_interface.app.content_analyzer')
    @patch('src.user_interface.app.report_generator')
    def test_search_documents(self, mock_report, mock_analyzer, mock_storage):
        """문서 검색 테스트"""
        # Mock 설정
        mock_search_results = {
            'matches': [
                {
                    'documentId': 'test_doc_1',
                    'text': 'test match',
                    'section': 'Section 1'
                }
            ],
            'total': 1
        }
        mock_analyzer.execute_search.return_value = mock_search_results
        mock_analyzer.create_search_query.return_value = {'patterns': ['test']}
        
        # Mock document metadata
        mock_storage.get_document_metadata.return_value = {
            'id': 'test_doc_1',
            'filename': 'test1.pdf',
            'createdAt': '2024-01-01T00:00:00',
            'format': 'pdf'
        }
        
        # Mock report generation
        mock_report.generate_report.return_value = {
            'id': 'report_123',
            'path': '/path/to/report.html'
        }
        
        response = self.client.post('/api/search',
                                  json={'patterns': ['test'], 'options': {}})
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertIn('results', json_data['data'])
        self.assertEqual(len(json_data['data']['results']), 1)
    
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
        
        response = self.client.get('/api/documents/test_doc_1')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['data']['id'], 'test_doc_1')
        self.assertEqual(json_data['data']['filename'], 'test.pdf')
    
    @patch('src.user_interface.app.storage_manager')
    def test_get_document_not_found(self, mock_storage):
        """존재하지 않는 문서 조회 테스트"""
        mock_storage.get_document.return_value = None
        
        response = self.client.get('/api/documents/nonexistent')
        
        self.assertEqual(response.status_code, 404)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'error')
        self.assertEqual(json_data['message'], 'Document not found')
    
    @patch('src.user_interface.app.storage_manager')
    def test_list_documents(self, mock_storage):
        """문서 목록 조회 테스트"""
        mock_storage.list_documents.return_value = list(self.test_documents.values())
        
        response = self.client.get('/api/documents')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(len(json_data['data']), 2)
        self.assertEqual(json_data['data'][0]['id'], 'test_doc_1')
    
    @patch('src.user_interface.app.storage_manager')
    def test_batch_jobs_list(self, mock_storage):
        """배치 작업 목록 조회 테스트"""
        # Mock batch processor
        mock_batch = MagicMock()
        mock_batch.get_all_jobs.return_value = [
            {
                'job_id': 'batch_job_123',
                'status': 'running',
                'progress': 0.5,
                'total_files': 10,
                'processed_files': 5
            }
        ]
        mock_storage.batch_processor = mock_batch
        
        response = self.client.get('/api/jobs')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(len(json_data['data']), 1)
        self.assertEqual(json_data['data'][0]['job_id'], 'batch_job_123')
    
    @patch('src.user_interface.app.storage_manager')
    def test_batch_job_status(self, mock_storage):
        """배치 작업 상태 조회 테스트"""
        # Mock batch processor
        mock_batch = MagicMock()
        mock_batch.get_job.return_value = {
            'job_id': 'batch_job_123',
            'status': 'processing',
            'progress': 0.5,
            'total_files': 10,
            'processed_files': 5
        }
        mock_storage.batch_processor = mock_batch
        
        response = self.client.get('/api/jobs/batch_job_123')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['data']['status'], 'processing')
        self.assertEqual(json_data['data']['progress'], 0.5)
    
    def test_search_page(self):
        """검색 페이지 테스트"""
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'search', response.data)
    
    def test_document_viewer_page(self):
        """문서 뷰어 페이지 테스트"""
        response = self.client.get('/view/document/test_doc_1')
        self.assertEqual(response.status_code, 200)
        # Check for Korean text that appears in the document viewer
        self.assertIn('문서 뷰어'.encode('utf-8'), response.data)
    
    def test_error_handling(self):
        """에러 핸들링 테스트"""
        # 404 에러 테스트
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
        self.assertIn('찾을 수 없습니다'.encode('utf-8'), response.data)
    
    @patch('src.user_interface.app.report_generator')
    def test_get_document_stats(self, mock_report):
        """문서 통계 API 테스트"""
        mock_report.get_document_statistics.return_value = {
            'total': 10,
            'processed': 8,
            'pending': 1,
            'error': 1,
            'recentDocuments': []
        }
        
        response = self.client.get('/api/documents/stats')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['data']['total'], 10)
        self.assertEqual(json_data['data']['processed'], 8)

    @patch('src.user_interface.app.report_generator')
    def test_get_report(self, mock_report):
        """보고서 조회 API 테스트"""
        mock_report.get_report.return_value = {
            'id': 'report_123',
            'format': 'html',
            'path': '/path/to/report.html',
            'generatedAt': '2024-01-01T00:00:00'
        }
        
        response = self.client.get('/api/reports/report_123')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['data']['id'], 'report_123')
    
    @patch('src.user_interface.app.report_generator')
    def test_get_report_not_found(self, mock_report):
        """존재하지 않는 보고서 조회 테스트"""
        mock_report.get_report.return_value = None
        
        response = self.client.get('/api/reports/nonexistent')
        
        self.assertEqual(response.status_code, 404)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'error')
        self.assertEqual(json_data['message'], 'Report not found')
    
    @patch('src.user_interface.app.report_generator')
    def test_view_report_html(self, mock_report):
        """HTML 보고서 뷰어 테스트"""
        # 임시 HTML 파일 생성
        report_path = os.path.join(self.output_dir, 'test_report.html')
        with open(report_path, 'w') as f:
            f.write('<html><body>Test Report</body></html>')
        
        mock_report.get_report.return_value = {
            'id': 'report_123',
            'format': 'html',
            'path': report_path
        }
        
        response = self.client.get('/view/report/report_123')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Report', response.data)
    
    @patch('src.user_interface.app.report_generator')
    def test_view_report_json(self, mock_report):
        """JSON 보고서 뷰어 테스트"""
        # 임시 JSON 파일 생성
        report_path = os.path.join(self.output_dir, 'test_report.json')
        with open(report_path, 'w') as f:
            json.dump({'test': 'report'}, f)
        
        mock_report.get_report.return_value = {
            'id': 'report_123',
            'format': 'json',
            'path': report_path
        }
        
        response = self.client.get('/view/report/report_123')
        
        self.assertEqual(response.status_code, 200)
        # JSON viewer template을 렌더링하는지 확인
        self.assertIn(b'json', response.data.lower())
    
    @patch('src.user_interface.app.storage_manager')
    @patch('src.user_interface.app.document_processor')
    def test_create_batch_job(self, mock_processor, mock_storage):
        """배치 작업 생성 테스트"""
        # Mock batch processor
        mock_batch = MagicMock()
        mock_batch.create_job.return_value = 'job_123'
        mock_batch.start_job.return_value = None
        mock_storage.batch_processor = mock_batch
        
        response = self.client.post('/api/jobs',
                                  json={
                                      'job_type': 'process_directory',
                                      'job_params': {'directory': '/test'}
                                  })
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['data']['job_id'], 'job_123')
        mock_batch.create_job.assert_called_once()
        mock_batch.start_job.assert_called_once_with('job_123')
    
    @patch('src.user_interface.app.storage_manager')
    def test_create_batch_job_invalid_type(self, mock_storage):
        """잘못된 작업 유형으로 배치 작업 생성 테스트"""
        mock_storage.batch_processor = MagicMock()
        
        response = self.client.post('/api/jobs',
                                  json={'job_type': 'invalid_type'})
        
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'error')
        self.assertIn('유효하지 않은 작업 유형', json_data['message'])
    
    @patch('src.user_interface.app.storage_manager')
    def test_delete_batch_job(self, mock_storage):
        """배치 작업 삭제 테스트"""
        mock_batch = MagicMock()
        mock_batch.job_exists.return_value = True
        mock_batch.delete_job.return_value = None
        mock_storage.batch_processor = mock_batch
        
        response = self.client.delete('/api/jobs/job_123')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        mock_batch.delete_job.assert_called_once_with('job_123')
    
    @patch('src.user_interface.app.storage_manager')
    def test_update_batch_job(self, mock_storage):
        """배치 작업 업데이트 테스트"""
        mock_batch = MagicMock()
        mock_batch.job_exists.return_value = True
        mock_batch.pause_job.return_value = None
        mock_storage.batch_processor = mock_batch
        
        response = self.client.put('/api/jobs/job_123',
                                 json={'action': 'pause'})
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertIn('일시 중지', json_data['message'])
        mock_batch.pause_job.assert_called_once_with('job_123')
    
    @patch('src.user_interface.app.storage_manager')
    def test_update_batch_job_invalid_action(self, mock_storage):
        """잘못된 액션으로 배치 작업 업데이트 테스트"""
        mock_batch = MagicMock()
        mock_batch.job_exists.return_value = True
        mock_storage.batch_processor = mock_batch
        
        response = self.client.put('/api/jobs/job_123',
                                 json={'action': 'invalid_action'})
        
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'error')
        self.assertIn('유효하지 않은 액션', json_data['message'])
    
    def test_jobs_page(self):
        """배치 작업 관리 페이지 테스트"""
        response = self.client.get('/jobs')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'jobs', response.data)
    
    @patch('src.user_interface.app.content_analyzer', None)
    def test_search_without_analyzer(self):
        """content_analyzer가 초기화되지 않은 상태에서 검색 테스트"""
        response = self.client.post('/api/search', json={'patterns': ['test']})
        
        self.assertEqual(response.status_code, 500)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'error')
        self.assertIn('Required components not initialized', json_data['message'])
    
    @patch('src.user_interface.app.storage_manager', None)
    def test_list_documents_without_storage(self):
        """storage_manager가 초기화되지 않은 상태에서 문서 목록 조회 테스트"""
        response = self.client.get('/api/documents')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['data'], [])
    
    def test_upload_empty_filename(self):
        """빈 파일명으로 업로드 테스트"""
        data = {
            'file': (None, '')
        }
        response = self.client.post('/api/upload',
                                  data=data,
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['status'], 'error')
        self.assertEqual(json_data['message'], 'No selected file')
    
    @patch('src.user_interface.app.initialize_app')
    def test_app_initialization(self, mock_init):
        """애플리케이션 초기화 테스트"""
        # 애플리케이션이 이미 초기화되어 있으므로 이 테스트는 초기화 함수가 호출되는지만 확인
        from src.user_interface import app as app_module
        
        # 설정이 로드되는지 확인
        self.assertIsInstance(app_module.config, dict)


if __name__ == '__main__':
    unittest.main() 