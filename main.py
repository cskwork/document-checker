"""
문서 검사기 메인 애플리케이션

이 파일은 문서 검사기 애플리케이션의 진입점입니다.
모든 컴포넌트를 초기화하고 웹 서버를 시작합니다.
"""

import os
from pathlib import Path
from src.document_processor.processor import DocumentProcessor
from src.storage_manager.manager import StorageManager
from src.content_analyzer.analyzer import ContentAnalyzer
from src.report_generator.generator import ReportGenerator
from src.user_interface.app import app

def initialize_components():
    """
    모든 백엔드 컴포넌트를 초기화합니다.
    """
    # 기본 디렉토리 설정
    base_dir = Path(__file__).parent
    input_dir = base_dir / 'input'
    output_dir = base_dir / 'output'
    
    # 디렉토리 생성
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # 컴포넌트 초기화
    document_processor = DocumentProcessor()
    storage_manager = StorageManager(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        document_processor=document_processor
    )
    content_analyzer = ContentAnalyzer(storage_manager=storage_manager)
    report_generator = ReportGenerator(output_dir=str(output_dir), storage_manager=storage_manager)
    
    # 컴포넌트를 Flask 앱에 연결
    app.document_processor = document_processor
    app.storage_manager = storage_manager
    app.content_analyzer = content_analyzer
    app.report_generator = report_generator
    
    # 파일 모니터링 시작
    storage_manager.start_monitoring()
    
    return {
        'document_processor': document_processor,
        'storage_manager': storage_manager,
        'content_analyzer': content_analyzer,
        'report_generator': report_generator
    }

if __name__ == "__main__":
    # 컴포넌트 초기화
    components = initialize_components()
    
    # 초기화 상태 출력
    print("문서 검사기 백엔드 컴포넌트 초기화 완료:")
    for name, component in components.items():
        print(f"- {name}: {type(component).__name__} 초기화됨")
    
    # Flask 앱 실행
    app.run(debug=True, host='0.0.0.0', port=5002) # 포트를 5002로 변경
