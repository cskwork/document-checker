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
            'content': '테스트 문서 내용',
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


if __name__ == '__main__':
    unittest.main()
