"""
문서 처리기 모듈

이 모듈은 다양한 형식의 문서를 처리하고 표준화된 형식으로 변환하는 기능을 제공합니다.
"""

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    import logging
    logging.getLogger(__name__).error("docling 라이브러리를 가져올 수 없습니다. 설치되어 있는지 확인하세요.")
import os
import datetime
import uuid
import logging # 로깅 모듈 임포트

# 로거 설정
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

class DocumentProcessor:
    """
    다양한 형식의 문서를 처리하는 클래스
    
    이 클래스는 PDF, DOCX, TXT 형식의 문서를 처리하고,
    문서의 내용과 메타데이터를 추출하여 표준화된 형식으로 반환합니다.
    """
    def __init__(self, config=None):
        """
        DocumentProcessor 초기화
        
        Args:
            config (dict, optional): 처리기 설정. 기본값은 None입니다.
        """
        self.config = config or {}
        self.supported_formats = ['pdf', 'docx', 'txt', 'doc']
        self.text_extensions = ['txt', 'md', 'csv', 'json', 'xml', 'html', 'htm']
        self.binary_extensions = ['pdf', 'docx', 'doc', 'xlsx', 'pptx']
        self.section_headers = ['##', '###', '####', '제목', '개요', '목차', '1. ', '2. ', '3. ', 'I. ', 'II. ', 'III. ']  # 섹션 헤더로 사용될 패턴
    
    def process_document(self, file_path):
        """
        문서를 처리하고 문서 모델을 반환합니다.
        
        Args:
            file_path (str): 처리할 문서의 경로
            
        Returns:
            dict: 처리된 문서 정보를 담은 딕셔너리
        """
        file_ext = os.path.splitext(file_path)[1].lower().replace('.', '') # 예외 발생 시 사용 위해 미리 정의
        try:
            # 파일 확장자 추출 및 지원 여부 확인
            # file_ext = os.path.splitext(file_path)[1].lower().replace('.', '') # 위로 이동
            if file_ext not in self.supported_formats:
                logger.error(f"지원하지 않는 파일 형식입니다: {file_ext} (경로: {file_path})") # 로그 추가
                raise ValueError(f"지원하지 않는 파일 형식입니다: {file_ext}")
            
            logger.info(f"'{file_path}' 문서 처리 시작...") # 로깅 추가
            
            # 텍스트 파일 처리
            if file_ext in self.text_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        doc_text = f.read()
                    
                    # 섹션 추출
                    sections = self._extract_sections_from_text(doc_text)
                    
                    return {
                        'id': str(uuid.uuid4()),
                        'filename': os.path.basename(file_path),
                        'format': file_ext,
                        'content': {
                            'text': doc_text,
                            'sections': sections,
                            'metadata': {
                                'file_size': os.path.getsize(file_path),
                                'created': datetime.datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                                'modified': datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                            }
                        },
                        'processingStatus': 'processed',
                        'createdAt': datetime.datetime.now().isoformat(),
                        'lastModified': datetime.datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"텍스트 파일 처리 중 오류: {str(e)}", exc_info=True)
                    raise
            
            # 바이너리 파일(PDF, DOCX 등) 처리
            elif file_ext in self.binary_extensions:
                # docling 라이브러리 사용 가능 여부 확인
                if not DOCLING_AVAILABLE:
                    logger.error("docling 라이브러리를 사용할 수 없어 문서를 처리할 수 없습니다.")
                    raise ImportError("docling 라이브러리를 사용할 수 없습니다.")
                    
                try:
                    # docling을 사용하여 문서 파싱
                    logger.info(f"DocumentConverter 인스턴스 생성 중...")
                    converter = DocumentConverter()
                    logger.info(f"'{file_path}' 변환 시작...")
                    result = converter.convert(file_path)
                    logger.info(f"변환 완료, document 객체 접근 중...")
                    docling_doc = result.document
                    logger.info(f"document 객체 접근 성공: {type(docling_doc)}")
                except Exception as e:
                    logger.error(f"docling을 사용한 문서 변환 중 오류: {str(e)}", exc_info=True)
                    raise
            
            # --- 로깅 추가 시작 ---
            extracted_text_sample = docling_doc.text[:200] if hasattr(docling_doc, 'text') and docling_doc.text else "텍스트 없음"
            logger.info(f"Docling 변환 결과: 문서 ID (내부) = {getattr(docling_doc, 'id', 'ID 없음')}, 추출된 텍스트 (앞 200자) = '{extracted_text_sample}'")
            if not (hasattr(docling_doc, 'text') and docling_doc.text):
                logger.warning(f"Docling이 '{file_path}' 파일에서 텍스트를 추출하지 못했습니다.")
            # --- 로깅 추가 끝 ---

            # 문서 모델 생성
            doc_text = ''
            sections = []
            metadata = {}
            
            # 1. export_to_markdown 사용 시도
            if hasattr(docling_doc, 'export_to_markdown'):
                try:
                    doc_text = docling_doc.export_to_markdown()
                    logger.info(f"export_to_markdown()로 문서 마크다운 추출 성공: 길이={len(doc_text)} 문자")
                    sections = self._extract_sections_from_markdown(doc_text)
                except Exception as md_e:
                    logger.error(f"export_to_markdown() 호출 중 오류: {str(md_e)}", exc_info=True)
            
            # 2. export_to_text 사용 시도
            if not doc_text and hasattr(docling_doc, 'export_to_text'):
                try:
                    doc_text = docling_doc.export_to_text()
                    logger.info(f"export_to_text()로 문서 텍스트 추출 성공: 길이={len(doc_text)} 문자")
                    sections = self._extract_sections_from_text(doc_text)
                except Exception as e:
                    logger.error(f"export_to_text() 호출 중 오류: {str(e)}", exc_info=True)
            
            # 메타데이터 추출
            metadata = self._extract_metadata(docling_doc, file_path)
            
            # 섹션과 메타데이터 추출 중 오류 방지
            try:
                sections = self._extract_sections(docling_doc)
                logger.info(f"섹션 추출 완료: {len(sections)}개 섹션")
            except Exception as sec_e:
                logger.error(f"섹션 추출 중 오류: {str(sec_e)}")
                sections = []
                
            try:
                metadata = self._extract_metadata(docling_doc, file_path)
                logger.info(f"메타데이터 추출 완료: {len(metadata)}개 항목")
            except Exception as meta_e:
                logger.error(f"메타데이터 추출 중 오류: {str(meta_e)}")
                metadata = {}
            
            doc_model = {
                'id': str(uuid.uuid4()),
                'filename': os.path.basename(file_path),
                'format': file_ext,
                'content': {
                    'text': doc_text,
                    'sections': sections,
                    'metadata': metadata
                },
                'processingStatus': 'processed',
                'createdAt': datetime.datetime.now().isoformat(),
                'lastModified': datetime.datetime.now().isoformat()
            }
            
            logger.info(f"'{file_path}' 문서 처리 완료. 생성된 ID: {doc_model['id']}") # 로깅 추가
            return doc_model
            
        except Exception as e:
            logger.error(f"'{file_path}' 문서 처리 중 심각한 오류 발생: {e}", exc_info=True) # exc_info=True로 스택 트레이스 포함
            # 오류 처리
            return {
                'id': str(uuid.uuid4()),
                'filename': os.path.basename(file_path),
                'format': file_ext, # file_ext는 try 블록 시작 시 정의됨
                'processingStatus': 'error',
                'error': str(e),
                'createdAt': datetime.datetime.now().isoformat(),
                'lastModified': datetime.datetime.now().isoformat()
            }
    
    def _extract_sections(self, docling_doc):
        """
        문서에서 섹션을 추출합니다.
        
        Args:
            docling_doc: docling Document 객체
            
        Returns:
            list: 문서 섹션 목록
        """
        sections = []
        try:
            if hasattr(docling_doc, 'sections') and docling_doc.sections:
                for section in docling_doc.sections:
                    sections.append({
                        'title': getattr(section, 'title', '제목 없음'),
                        'content': getattr(section, 'text', '')
                    })
        except Exception as e:
            logger.error(f"섹션 추출 중 오류: {str(e)}")
        
        return sections
    
    def _extract_sections_from_text(self, text: str) -> list:
        """
        일반 텍스트에서 섹션을 추출합니다.
        
        Args:
            text (str): 추출할 텍스트
            
        Returns:
            list: 섹션 목록
        """
        sections = []
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 섹션 헤더 감지
            is_section = any(line.startswith(header) for header in self.section_headers)
            
            if is_section:
                if current_section:
                    sections.append(current_section)
                current_section = {'title': line, 'content': ''}
            elif current_section:
                current_section['content'] += line + '\n'
        
        # 마지막 섹션 추가
        if current_section:
            sections.append(current_section)
            
        return sections
    
    def _extract_sections_from_markdown(self, markdown: str) -> list:
        """
        마크다운 텍스트에서 섹션을 추출합니다.
        
        Args:
            markdown (str): 마크다운 형식의 텍스트
            
        Returns:
            list: 섹션 목록
        """
        sections = []
        lines = markdown.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 마크다운 헤더 감지 (##, ###, #### 등)
            if line.startswith('#'):
                if current_section:
                    sections.append(current_section)
                current_section = {'title': line.lstrip('#').strip(), 'content': ''}
            elif current_section:
                current_section['content'] += line + '\n'
        
        # 마지막 섹션 추가
        if current_section:
            sections.append(current_section)
            
        return sections
    
    def _extract_metadata(self, docling_doc, file_path: str) -> dict:
        """
        문서에서 메타데이터를 추출합니다.
        
        Args:
            docling_doc: docling 문서 객체
            file_path (str): 파일 경로
            
        Returns:
            dict: 추출된 메타데이터
        """
        metadata = {}
        
        try:
            # 파일 시스템 메타데이터
            metadata.update({
                'file_size': os.path.getsize(file_path),
                'created': datetime.datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                'modified': datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                'file_type': os.path.splitext(file_path)[1].lower().replace('.', '')
            })
            
            # docling 문서에서 메타데이터 추출
            if hasattr(docling_doc, 'metadata') and isinstance(docling_doc.metadata, dict):
                metadata.update(docling_doc.metadata)
                
            # 문서 속성에서 추가 메타데이터 추출
            doc_attrs = ['title', 'author', 'subject', 'keywords', 'creator', 'producer', 'creation_date', 'modification_date']
            for attr in doc_attrs:
                if hasattr(docling_doc, attr):
                    value = getattr(docling_doc, attr)
                    if value:
                        metadata[attr] = value
                        
        except Exception as e:
            logger.error(f"메타데이터 추출 중 오류: {str(e)}", exc_info=True)
            
        return metadata
