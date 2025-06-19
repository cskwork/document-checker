from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, send_from_directory
import os
import json
from pathlib import Path
import datetime

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Initialize other components (will be set by main application)
document_processor = None
storage_manager = None
content_analyzer = None
report_generator = None

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(Path(__file__).parent.parent.parent, 'input')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """메인 애플리케이션 페이지"""
    return render_template('index.html')

@app.route('/search')
def search_page():
    """검색 구성 페이지"""
    return render_template('search.html')

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """문서 목록을 반환하는 API 엔드포인트"""
    try:
        filters = request.args.to_dict()
        documents = storage_manager.list_documents(filters) if storage_manager else []
        return jsonify({
            'status': 'success',
            'data': documents
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """특정 문서를 조회하는 API 엔드포인트"""
    try:
        if not storage_manager:
            raise Exception("Storage manager not initialized")
            
        document = storage_manager.get_document(doc_id)
        if document:
            return jsonify({
                'status': 'success',
                'data': document
            })
        return jsonify({
            'status': 'error',
            'message': 'Document not found'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/documents/stats', methods=['GET'])
def get_document_stats():
    """문서 통계 정보를 반환하는 API 엔드포인트"""
    try:
        if not report_generator:
            return jsonify({
                'status': 'error',
                'message': 'Report generator component is not initialized.'
            }), 500
        
        stats = report_generator.get_document_statistics()
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        # 프로덕션 환경에서는 app.logger.error(f"Error fetching document stats: {str(e)}") 등으로 로깅하는 것이 좋습니다.
        return jsonify({
            'status': 'error',
            'message': f'An error occurred while fetching document statistics: {str(e)}'
        }), 500

@app.route('/api/search', methods=['POST'])
def execute_search():
    """검색을 실행하는 API 엔드포인트"""
    try:
        if not content_analyzer or not report_generator:
            raise Exception("Required components not initialized")
            
        data = request.json or {}
        print(f"[DEBUG] 검색 요청 데이터: {data}")
        
        # 검색 쿼리 생성
        query = content_analyzer.create_search_query(
            patterns=data.get('patterns', []),
            options=data.get('options', {}),
            scope=data.get('scope', {})
        )
        print(f"[DEBUG] 생성된 검색 쿼리: {query}")
        
        # 사용 가능한 문서 목록 확인
        available_docs = storage_manager.list_documents()
        print(f"[DEBUG] 사용 가능한 문서 수: {len(available_docs)}")
        if available_docs:
            print(f"[DEBUG] 첫 번째 문서 ID: {available_docs[0].get('id')}")
        
        # 검색 범위에 해당하는 문서 목록 확인
        doc_ids = content_analyzer._get_documents_by_scope(query.get('scope', {}))
        print(f"[DEBUG] 검색 범위 문서 수: {len(doc_ids)}")
        if doc_ids:
            print(f"[DEBUG] 범위 내 첫 번째 문서 ID: {doc_ids[0]}")
        
        # 검색 실행
        search_run_results = content_analyzer.execute_search(query) # 이 결과는 {id: ..., matches: [...], ...} 형태의 딕셔너리
        print(f"[DEBUG] 검색 결과 - 매치 수: {len(search_run_results.get('matches', []))}")

        # 결과를 문서 ID별로 그룹화하고 프론트엔드 형식에 맞게 변환
        grouped_results = {}
        if 'matches' in search_run_results:
            for match in search_run_results['matches']:
                doc_id = match.get('documentId')
                if doc_id not in grouped_results:
                    # storage_manager를 사용하여 문서 메타데이터 가져오기
                    doc_meta = storage_manager.get_document_metadata(doc_id)
                    if not doc_meta: # 문서 메타데이터가 없는 경우 건너뛰기
                        print(f"[WARNING] 메타데이터를 찾을 수 없음: 문서 ID {doc_id}")
                        continue

                    grouped_results[doc_id] = {
                        'id': doc_id,
                        'filename': doc_meta.get('filename', 'Unknown File'),
                        'date': doc_meta.get('createdAt', datetime.now().isoformat()), # 'createdAt' 키 사용
                        'filetype': doc_meta.get('format', 'N/A').upper(),          # 'format' 키 사용
                        'size': doc_meta.get('size', 0),
                        'matches': [],
                        'matchCountInDoc': 0
                    }
                grouped_results[doc_id]['matches'].append(match)
                grouped_results[doc_id]['matchCountInDoc'] += 1
        
        # 프론트엔드로 보낼 최종 결과 (딕셔너리의 값들을 리스트로 변환)
        frontend_results = list(grouped_results.values())
        print(f"[DEBUG] 프론트엔드 결과 수: {len(frontend_results)}")

        # 결과가 없는 경우 기본 문서라도 가져와서 보여주기 (디버깅용)
        if not frontend_results and available_docs:
            print(f"[DEBUG] 결과가 없어 샘플 문서를 확인합니다.")
            # 첫 번째 문서의 일부 내용 출력
            sample_doc = storage_manager.get_document(available_docs[0].get('id'))
            if sample_doc and 'content' in sample_doc and 'text' in sample_doc['content']:
                sample_text = sample_doc['content']['text'][:200] + '...' if len(sample_doc['content']['text']) > 200 else sample_doc['content']['text']
                print(f"[DEBUG] 샘플 문서 내용: {sample_text}")

        # 보고서 생성 (보고서 생성기는 search_run_results 전체를 받을 수도 있고, frontend_results를 받을 수도 있음.
        # 현재 generate_report는 search_results를 받으므로 search_run_results를 전달)
        report_format = data.get('reportFormat', 'html')
        report_metadata = report_generator.generate_report(search_run_results, report_format=report_format)
        
        return jsonify({
            'status': 'success',
            'data': {
                'results': frontend_results, # 프론트엔드에는 변환된 결과를 전달
                'reportUrl': f"/view/report/{report_metadata['id']}"
            }
        })
    except Exception as e:
        print(f"[ERROR] 검색 오류: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    """보고서를 조회하는 API 엔드포인트"""
    try:
        if not report_generator:
            raise Exception("Report generator not initialized")
            
        report = report_generator.get_report(report_id)
        if report:
            return jsonify({
                'status': 'success',
                'data': report
            })
        return jsonify({
            'status': 'error',
            'message': 'Report not found'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/view/document/<doc_id>')
def view_document(doc_id):
    """문서 뷰어 페이지"""
    return render_template('document_viewer.html', doc_id=doc_id)

@app.route('/view/report/<report_id>')
def view_report(report_id):
    """보고서 뷰어 페이지"""
    if not report_generator:
        return "Report generator not initialized", 500
        
    report = report_generator.get_report(report_id)
    if not report:
        return "Report not found", 404
        
    if not os.path.exists(report['path']):
        return "Report file not found", 404
        
    if report['format'] == 'html':
        # HTML 보고서 제공
        return send_file(report['path'])
    elif report['format'] == 'json':
        # JSON 보고서 뷰어에서 렌더링
        try:
            with open(report['path'], 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            return render_template('json_viewer.html', 
                               report_id=report_id,
                               report_data=json.dumps(report_data, indent=2, ensure_ascii=False))
        except Exception as e:
            return f"Error loading JSON report: {str(e)}", 500
    else:
        # 기타 형식은 다운로드로 처리
        return send_file(report['path'], as_attachment=True)

# 에러 핸들러
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, error_message="페이지를 찾을 수 없습니다."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message="서버 내부 오류가 발생했습니다."), 500

# 파일 업로드 API
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """파일 업로드 API 엔드포인트"""
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No file part'
        }), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file'
        }), 400
        
    if file:
        try:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            return jsonify({
                'status': 'success',
                'message': 'File uploaded successfully',
                'filename': file.filename
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

# 배치 작업 관리 API
@app.route('/api/jobs', methods=['GET', 'POST'])
def manage_jobs():
    """배치 작업 관리 API 엔드포인트"""
    if not storage_manager or not document_processor:
        return jsonify({
            'status': 'error',
            'message': '필요한 컴포넌트가 초기화되지 않았습니다.'
        }), 500
        
    if request.method == 'GET':
        # 작업 목록 조회
        try:
            # BatchProcessor에서 작업 목록 가져오기
            jobs = storage_manager.batch_processor.get_all_jobs() if hasattr(storage_manager, 'batch_processor') else []
            return jsonify({
                'status': 'success',
                'data': jobs
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'작업 목록 조회 중 오류 발생: {str(e)}'
            }), 500
            
    elif request.method == 'POST':
        # 새 작업 생성
        try:
            data = request.json or {}
            job_type = data.get('job_type')
            job_params = data.get('job_params', {})
            
            # 작업 유형 검증
            valid_types = ['process_directory', 'bulk_analyze', 'generate_reports']
            if job_type not in valid_types:
                return jsonify({
                    'status': 'error',
                    'message': f'유효하지 않은 작업 유형입니다. 가능한 값: {valid_types}'
                }), 400
            
            # 작업 생성 및 실행
            job_id = storage_manager.batch_processor.create_job(job_type, job_params)
            storage_manager.batch_processor.start_job(job_id)
            
            return jsonify({
                'status': 'success',
                'data': {
                    'job_id': job_id,
                    'status': 'running',
                    'message': '작업이 성공적으로 시작되었습니다.'
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'작업 생성 중 오류 발생: {str(e)}'
            }), 500

@app.route('/api/jobs/<job_id>', methods=['GET', 'DELETE', 'PUT'])
def job_detail(job_id):
    """특정 작업 조회, 삭제 또는 업데이트"""
    if not storage_manager or not hasattr(storage_manager, 'batch_processor'):
        return jsonify({
            'status': 'error',
            'message': '필요한 컴포넌트가 초기화되지 않았습니다.'
        }), 500
        
    try:
        batch_processor = storage_manager.batch_processor
        
        if request.method == 'GET':
            # 작업 상세 정보 조회
            job = batch_processor.get_job(job_id)
            
            if not job:
                return jsonify({
                    'status': 'error',
                    'message': f'작업 ID {job_id}을(를) 찾을 수 없습니다.'
                }), 404
                
            return jsonify({
                'status': 'success',
                'data': job
            })
            
        elif request.method == 'DELETE':
            # 작업 삭제
            if not batch_processor.job_exists(job_id):
                return jsonify({
                    'status': 'error',
                    'message': f'작업 ID {job_id}을(를) 찾을 수 없습니다.'
                }), 404
                
            batch_processor.delete_job(job_id)
            return jsonify({
                'status': 'success',
                'message': f'작업 {job_id}이(가) 성공적으로 삭제되었습니다.'
            })
            
        elif request.method == 'PUT':
            # 작업 업데이트 (상태 변경 등)
            if not batch_processor.job_exists(job_id):
                return jsonify({
                    'status': 'error',
                    'message': f'작업 ID {job_id}을(를) 찾을 수 없습니다.'
                }), 404
                
            data = request.json or {}
            action = data.get('action')
            
            if action == 'pause':
                batch_processor.pause_job(job_id)
                message = '작업이 일시 중지되었습니다.'
            elif action == 'resume':
                batch_processor.resume_job(job_id)
                message = '작업이 재개되었습니다.'
            elif action == 'cancel':
                batch_processor.cancel_job(job_id)
                message = '작업이 취소되었습니다.'
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'유효하지 않은 액션입니다. 가능한 값: pause, resume, cancel'
                }), 400
                
            return jsonify({
                'status': 'success',
                'message': message
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'작업 처리 중 오류 발생: {str(e)}'
        }), 500

# 정적 파일 제공을 위한 라우트
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# 배치 작업 관리 페이지 라우트 추가
@app.route('/jobs')
def jobs_page():
    """배치 작업 관리 페이지"""
    return render_template('jobs.html')

# 초기화 함수 추가
def initialize_app(config):
    """애플리케이션 초기화 함수"""
    global document_processor, storage_manager, content_analyzer, report_generator
    
    try:
        # 모듈 import - 상대 경로로 수정
        from src.document_processor.processor import DocumentProcessor
        from src.storage_manager.manager import StorageManager
        from src.content_analyzer.analyzer import ContentAnalyzer
        from src.report_generator.generator import ReportGenerator
        
        # 컴포넌트 초기화
        document_processor = DocumentProcessor(config.get('document_processor', {}))
        storage_manager = StorageManager(
            config.get('input_dir', 'input'),
            config.get('output_dir', 'output'),
            document_processor
        )
        content_analyzer = ContentAnalyzer(storage_manager)
        report_generator = ReportGenerator(config.get('output_dir', 'output'), storage_manager)
        
        # 파일 모니터링 시작
        storage_manager.start_monitoring()
        
        return True
    except Exception as e:
        print(f"애플리케이션 초기화 중 오류 발생: {str(e)}")
        return False

# 설정 로드
config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
try:
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        print("설정 파일을 찾을 수 없어 기본 설정을 사용합니다.")
        config = {
            'debug': True,
            'host': '0.0.0.0',
            'port': 5000,
            'input_dir': os.path.join(os.path.dirname(__file__), '..', '..', 'input'),
            'output_dir': os.path.join(os.path.dirname(__file__), '..', '..', 'output')
        }
except Exception as e:
    print(f"설정 파일 로드 중 오류 발생: {str(e)}")
    config = {}

# 애플리케이션 초기화
initialize_app(config)

if __name__ == '__main__':
    # Flask 앱 실행
    app.run(debug=config.get('debug', True), 
            host=config.get('host', '0.0.0.0'), 
            port=5003) # 포트를 5003으로 변경
