#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docling 라이브러리 테스트 스크립트
PDF 파일을 마크다운으로 변환하는 기능 테스트
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_docling_conversion(input_file, output_dir):
    """
    Docling을 사용하여 PDF 파일을 마크다운으로 변환
    """
    try:
        from docling.document_converter import DocumentConverter
        logger.info(f"Docling 라이브러리 import 성공")
    except ImportError as e:
        logger.error(f"Docling 라이브러리를 import 할 수 없습니다: {e}")
        return False
        
    if not os.path.exists(input_file):
        logger.error(f"입력 파일이 존재하지 않습니다: {input_file}")
        return False
        
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"입력 파일: {input_file} 처리 시작")
        file_size = os.path.getsize(input_file)
        logger.info(f"파일 크기: {file_size} 바이트")
        
        # Docling DocumentConverter 인스턴스 생성
        logger.info("DocumentConverter 인스턴스 생성 중...")
        converter = DocumentConverter()
        
        # 변환 실행
        logger.info(f"파일 변환 중...")
        result = converter.convert(input_file)
        
        logger.info(f"변환 완료, 결과 타입: {type(result)}")
        
        # document 객체 접근
        logger.info("document 객체 접근 중...")
        docling_doc = result.document
        logger.info(f"Document 객체 타입: {type(docling_doc)}")
        
        # 텍스트 추출
        if hasattr(docling_doc, 'text'):
            text_length = len(docling_doc.text) if docling_doc.text else 0
            logger.info(f"추출된 텍스트 길이: {text_length} 문자")
            
            # 텍스트 샘플 출력
            if text_length > 0:
                text_sample = docling_doc.text[:200] + "..." if text_length > 200 else docling_doc.text
                logger.info(f"텍스트 샘플: {text_sample}")
            else:
                logger.warning("추출된 텍스트가 없습니다.")
        else:
            logger.warning("Document 객체에 text 속성이 없습니다")
            
        # 메타데이터 추출
        if hasattr(docling_doc, 'metadata'):
            logger.info(f"메타데이터: {docling_doc.metadata}")
        else:
            logger.warning("Document 객체에 metadata 속성이 없습니다")
        
        # 출력 파일 생성
        output_path = os.path.join(output_dir, os.path.basename(input_file) + ".md")
        if hasattr(docling_doc, 'text') and docling_doc.text:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(docling_doc.text)
            logger.info(f"텍스트를 파일로 저장했습니다: {output_path}")
            logger.info(f"파일 크기: {os.path.getsize(output_path)} 바이트")
        else:
            logger.error("저장할 텍스트가 없습니다.")
            
        return True
    except Exception as e:
        logger.exception(f"Docling 처리 중 오류 발생: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Docling 라이브러리 테스트")
    parser.add_argument("input_file", help="처리할 PDF 파일 경로")
    parser.add_argument("--output-dir", default="output", help="출력 디렉토리 (기본값: output)")
    
    args = parser.parse_args()
    
    success = test_docling_conversion(args.input_file, args.output_dir)
    if success:
        logger.info("테스트 성공")
        return 0
    else:
        logger.error("테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())
