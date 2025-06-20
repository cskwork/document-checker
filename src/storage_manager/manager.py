"""
Storage Manager Module

이 모듈은 문서의 저장, 검색, 파일 시스템 모니터링 및 배치 처리를 관리하는 저장소 관리자 컴포넌트를 제공합니다.
"""

import os
import json
import time
import logging
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 배치 프로세서 임포트
from .batch_processor import BatchProcessor, init_batch_processor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageManager:
    """
    문서 저장소를 관리하는 클래스입니다.
    
    이 클래스는 문서의 저장, 검색, 파일 시스템 모니터링 및 배치 처리를 담당합니다.
    """
    
    def __init__(self, input_dir: str, output_dir: str, document_processor: Any, num_workers: int = 2):
        """
        StorageManager 초기화
        
        Args:
            input_dir (str): 입력 디렉토리 경로
            output_dir (str): 출력 디렉토리 경로
            document_processor: 문서 처리기 인스턴스
            num_workers (int): 배치 처리에 사용할 작업자 수 (기본값: 2)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.document_processor = document_processor
        self.document_index: Dict[str, Dict] = {}
        self.cache: Dict[str, Any] = {}
        self.observer: Optional[Observer] = None
        
        # 디렉토리 생성
        self._setup_directories()
        
        # 기존 문서 인덱스 로드
        self._load_document_index()
        
        # 배치 프로세서 초기화
        self.batch_processor = init_batch_processor(self, num_workers=num_workers)
    
    def _setup_directories(self) -> None:
        """필요한 디렉토리 구조를 생성합니다."""
        try:
            self.input_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / 'documents').mkdir(exist_ok=True)
            logger.info(f"디렉토리 설정 완료: 입력 디렉토리={self.input_dir}, 출력 디렉토리={self.output_dir}")
        except Exception as e:
            logger.error(f"디렉토리 설정 중 오류 발생: {e}")
            raise
    
    def _load_document_index(self) -> None:
        """저장된 문서 인덱스를 로드합니다."""
        index_file = self.output_dir / 'document_index.json'
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.document_index = json.load(f)
                logger.info(f"문서 인덱스 로드 완료: 총 {len(self.document_index)}개 문서")
            except Exception as e:
                logger.error(f"문서 인덱스 로드 중 오류: {e}")
                self.document_index = {}
    
    def _save_document_index(self) -> None:
        """문서 인덱스를 파일에 저장합니다."""
        index_file = self.output_dir / 'document_index.json'
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"문서 인덱스 저장 중 오류: {e}")
    
    # 배치 처리 관련 메서드
    
    def process_batch(self, file_paths: List[str], callback: Optional[Callable] = None) -> str:
        """문서 배치 처리를 시작합니다.
        
        Args:
            file_paths (List[str]): 처리할 파일 경로 목록
            callback (Optional[Callable]): 배치 처리 완료 시 호출될 콜백 함수
            
        Returns:
            str: 배치 작업 ID
        """
        return self.batch_processor.submit_job(file_paths, callback)
    
    def get_batch_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """배치 작업 상태를 조회합니다.
        
        Args:
            job_id (str): 조회할 작업 ID
            
        Returns:
            Optional[Dict[str, Any]]: 작업 상태 정보 (없는 경우 None)
        """
        return self.batch_processor.get_batch_status(job_id)
    
    def list_batch_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """배치 작업 목록을 조회합니다.
        
        Args:
            status (Optional[str]): 필터링할 작업 상태 (None이면 모든 작업 반환)
            
        Returns:
            List[Dict[str, Any]]: 작업 목록
        """
        return self.batch_processor.list_jobs(status)
    
    def save_document_index(self) -> None:
        """문서 인덱스를 파일에 저장합니다. (외부에서 호출 가능하도록 공개 메서드로 추가)"""
        self._save_document_index()
    
    def start_monitoring(self) -> None:
        """입력 디렉토리 모니터링을 시작합니다."""
        if self.observer and self.observer.is_alive():
            logger.warning("이미 모니터링이 실행 중입니다.")
            return
            
        event_handler = DocumentEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.input_dir), recursive=True)
        self.observer.start()
        logger.info(f"파일 모니터링 시작: {self.input_dir}")
        
        # 배치 프로세서 시작 (이미 시작되어 있을 수 있음)
        try:
            self.batch_processor.start()
        except Exception as e:
            logger.error(f"배치 프로세서 시작 중 오류: {e}")
    
    def stop_monitoring(self) -> None:
        """입력 디렉토리 모니터링을 중지합니다."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("파일 모니터링 중지")
        
        # 배치 프로세서 정지
        try:
            self.batch_processor.stop()
        except Exception as e:
            logger.error(f"배치 프로세서 정지 중 오류: {e}")
    
    def process_new_document(self, file_path: str, batch_mode: bool = False) -> Optional[str]:
        """새 문서를 처리하고 저장합니다.
        
        Args:
            file_path (str): 처리할 문서 파일 경로
            batch_mode (bool): 배치 모드 여부 (True인 경우 일부 로깅 생략)
            
        Returns:
            Optional[str]: 문서 ID (실패 시 None)
        """
        try:
            # 로깅: 문서 처리 시작
            logger.info(f"[process_new_document] 문서 처리 시작: {file_path}")
            
            # 파일 존재 여부 검사
            if not os.path.exists(file_path):
                logger.error(f"[process_new_document] 파일이 존재하지 않습니다: {file_path}")
                return None
                
            # 로그: 파일 크기
            try:
                file_size = os.path.getsize(file_path)
                logger.info(f"[process_new_document] 파일 크기: {file_size} bytes")
            except Exception as e:
                logger.warning(f"[process_new_document] 파일 크기 확인 중 오류: {e}")
                
            # 문서 처리
            logger.info(f"[process_new_document] 문서 처리기 호출: document_processor.process_document({file_path})")
            doc_model = self.document_processor.process_document(file_path)
            
            # 문서 처리 결과 로깅
            if doc_model:
                # doc_model이 문자열인 경우 처리
                if isinstance(doc_model, str):
                    try:
                        # JSON 문자열인지 시도
                        import json
                        doc_model = json.loads(doc_model)
                        logger.info("[process_new_document] JSON 문자열을 파싱하여 문서 모델로 변환했습니다.")
                    except json.JSONDecodeError:
                        # JSON이 아니면 단순 문자열로 처리
                        logger.warning("문서 모델이 문자열로 반환되었습니다. 기본 문서 모델을 생성합니다.")
                        doc_model = {
                            'id': str(uuid.uuid4()),
                            'filename': os.path.basename(file_path),
                            'format': os.path.splitext(file_path)[1].lstrip('.').lower(),
                            'content': {'text': str(doc_model)},
                            'processingStatus': 'processed',
                            'createdAt': datetime.datetime.now().isoformat(),
                            'lastModified': datetime.datetime.now().isoformat()
                        }
                elif not isinstance(doc_model, dict):
                    logger.error(f"예상치 못한 문서 모델 타입: {type(doc_model)}")
                    return None
                    
                logger.info(f"[process_new_document] 문서 처리 성공: model={doc_model.get('id')}")
                
                # 처리 내용 디버그 로깅
                content_sample = ''
                if isinstance(doc_model.get('content'), dict):
                    content_sample = str(doc_model.get('content', {}).get('text', ''))[:100]
                else:
                    content_sample = str(doc_model.get('content', ''))[:100]
                    
                logger.info(f"[process_new_document] 문서 내용 샘플: {content_sample}...")
            else:
                logger.error(f"[process_new_document] 문서 처리 실패 (doc_model is None): {file_path}")
                return None

            # 처리 상태 확인
            if doc_model.get('processingStatus') == 'error':
                error_message = doc_model.get('error', 'Unknown error')
                logger.error(f"[process_new_document] 문서 처리 오류: {file_path}, 오류: {error_message}")
                return None
        
            # 문서 저장
            doc_id = doc_model.get('id')
            if not doc_id:
                logger.error(f"[process_new_document] 문서 ID가 없습니다: {file_path}")
                return None
            
            # 문서 저장 경로 로깅
            doc_path = self._get_document_path(doc_id)
            logger.info(f"[process_new_document] 문서 저장 경로: {doc_path}")
            
            # 저장 시도
            logger.info(f"[process_new_document] 문서 저장 시작: ID={doc_id}")
            storage_result = self.store_document(doc_model)
            
            if not storage_result:
                logger.error(f"[process_new_document] 문서 저장 실패: ID={doc_id}")
                return None
            
            logger.info(f"[process_new_document] 문서 저장 성공: ID={doc_id}")
            
            # 인덱스 업데이트
            self.document_index[doc_id] = {
                'id': doc_id,
                'filename': os.path.basename(file_path),
                'format': doc_model.get('format', 'unknown'),
                'createdAt': doc_model.get('createdAt', time.time()),
                'path': str(self._get_document_path(doc_id))
            }
            
            # 인덱스 저장 (배치 모드에서는 마지막에 한 번만 저장)
            if not batch_mode:
                logger.info(f"[process_new_document] 문서 인덱스 저장 시작")
                self._save_document_index()
                logger.info(f"[process_new_document] 문서 인덱스 저장 완료")
            
            logger.info(f"[process_new_document] 새 문서 처리 완료: ID={doc_id}, 파일={file_path}")
            return doc_id
            
        except Exception as e:
            if not batch_mode:
                logger.error(f"문서 처리 중 오류 발생: {file_path}, 오류: {e}")
            raise  # 배치 프로세서에서 오류 처리를 위해 예외를 다시 던짐
    
    def store_document(self, doc_model: Dict) -> bool:
        """문서를 디스크에 저장합니다.
        
        Args:
            doc_model (Dict): 저장할 문서 모델
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            doc_id = doc_model.get('id')
            if not doc_id:
                logger.error("[store_document] 문서 ID가 없습니다.")
                return False
                
            doc_path = self._get_document_path(doc_id)
            logger.info(f"[store_document] 문서 저장 경로: {doc_path}")
            
            # 디렉토리 경로 확인 및 생성
            dir_path = os.path.dirname(doc_path)
            logger.info(f"[store_document] 디렉토리 경로: {dir_path}")
            
            # 디렉토리 존재 여부 확인
            if not os.path.exists(dir_path):
                logger.info(f"[store_document] 디렉토리가 존재하지 않아 생성합니다: {dir_path}")
            
            # 디렉토리 생성
            os.makedirs(dir_path, exist_ok=True)
            
            # 디렉토리 권한 및 존재 여부 재확인
            if not os.path.exists(dir_path):
                logger.error(f"[store_document] 디렉토리 생성 실패: {dir_path}")
                return False
                
            logger.info(f"[store_document] 디렉토리 존재 확인됨, 쓰기 권한 확인 중: {dir_path}")
            
            # 쓰기 권한 확인
            if not os.access(dir_path, os.W_OK):
                logger.error(f"[store_document] 디렉토리에 쓰기 권한이 없습니다: {dir_path}")
                return False
            
            # 파일 저장
            logger.info(f"[store_document] 문서 파일 저장 시작: {doc_path}")
            try:
                with open(doc_path, 'w', encoding='utf-8') as f:
                    json.dump(doc_model, f, ensure_ascii=False, indent=2)
                logger.info(f"[store_document] 문서 파일 저장 성공: {doc_path}")
            except Exception as file_e:
                logger.error(f"[store_document] 파일 쓰기 중 오류: {file_e}", exc_info=True)
                return False
            
            # 파일 존재 여부 확인
            if not os.path.exists(doc_path):
                logger.error(f"[store_document] 파일 저장 후에도 파일이 존재하지 않습니다: {doc_path}")
                return False
            
            # 캐시 업데이트
            self.cache[doc_id] = doc_model
            
            logger.info(f"[store_document] 문서 저장 완료: ID={doc_id}, 경로={doc_path}")
            return True
            
        except Exception as e:
            logger.error(f"[store_document] 문서 저장 중 오류 발생: {e}", exc_info=True)
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """문서 ID로 문서를 조회합니다.
        
        Args:
            doc_id (str): 조회할 문서 ID
            
        Returns:
            Optional[Dict]: 문서 모델 (없는 경우 None)
        """
        # 캐시에서 조회
        if doc_id in self.cache:
            logger.debug(f"캐시에서 문서 조회: ID={doc_id}")
            return self.cache[doc_id]
        
        # 디스크에서 조회
        doc_path = self._get_document_path(doc_id)
        if os.path.exists(doc_path):
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    doc_model = json.load(f)
                    self.cache[doc_id] = doc_model  # 캐시에 저장
                    logger.debug(f"디스크에서 문서 조회: ID={doc_id}")
                    return doc_model
            except Exception as e:
                logger.error(f"문서 로드 중 오류: {doc_id}, 오류: {e}")
        
        logger.warning(f"문서를 찾을 수 없음: ID={doc_id}")
        return None
    
    def list_documents(self, filters: Optional[Dict] = None) -> List[Dict]:
        """문서 목록을 조회합니다.
        
        Args:
            filters (Optional[Dict]): 필터 조건
                - format: 문서 형식 필터
                
        Returns:
            List[Dict]: 문서 목록
        """
        documents = list(self.document_index.values())
        
        if not filters:
            return documents
            
        # 형식 필터링
        if 'format' in filters and filters['format']:
            documents = [d for d in documents if d.get('format') == filters['format']]
            
        # 생성일 필터링 (예시: 최근 7일 이내)
        if 'days' in filters and isinstance(filters['days'], int):
            time_threshold = time.time() - (filters['days'] * 24 * 60 * 60)
            documents = [d for d in documents if d.get('createdAt', 0) >= time_threshold]
            
        return documents

    def get_document_metadata(self, doc_id: str) -> Optional[Dict]:
        """문서 ID로 문서의 메타데이터를 조회합니다.
        
        Args:
            doc_id (str): 조회할 문서 ID
            
        Returns:
            Optional[Dict]: 문서 메타데이터 (없는 경우 None)
        """
        return self.document_index.get(doc_id)
    
    def _get_document_path(self, doc_id: str) -> str:
        """문서 파일 경로를 생성합니다.
        
        Args:
            doc_id (str): 문서 ID
            
        Returns:
            str: 문서 파일 경로
        """
        return str(self.output_dir / 'documents' / f"{doc_id}.json")


class DocumentEventHandler(FileSystemEventHandler):
    """파일 시스템 이벤트 핸들러"""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self._processing = set()  # 처리 중인 파일 추적
        self.logger = logging.getLogger(__name__ + ".DocumentEventHandler") # 독립적인 로거 사용 가능
        self.logger.info("DocumentEventHandler 초기화됨")
    
    def on_created(self, event):
        """파일 생성 이벤트 처리"""
        self.logger.info(f"파일 시스템 이벤트 감지: {event.src_path}, is_directory={event.is_directory}") # 이벤트 감지 로그

        if event.is_directory:
            self.logger.debug(f"디렉토리 생성 이벤트는 무시: {event.src_path}")
            return
            
        file_path = event.src_path
        self.logger.info(f"파일 경로 디코딩: {file_path}")
        
        # 중복 처리 방지
        if file_path in self._processing:
            self.logger.debug(f"이미 처리 중인 파일: {file_path}")
            return
            
        # 지원하는 파일 형식 확인
        try:
            file_ext = os.path.splitext(file_path)[1].lower() # .pdf, .docx 등
            self.logger.info(f"파일 확장자: {file_ext}")
        except Exception as ext_e:
            self.logger.error(f"파일 확장자 추출 중 오류: {ext_e}")
            file_ext = ''
        
        # StorageManager가 document_processor를 통해 지원 형식을 알 수 있도록 해야 하지만, 우선 여기서 직접 정의
        supported_event_handler_formats = ['.pdf', '.docx', '.txt', '.doc'] # DocumentProcessor의 것과 동기화 필요
        
        if file_ext not in supported_event_handler_formats:
            self.logger.info(f"지원하지 않는 파일 형식({file_ext})이므로 처리하지 않음: {file_path}")
            return
            
        self.logger.info(f"새 파일 감지 및 처리 시작 예정: {file_path}")
        self._processing.add(file_path)
        
        try:
            # 파일이 완전히 쓰여질 때까지 대기 (네트워크 드라이브 등 고려 시 필요할 수 있음)
            # 실제 프로덕션에서는 더 견고한 파일 잠금/완료 확인 메커니즘이 필요할 수 있음
            time.sleep(1) # 짧은 대기
            
            # 파일이 여전히 존재하는지 확인
            if not os.path.exists(file_path):
                self.logger.warning(f"처리 전 파일 사라짐: {file_path}")
                return
              
            # 파일 크기 확인
            try:
                file_size = os.path.getsize(file_path)
                self.logger.info(f"파일 크기: {file_size} bytes")
                if file_size == 0:
                    self.logger.warning(f"파일 크기가 0입니다: {file_path}")
                    return
            except Exception as size_e:
                self.logger.error(f"파일 크기 확인 중 오류: {size_e}")
            
            # 파일 읽기 권한 확인
            if not os.access(file_path, os.R_OK):
                self.logger.error(f"파일에 읽기 권한이 없습니다: {file_path}")
                return
            
            self.logger.info(f"StorageManager.process_new_document 호출 예정: {file_path}")
            # 파일 처리 (단일 파일 처리)
            try:
                # 직접 파일을 처리하는 방식으로 변경
                doc_id = self.storage_manager.process_new_document(file_path, batch_mode=False)
                self.logger.info(f"문서 처리 완료: doc_id={doc_id}, 파일={file_path}")
            except Exception as proc_e:
                self.logger.error(f"process_new_document 호출 중 오류: {proc_e}", exc_info=True)
            
        except Exception as e:
            self.logger.error(f"파일 처리 중 DocumentEventHandler에서 오류 발생: {file_path}, 오류: {e}", exc_info=True)
            
        finally:
            # 처리 완료 후 추적에서 제거
            self._processing.discard(file_path)
            self.logger.debug(f"파일 처리 완료 (또는 실패 후 정리): {file_path}")
