"""
테스트를 위한 docling 모듈 모의 구현
"""

class Document:
    """문서 클래스 모의 구현"""
    
    def __init__(self, content=None, **kwargs):
        """문서 초기화"""
        self.content = content or ""
        self.metadata = kwargs
        # DocumentProcessor에서 사용하는 속성 추가
        self.text = self.content  # content와 동일한 값 사용
    
    def to_dict(self):
        """문서를 딕셔너리로 변환"""
        return {
            'content': self.content,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_file(cls, file_path, **kwargs):
        """파일에서 문서 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return cls(content=content, **kwargs)
        except Exception as e:
            raise Exception(f"파일을 로드하는 중 오류 발생: {e}")
    
    def save(self, file_path):
        """문서를 파일로 저장"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.content)
            return True
        except Exception as e:
            raise Exception(f"파일을 저장하는 중 오류 발생: {e}")
            
    def get_sections(self):
        """문서의 섹션 목록을 반환 (DocumentProcessor 호환용)"""
        # 테스트용으로 간단히 빈 리스트 반환
        return []


class PDFDocument(Document):
    """PDF 문서 클래스 모의 구현"""
    
    @classmethod
    def from_file(cls, file_path, **kwargs):
        """PDF 파일에서 문서 로드"""
        # 간단한 PDF 헤더 확인
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                raise ValueError("유효한 PDF 파일이 아닙니다.")
        
        # 테스트용으로 간단한 내용 반환
        return cls(content="PDF 문서 내용", format='pdf', **kwargs)


class WordDocument(Document):
    """워드 문서 클래스 모의 구현"""
    
    @classmethod
    def from_file(cls, file_path, **kwargs):
        """워드 파일에서 문서 로드"""
        # 확장자 확인
        ext = file_path.lower().split('.')[-1]
        if ext not in ['docx', 'doc']:
            raise ValueError("지원하지 않는 파일 형식입니다.")
        
        # 테스트용으로 간단한 내용 반환
        return cls(content="워드 문서 내용", format=ext, **kwargs)

