#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Docling 결과 객체의 구조를 검사하는 스크립트
"""

import os
import sys
import argparse
import logging
import inspect
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inspect_docling_result(input_file):
    """
    Docling 결과 객체의 구조 검사
    """
    try:
        from docling.document_converter import DocumentConverter
        logger.info(f"Docling 라이브러리 import 성공")
    except ImportError as e:
        logger.error(f"Docling 라이브러리를 import 할 수 없습니다: {e}")
        return False
        
    try:
        # Docling DocumentConverter 인스턴스 생성
        converter = DocumentConverter()
        
        # 변환 실행
        logger.info(f"파일 '{input_file}' 변환 중...")
        result = converter.convert(input_file)
        
        # 결과 객체 탐색
        logger.info(f"결과 객체 타입: {type(result)}")
        logger.info(f"결과 객체 속성: {dir(result)}")
        
        # document 객체 탐색
        docling_doc = result.document
        logger.info(f"Document 객체 타입: {type(docling_doc)}")
        logger.info(f"Document 객체 속성: {dir(docling_doc)}")
        
        # 클래스 검사
        logger.info(f"Document 클래스 MRO: {type(docling_doc).__mro__}")
        
        # get_text 메서드가 있는지 확인
        if hasattr(docling_doc, 'get_text'):
            logger.info("get_text 메서드 발견! 호출 시도 중...")
            text = docling_doc.get_text()
            logger.info(f"텍스트 샘플: {text[:200] if text else 'None'}")
        
        # get_markdown 메서드가 있는지 확인
        if hasattr(docling_doc, 'get_markdown'):
            logger.info("get_markdown 메서드 발견! 호출 시도 중...")
            markdown = docling_doc.get_markdown()
            logger.info(f"마크다운 샘플: {markdown[:200] if markdown else 'None'}")
        
        # get_content 메서드가 있는지 확인
        if hasattr(docling_doc, 'get_content'):
            logger.info("get_content 메서드 발견! 호출 시도 중...")
            content = docling_doc.get_content()
            logger.info(f"내용 샘플: {str(content)[:200] if content else 'None'}")
            
        # content 속성이 있는지 확인
        if hasattr(docling_doc, 'content'):
            logger.info("content 속성 발견!")
            logger.info(f"내용 샘플: {str(docling_doc.content)[:200] if docling_doc.content else 'None'}")
            
        # sections 속성이 있는지 확인
        if hasattr(docling_doc, 'sections'):
            logger.info("sections 속성 발견!")
            sections = docling_doc.sections
            logger.info(f"섹션 수: {len(sections) if sections else 0}")
            if sections and len(sections) > 0:
                logger.info(f"첫 번째 섹션 내용: {str(sections[0])[:200]}")
                
        # pages 속성이 있는지 확인
        if hasattr(docling_doc, 'pages'):
            logger.info("pages 속성 발견!")
            pages = docling_doc.pages
            logger.info(f"페이지 수: {len(pages) if pages else 0}")
            if pages and len(pages) > 0:
                logger.info(f"첫 번째 페이지 속성: {dir(pages[0])}")
                # 페이지의 텍스트 확인
                if hasattr(pages[0], 'text'):
                    logger.info(f"첫 번째 페이지 텍스트 샘플: {pages[0].text[:200] if pages[0].text else 'None'}")
                    
        return True
    except Exception as e:
        logger.exception(f"검사 중 오류 발생: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Docling 결과 객체 검사")
    parser.add_argument("input_file", help="처리할 PDF 파일 경로")
    
    args = parser.parse_args()
    
    success = inspect_docling_result(args.input_file)
    if success:
        logger.info("검사 완료")
        return 0
    else:
        logger.error("검사 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())
