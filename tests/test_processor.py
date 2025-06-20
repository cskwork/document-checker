"""
문서 처리기 테스트 스크립트

이 스크립트는 수정된 DocumentProcessor 클래스를 테스트합니다.
"""

import os
import sys
from pathlib import Path
from src.document_processor.processor import DocumentProcessor

def test_processor():
    # 테스트 파일 경로
    test_files = [
        "/Users/danny/Documents/document-checker/input/test_section.txt",
        "/Users/danny/Documents/document-checker/input/test1.txt",
        "/Users/danny/Documents/document-checker/input/test2.txt"
    ]
    
    # DocumentProcessor 초기화
    processor = DocumentProcessor()
    
    # 각 파일에 대해 테스트
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"파일을 찾을 수 없습니다: {file_path}")
            continue
            
        print(f"\n{'='*50}")
        print(f"파일 처리 중: {file_path}")
        print(f"{'='*50}")
        
        try:
            # 문서 처리
            result = processor.process_document(file_path)
            
            # 결과 출력
            print(f"문서 ID: {result['id']}")
            print(f"파일명: {result['filename']}")
            print(f"형식: {result['format']}")
            print(f"처리 상태: {result['processingStatus']}")
            print(f"생성일: {result['createdAt']}")
            
            # 내용 요약
            content = result['content']
            print(f"\n텍스트 길이: {len(content['text'])}자")
            print(f"추출된 섹션 수: {len(content['sections']) if 'sections' in content else 0}")
            print(f"메타데이터: {content['metadata']}")
            
            # 섹션 미리보기
            if 'sections' in content and content['sections']:
                print("\n섹션 미리보기:")
                for i, section in enumerate(content['sections'][:3]):  # 처음 3개 섹션만 표시
                    title = section.get('title', '제목 없음')
                    preview = section.get('content', '').replace('\n', ' ').strip()
                    print(f"  {i+1}. [{title}] {preview[:100]}...")
            
        except Exception as e:
            print(f"처리 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_processor()
