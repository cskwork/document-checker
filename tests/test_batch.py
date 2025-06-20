"""
배치 처리 테스트 스크립트
"""

import os
import sys
from pathlib import Path
from src.storage_manager.manager import StorageManager
from src.document_processor.processor import DocumentProcessor

def test_batch_processing():
    # 기본 디렉토리 설정
    base_dir = Path(__file__).parent
    input_dir = base_dir / 'input'
    output_dir = base_dir / 'output'
    
    # 입력 디렉토리가 없으면 생성
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # 입력 디렉토리에서 파일 목록 가져오기
    file_paths = [str(f.absolute()) for f in input_dir.iterdir() if f.is_file()]
    
    if not file_paths:
        print("입력 디렉토리에 파일이 없습니다.")
        # 테스트 파일 생성
        test_file = input_dir / 'test_document.txt'
        test_file.write_text('This is a test document for batch processing.')
        file_paths = [str(test_file.absolute())]
    
    print(f"처리할 파일 목록: {file_paths}")
    
    # 컴포넌트 초기화
    document_processor = DocumentProcessor()
    storage_manager = StorageManager(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        document_processor=document_processor
    )
    
    # 배치 처리 시작
    job_id = storage_manager.process_batch(file_paths)
    print(f"배치 작업 ID: {job_id}")
    
    # 작업 상태 확인
    status = storage_manager.get_batch_status(job_id)
    print(f"초기 작업 상태: {status}")
    
    # 출력 디렉토리 확인
    print("\n처리된 문서 목록:")
    documents = storage_manager.list_documents()
    for doc in documents:
        print(f"- ID: {doc['id']}, 파일명: {doc['filename']}, 상태: {doc.get('processingStatus', '알 수 없음')}")
    
    # 테스트 검증 추가
    assert job_id is not None, "배치 작업 ID가 생성되어야 합니다"
    assert status is not None, "배치 작업 상태를 가져올 수 있어야 합니다"
    assert len(documents) > 0, "처리된 문서가 최소 1개 이상 있어야 합니다"

if __name__ == "__main__":
    test_batch_processing()
    
    # 배치 작업 목록 확인
    print("\n모든 배치 작업 목록:")
    from src.storage_manager.batch_processor import get_batch_processor
    batch_processor = get_batch_processor()
    jobs = batch_processor.list_jobs()
    for job in jobs:
        print(f"- ID: {job['job_id']}, 상태: {job['status']}, 진행률: {job['progress']:.2f}, "
              f"파일 수: {job['total_files']}")
