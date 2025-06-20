"""
StorageManager 테스트 모듈

이 모듈은 StorageManager 클래스의 기능을 테스트합니다.
"""

import os
import json
import time
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# 테스트를 위한 임시 디렉토리 경로
TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
INPUT_DIR = os.path.join(TEST_DIR, 'input')
OUTPUT_DIR = os.path.join(TEST_DIR, 'output')

class TestStorageManager(unittest.TestCase):
    """StorageManager 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # 테스트 디렉토리 생성
        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def setUp(self):
        """각 테스트 메서드 전에 실행"""
        from src.storage_manager.manager import StorageManager
        
        # 모의 문서 처리기 생성
        self.mock_processor = MagicMock()
        self.mock_processor.process_document.return_value = {
            'id': 'test_doc_123',
            'filename': 'test.pdf',
            'format': 'pdf',
            'content': {
                'text': '테스트 문서 내용',
                'sections': [],
                'metadata': {}
            },
            'processingStatus': 'processed',
            'createdAt': time.time()
        }
        
        # StorageManager 인스턴스 생성
        self.storage = StorageManager(
            input_dir=INPUT_DIR,
            output_dir=OUTPUT_DIR,
            document_processor=self.mock_processor
        )
    
    def tearDown(self):
        """각 테스트 메서드 후에 실행"""
        # 모니터링 중지
        self.storage.stop_monitoring()
        
        # 테스트 파일 정리
        for item in os.listdir(INPUT_DIR):
            path = os.path.join(INPUT_DIR, item)
            if os.path.isfile(path):
                os.remove(path)
        
        for root, dirs, files in os.walk(OUTPUT_DIR, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    
    def test_initialization(self):
        """초기화 테스트"""
        self.assertTrue(os.path.exists(INPUT_DIR))
        self.assertTrue(os.path.exists(OUTPUT_DIR))
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, 'documents')))
    
    def test_store_and_retrieve_document(self):
        """문서 저장 및 조회 테스트"""
        # 테스트 문서 모델
        doc = {
            'id': 'test_doc_1',
            'filename': 'test.pdf',
            'format': 'pdf',
            'content': '테스트 문서 내용',
            'createdAt': time.time()
        }
        
        # 문서 저장
        result = self.storage.store_document(doc)
        self.assertTrue(result)
        
        # 문서 조회
        retrieved_doc = self.storage.get_document('test_doc_1')
        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc['id'], 'test_doc_1')
        self.assertEqual(retrieved_doc['filename'], 'test.pdf')
        
        # 캐시에서 조회되는지 확인
        self.assertIn('test_doc_1', self.storage.cache)
    
    def test_process_new_document(self):
        """새 문서 처리 테스트"""
        # 테스트 파일 생성
        test_file = os.path.join(INPUT_DIR, 'test_document.pdf')
        with open(test_file, 'w') as f:
            f.write('테스트 파일 내용')
        
        # 문서 처리
        doc_id = self.storage.process_new_document(test_file)
        self.assertIsNotNone(doc_id)
        
        # 문서가 인덱스에 추가되었는지 확인
        self.assertIn(doc_id, self.storage.document_index)
        self.assertEqual(self.storage.document_index[doc_id]['filename'], 'test_document.pdf')
    
    def test_file_monitoring(self):
        """파일 모니터링 테스트"""
        # 모니터링 시작
        self.storage.start_monitoring()
        
        # 테스트 파일 생성
        test_file = os.path.join(INPUT_DIR, 'monitor_test.pdf')
        with open(test_file, 'w') as f:
            f.write('모니터링 테스트 파일')
        
        # 파일이 처리될 시간 확보 (이벤트 루프가 처리할 시간을 주기 위해 대기)
        max_attempts = 10
        for _ in range(max_attempts):
            if self.mock_processor.process_document.called:
                break
            time.sleep(0.5)
        
        # 문서 처리기 호출 확인
        self.assertTrue(self.mock_processor.process_document.called, 
                       "문서 처리기가 호출되지 않았습니다.")
        
        # 호출된 인자 확인
        args, _ = self.mock_processor.process_document.call_args
        self.assertEqual(args[0], test_file)
        
        # 문서가 인덱스에 추가되었는지 확인
        self.assertGreater(len(self.storage.document_index), 0, 
                          "문서가 인덱스에 추가되지 않았습니다.")
        
        # 테스트 종료 전에 모니터링 중지 (이미 tearDown에서 처리되지만 명시적으로 중지)
        self.storage.stop_monitoring()
    
    def test_list_documents(self):
        """문서 목록 조회 테스트"""
        # 테스트 문서 추가
        for i in range(5):
            doc = {
                'id': f'test_doc_{i}',
                'filename': f'test_{i}.pdf',
                'format': 'pdf',
                'content': f'테스트 문서 {i}',
                'createdAt': time.time() - (i * 86400)  # 하루 간격으로 생성일 설정
            }
            self.storage.store_document(doc)
            
            # 문서 인덱스에 추가
            self.storage.document_index[doc['id']] = {
                'id': doc['id'],
                'filename': doc['filename'],
                'format': doc['format'],
                'createdAt': doc['createdAt'],
                'path': self.storage._get_document_path(doc['id'])
            }
        
        # 모든 문서 조회
        all_docs = self.storage.list_documents()
        self.assertEqual(len(all_docs), 5)
        
        # 필터링 조회 (최근 3일 이내)
        recent_docs = self.storage.list_documents({'days': 3})
        self.assertEqual(len(recent_docs), 3)
        
        # 형식 필터링
        pdf_docs = self.storage.list_documents({'format': 'pdf'})
        self.assertEqual(len(pdf_docs), 5)
        
        # 존재하지 않는 형식 필터링
        docx_docs = self.storage.list_documents({'format': 'docx'})
        self.assertEqual(len(docx_docs), 0)

    def test_get_document_metadata(self):
        """문서 메타데이터 조회 테스트"""
        # 테스트 문서 인덱스 추가
        test_metadata = {
            'id': 'test_doc_meta',
            'filename': 'test_meta.pdf',
            'format': 'pdf',
            'createdAt': time.time(),
            'path': '/path/to/doc'
        }
        self.storage.document_index['test_doc_meta'] = test_metadata
        
        # 메타데이터 조회
        metadata = self.storage.get_document_metadata('test_doc_meta')
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['filename'], 'test_meta.pdf')
        
        # 존재하지 않는 문서 메타데이터 조회
        none_metadata = self.storage.get_document_metadata('nonexistent')
        self.assertIsNone(none_metadata)
    
    def test_process_new_document_errors(self):
        """문서 처리 중 오류 상황 테스트"""
        # 1. 파일이 존재하지 않는 경우
        result = self.storage.process_new_document('/nonexistent/file.pdf')
        self.assertIsNone(result)
        
        # 2. 문서 처리기가 None을 반환하는 경우
        self.mock_processor.process_document.return_value = None
        test_file = os.path.join(INPUT_DIR, 'test_error.pdf')
        with open(test_file, 'w') as f:
            f.write('테스트 파일')
        
        result = self.storage.process_new_document(test_file)
        self.assertIsNone(result)
        
        # 3. 문서 처리기가 문자열을 반환하는 경우
        self.mock_processor.process_document.return_value = "Simple text content"
        test_file2 = os.path.join(INPUT_DIR, 'test_string.pdf')
        with open(test_file2, 'w') as f:
            f.write('테스트 파일')
        
        result = self.storage.process_new_document(test_file2)
        self.assertIsNotNone(result)  # 문자열도 처리 가능하게 구현됨
        
        # 4. 문서 처리기가 오류 상태를 반환하는 경우
        self.mock_processor.process_document.return_value = {
            'id': 'error_doc',
            'processingStatus': 'error',
            'error': 'Processing failed'
        }
        test_file3 = os.path.join(INPUT_DIR, 'test_error_status.pdf')
        with open(test_file3, 'w') as f:
            f.write('테스트 파일')
            
        result = self.storage.process_new_document(test_file3)
        self.assertIsNone(result)
        
        # 5. 문서 ID가 없는 경우
        self.mock_processor.process_document.return_value = {
            'filename': 'no_id.pdf',
            'content': 'test'
        }
        test_file4 = os.path.join(INPUT_DIR, 'test_no_id.pdf')
        with open(test_file4, 'w') as f:
            f.write('테스트 파일')
            
        result = self.storage.process_new_document(test_file4)
        self.assertIsNone(result)
    
    def test_store_document_errors(self):
        """문서 저장 중 오류 상황 테스트"""
        # 1. 문서 ID가 없는 경우
        doc_no_id = {
            'filename': 'no_id.pdf',
            'content': 'test'
        }
        result = self.storage.store_document(doc_no_id)
        self.assertFalse(result)
        
        # 2. 디렉토리 생성 실패 시뮬레이션 (권한 문제 등)
        # 이 테스트는 실제로는 OS 권한 문제를 시뮬레이션하기 어려우므로 
        # 다른 방법으로 접근
        doc_valid = {
            'id': 'test_doc_perm',
            'filename': 'test_perm.pdf',
            'content': 'test'
        }
        # 정상적인 경우 테스트
        result = self.storage.store_document(doc_valid)
        self.assertTrue(result)
    
    def test_get_document_not_found(self):
        """존재하지 않는 문서 조회 테스트"""
        # 캐시와 디스크 모두에 없는 문서
        doc = self.storage.get_document('nonexistent_doc')
        self.assertIsNone(doc)
    
    def test_get_document_load_error(self):
        """문서 로드 중 오류 테스트"""
        # 잘못된 JSON 파일 생성
        doc_id = 'corrupt_doc'
        doc_path = self.storage._get_document_path(doc_id)
        os.makedirs(os.path.dirname(doc_path), exist_ok=True)
        
        with open(doc_path, 'w') as f:
            f.write('invalid json content')
        
        # 문서 조회 시도
        doc = self.storage.get_document(doc_id)
        self.assertIsNone(doc)
    
    def test_save_document_index_error(self):
        """문서 인덱스 저장 중 오류 테스트"""
        # 인덱스 파일 경로를 잘못된 경로로 변경
        original_output = self.storage.output_dir
        self.storage.output_dir = Path('/invalid/path/that/does/not/exist')
        
        # 인덱스 저장 시도 (오류가 발생하지만 예외를 던지지 않음)
        self.storage._save_document_index()
        
        # 경로 복원
        self.storage.output_dir = original_output
    
    def test_load_document_index_error(self):
        """문서 인덱스 로드 중 오류 테스트"""
        # 잘못된 JSON 파일 생성
        index_file = os.path.join(OUTPUT_DIR, 'document_index.json')
        with open(index_file, 'w') as f:
            f.write('invalid json content')
        
        # 새 StorageManager 인스턴스 생성 (인덱스 로드 시도)
        new_storage = self.storage.__class__(
            input_dir=INPUT_DIR,
            output_dir=OUTPUT_DIR,
            document_processor=self.mock_processor
        )
        
        # 빈 인덱스로 초기화되어야 함
        self.assertEqual(len(new_storage.document_index), 0)
    
    def test_batch_processor_methods(self):
        """배치 프로세서 관련 메서드 테스트"""
        # 배치 작업 제출
        file_paths = ['/path/to/file1.pdf', '/path/to/file2.pdf']
        job_id = self.storage.process_batch(file_paths)
        self.assertIsNotNone(job_id)
        
        # 배치 작업 상태 조회
        status = self.storage.get_batch_status(job_id)
        self.assertIsNotNone(status)
        
        # 배치 작업 목록 조회
        jobs = self.storage.list_batch_jobs()
        self.assertIsInstance(jobs, list)
        
        # 특정 상태로 필터링
        pending_jobs = self.storage.list_batch_jobs('pending')
        self.assertIsInstance(pending_jobs, list)
    
    def test_monitoring_already_running(self):
        """모니터링이 이미 실행 중일 때 테스트"""
        # 모니터링 시작
        self.storage.start_monitoring()
        
        # 다시 시작 시도
        self.storage.start_monitoring()  # 경고 로그만 출력되고 정상 동작
        
        # 모니터링 중지
        self.storage.stop_monitoring()
    
    def test_process_new_document_json_string(self):
        """문서 처리기가 JSON 문자열을 반환하는 경우 테스트"""
        # JSON 문자열 반환 설정
        json_doc = {
            'id': 'json_doc',
            'content': 'JSON document content',
            'format': 'pdf'
        }
        self.mock_processor.process_document.return_value = json.dumps(json_doc)
        
        test_file = os.path.join(INPUT_DIR, 'test_json.pdf')
        with open(test_file, 'w') as f:
            f.write('테스트 파일')
        
        result = self.storage.process_new_document(test_file)
        self.assertIsNotNone(result)
    
    def test_process_new_document_unexpected_type(self):
        """문서 처리기가 예상치 못한 타입을 반환하는 경우"""
        # 리스트 반환 (예상치 못한 타입)
        self.mock_processor.process_document.return_value = ['unexpected', 'list']
        
        test_file = os.path.join(INPUT_DIR, 'test_unexpected.pdf')
        with open(test_file, 'w') as f:
            f.write('테스트 파일')
        
        result = self.storage.process_new_document(test_file)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
