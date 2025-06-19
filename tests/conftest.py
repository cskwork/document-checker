"""
테스트 설정 파일

이 파일은 pytest 테스트 실행 시 자동으로 로드되어 테스트 환경을 설정합니다.
"""

import sys
import os
from pathlib import Path

# 테스트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# 모의 모듈을 sys.modules에 추가하여 임포트 시 사용되도록 함
import tests.mocks.docling as docling_mock
import sys
sys.modules['docling'] = docling_mock

# 테스트에 필요한 환경 변수 설정
os.environ['TESTING'] = 'True'
