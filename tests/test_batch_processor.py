"""
배치 프로세서 테스트 모듈

이 모듈은 배치 프로세서의 기능을 테스트합니다.
"""

import os
import time
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from src.storage_manager.manager import StorageManager

# DocumentProcessor 모의 클래스
class MockDocumentProcessor:
    """테스트용 문서 처리기 모의 클래스"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.supported_formats = ['pdf', 'docx', 'txt']
    
    def process_document(self, file_path):
        """문서 처리를 시뮬레이션합니다."""
        try:
            # 파일 확장자 추출
            file_ext = os.path.splitext(file_path)[1].lower().replace('.', '')
            
            # 지원하지 않는 형식인 경우 예외 발생
            if file_ext not in self.supported_formats:
                raise ValueError(f"지원하지 않는 파일 형식입니다: {file_ext}")
            
            # 파일이 존재하지 않는 경우 예외 발생 (테스트용)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
            # 테스트용 문서 모델 생성
            doc_id = f"doc_{uuid.uuid4().hex[:8]}"
            return {
                'id': doc_id,
                'filename': os.path.basename(file_path),
                'format': file_ext,
                'content': f'Content of {os.path.basename(file_path)}',
                'processingStatus': 'processed',
                'createdAt': time.time(),
                'lastModified': time.time()
            }
            
        except Exception as e:
            # 오류 발생 시 None 반환 (테스트용)
            return None


class TestBatchProcessor(unittest.TestCase):
    """배치 프로세서 테스트 클래스"""
    
    def setUp(self):
        """테스트 전 설정"""
        # 테스트용 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, 'input')
        self.output_dir = os.path.join(self.test_dir, 'output')
        
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 모의 문서 처리기 생성
        self.mock_processor = MockDocumentProcessor()
        
        # 저장소 관리자 초기화
        self.storage_manager = StorageManager(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            document_processor=self.mock_processor,
            num_workers=2  # 2개의 워커 스레드로 테스트
        )
        
        # 모니터링 시작
        self.storage_manager.start_monitoring()
    
    def tearDown(self):
        """테스트 후 정리"""
        # 저장소 관리자 정지
        self.storage_manager.stop_monitoring()
        
        # 임시 디렉토리 삭제
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_test_files(self, count: int, prefix: str = 'test', ext: str = 'txt'):
        """테스트용 파일 생성
        
        Args:
            count (int): 생성할 파일 수
            prefix (str): 파일명 접두사
            ext (str): 파일 확장자
            
        Returns:
            List[str]: 생성된 파일 경로 목록
        """
        file_paths = []
        for i in range(count):
            file_name = f"{prefix}_{i+1}.{ext}"
            file_path = os.path.join(self.input_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"This is a test file: {file_name}")
            file_paths.append(file_path)
        return file_paths
    
    def test_single_batch_job(self):
        """단일 배치 작업 테스트"""
        # 파일 시스템 감지에 의한 자동 처리를 방지하기 위해 모니터링 일시 중지
        self.storage_manager.stop_monitoring()
        
        try:
            # 테스트용 파일 생성
            test_files = self._create_test_files(3)
            
            # 배치 작업 제출
            job_id = self.storage_manager.process_batch(test_files)
            
            # 작업이 완료될 때까지 기다림
            # 파일을 처리하는 데 충분한 시간을 확보하기 위해 대기 시간 증가
            for i in range(30):  # 최대 30초 대기
                # 배치 프로세서에서 파일을 직접 처리하도록 함
                for file_path in test_files:
                    self.storage_manager.process_new_document(file_path)
                
                # 작업 상태 확인
                status = self.storage_manager.get_batch_status(job_id)
                print(f"[테스트] 작업 상태 확인 {i}: {status['status'] if status else 'None'}, job_id={job_id}")
                
                if status and status['status'] in ['completed', 'failed']:
                    print(f"[테스트] 작업 완료: {status}")
                    break
                time.sleep(1)
            
            # 검증
            self.assertIsNotNone(status)
            self.assertEqual(status['status'], 'completed')
            self.assertEqual(status['processed_files'], 3)
            self.assertEqual(status['failed_files'], 0)
            self.assertGreaterEqual(status['progress'], 1.0)
        finally:
            # 테스트 후 모니터링 재개
            self.storage_manager.start_monitoring()
    
    def test_batch_with_failures(self):
        """실패가 포함된 배치 작업 테스트"""
        # 테스트용 파일 생성 (일부는 실패하도록 유도)
        test_files = self._create_test_files(2)  # 성공할 파일
        fail_files = [
            os.path.join(self.input_dir, 'invalid_1.txt'),
            os.path.join(self.input_dir, 'invalid_2.txt')
        ]
        
        # 실패할 파일 생성 (내용 없이 빈 파일)
        for file_path in fail_files:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("")
        
        # 파일 시스템 감지에 의한 자동 처리를 방지하기 위해 모니터링 일시 중지
        self.storage_manager.stop_monitoring()
        
        try:
            # 모든 파일을 포함하여 배치 작업 제출
            all_files = test_files + fail_files
            job_id = self.storage_manager.process_batch(all_files)
            
            # 작업이 완료될 때까지 기다림
            for i in range(30):  # 최대 30초 대기
                # 배치 프로세서에서 파일을 직접 처리하도록 함
                for file_path in test_files:
                    self.storage_manager.process_new_document(file_path)
                
                # 작업 상태 확인
                status = self.storage_manager.get_batch_status(job_id)
                print(f"[테스트] 실패테스트 상태 확인 {i}: {status['status'] if status else 'None'}, job_id={job_id}")
                
                if status and status['status'] in ['completed', 'failed']:
                    print(f"[테스트] 실패테스트 작업 완료: {status}")
                    break
                time.sleep(1)
            
            # 검증
            self.assertIsNotNone(status)
            self.assertEqual(status['status'], 'completed')
            self.assertEqual(status['processed_files'], 2)  # 성공한 파일 수
            self.assertEqual(status['failed_files'], 2)     # 실패한 파일 수
        finally:
            # 테스트 후 모니터링 재개
            self.storage_manager.start_monitoring()
    
    def test_concurrent_batch_jobs(self):
        """동시에 여러 배치 작업 테스트"""
        # 파일 시스템 감지에 의한 자동 처리를 방지하기 위해 모니터링 일시 중지
        self.storage_manager.stop_monitoring()
        
        try:
            # 테스트용 파일 그룹 생성
            file_groups = [
                self._create_test_files(2, prefix=f'group1_{i}') for i in range(3)
            ]
            
            # 여러 배치 작업 제출
            job_ids = []
            for files in file_groups:
                job_id = self.storage_manager.process_batch(files)
                job_ids.append(job_id)
            
            # 모든 파일을 직접 처리하여 작업 완료를 지원
            all_files = [file for group in file_groups for file in group]
            for _ in range(3):  # 여러 번 처리하여 확실히 처리되도록 함
                for file_path in all_files:
                    self.storage_manager.process_new_document(file_path)
            
            # 모든 작업이 완료될 때까지 대기
            for job_id in job_ids:
                for i in range(30):  # 최대 30초 대기
                    status = self.storage_manager.get_batch_status(job_id)
                    print(f"[테스트] 동시작업 상태 확인 {i}: {status['status'] if status else 'None'}, job_id={job_id}")
                    
                    if status and status['status'] in ['completed', 'failed']:
                        print(f"[테스트] 동시작업 완료: {status}")
                        break
                    time.sleep(1)
                
                # 각 작업 검증
                self.assertEqual(status['status'], 'completed')
                self.assertEqual(status['processed_files'], 2)
                self.assertEqual(status['failed_files'], 0)
        finally:
            # 테스트 후 모니터링 재개
            self.storage_manager.start_monitoring()
    
    def test_list_batch_jobs(self):
        """배치 작업 목록 조회 테스트"""
        # 파일 시스템 감지에 의한 자동 처리를 방지하기 위해 모니터링 일시 중지
        self.storage_manager.stop_monitoring()
        
        try:
            # 초기 작업 목록 확인
            jobs = self.storage_manager.list_batch_jobs()
            initial_count = len(jobs)
            
            # 테스트용 파일 생성 및 배치 작업 제출
            test_files = self._create_test_files(1)
            job_id = self.storage_manager.process_batch(test_files)
            
            # 작업이 완료될 때까지 대기
            for i in range(30):  # 최대 30초 대기
                # 파일 직접 처리
                for file_path in test_files:
                    self.storage_manager.process_new_document(file_path)
                
                status = self.storage_manager.get_batch_status(job_id)
                print(f"[테스트] 목록테스트 상태 확인 {i}: {status['status'] if status else 'None'}, job_id={job_id}")
                
                if status and status['status'] in ['completed', 'failed']:
                    print(f"[테스트] 목록테스트 작업 완료: {status}")
                    break
                time.sleep(1)
            
            # 작업 목록 조회
            jobs = self.storage_manager.list_batch_jobs()
            self.assertGreaterEqual(len(jobs), initial_count + 1)
            
            # 특정 상태로 필터링하여 조회
            completed_jobs = self.storage_manager.list_batch_jobs(status='completed')
            print(f"[테스트] 완료된 작업 목록: {completed_jobs}")
            self.assertGreater(len(completed_jobs), 0)
            self.assertTrue(any(job['job_id'] == job_id for job in completed_jobs))
        finally:
            # 테스트 후 모니터링 재개
            self.storage_manager.start_monitoring()


if __name__ == '__main__':
    unittest.main()
