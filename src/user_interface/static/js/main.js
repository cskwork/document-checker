/**
 * 문서 검사기 메인 JavaScript 파일
 * 공통 기능 및 UI 상호작용을 처리합니다.
 */

document.addEventListener('DOMContentLoaded', function() {
    // 파일 업로드 모달 초기화
    initFileUpload();
    
    // 네비게이션 활성화
    activateCurrentNavItem();
    
    // 알림 자동 닫기
    initAlertDismiss();
});

/**
 * 파일 업로드 기능 초기화
 */
function initFileUpload() {
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadModal = document.getElementById('uploadModal');
    const uploadForm = document.getElementById('uploadForm');
    const submitUpload = document.getElementById('submitUpload');
    const fileInput = document.getElementById('fileInput');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = uploadProgress ? uploadProgress.querySelector('.progress-bar') : null;
    
    if (!uploadBtn || !uploadModal) return;
    
    // 업로드 버튼 클릭 이벤트
    uploadBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const modalInstance = new bootstrap.Modal(uploadModal);
        modalInstance.show();
    });
    
    // 파일 업로드 제출 이벤트
    if (submitUpload && uploadForm && fileInput && uploadProgress && progressBar) {
        submitUpload.addEventListener('click', function() {
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('파일을 선택해주세요.');
                return;
            }
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            // 프로그레스 바 초기화
            uploadProgress.classList.remove('d-none');
            progressBar.style.width = '0%';
            progressBar.setAttribute('aria-valuenow', 0);
            progressBar.classList.remove('bg-success', 'bg-danger');
            progressBar.classList.add('bg-primary');
            
            // AJAX 요청으로 파일 업로드
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/upload', true);
            
            // 업로드 진행 상황 모니터링
            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percentComplete + '%';
                    progressBar.setAttribute('aria-valuenow', percentComplete);
                }
            };
            
            // 업로드 완료 처리
            xhr.onload = function() {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.status === 'success') {
                            progressBar.classList.remove('bg-primary');
                            progressBar.classList.add('bg-success');
                            progressBar.style.width = '100%';
                            progressBar.setAttribute('aria-valuenow', 100);
                            
                            // 성공 메시지 표시 후 페이지 새로고침
                            setTimeout(function() {
                                const modalInstance = bootstrap.Modal.getInstance(uploadModal);
                                modalInstance.hide();
                                window.location.reload();
                            }, 1000);
                        } else {
                            throw new Error(response.message || '파일 업로드 중 오류가 발생했습니다.');
                        }
                    } catch (error) {
                        showUploadError(error.message);
                    }
                } else {
                    showUploadError('서버 오류: ' + xhr.status);
                }
            };
            
            // 업로드 오류 처리
            xhr.onerror = function() {
                showUploadError('네트워크 오류가 발생했습니다.');
            };
            
            // 요청 전송
            xhr.send(formData);
        });
    }
    
    // 업로드 오류 표시 함수
    function showUploadError(message) {
        if (progressBar) {
            progressBar.classList.remove('bg-primary');
            progressBar.classList.add('bg-danger');
            progressBar.style.width = '100%';
            progressBar.setAttribute('aria-valuenow', 100);
        }
        alert('파일 업로드 오류: ' + message);
    }
}

/**
 * 현재 페이지에 해당하는 네비게이션 항목 활성화
 */
function activateCurrentNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
        } else if (currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        }
    });
}

/**
 * 알림 자동 닫기 기능 초기화
 */
function initAlertDismiss() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * 파일 크기를 사람이 읽기 쉬운 형식으로 변환
 * @param {number} bytes - 바이트 단위 파일 크기
 * @returns {string} 변환된 파일 크기 문자열
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 날짜를 사람이 읽기 쉬운 형식으로 변환
 * @param {string|Date} date - 날짜 문자열 또는 Date 객체
 * @returns {string} 변환된 날짜 문자열
 */
function formatDate(date) {
    if (!date) return '-';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return '-';
    
    return d.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 문서 유형에 따른 아이콘 클래스 반환
 * @param {string} fileType - 문서 유형 (확장자)
 * @returns {string} Bootstrap 아이콘 클래스
 */
function getFileTypeIcon(fileType) {
    if (!fileType) return 'bi-file-earmark';
    
    const type = fileType.toLowerCase();
    
    switch (type) {
        case 'pdf':
            return 'bi-file-earmark-pdf';
        case 'docx':
        case 'doc':
            return 'bi-file-earmark-word';
        case 'xlsx':
        case 'xls':
            return 'bi-file-earmark-excel';
        case 'pptx':
        case 'ppt':
            return 'bi-file-earmark-ppt';
        case 'txt':
            return 'bi-file-earmark-text';
        case 'csv':
            return 'bi-file-earmark-spreadsheet';
        case 'jpg':
        case 'jpeg':
        case 'png':
        case 'gif':
            return 'bi-file-earmark-image';
        default:
            return 'bi-file-earmark';
    }
}

/**
 * API 요청 함수
 * @param {string} url - 요청 URL
 * @param {Object} options - fetch 옵션
 * @returns {Promise} API 응답 Promise
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (data.status === 'error') {
            throw new Error(data.message || '요청 처리 중 오류가 발생했습니다.');
        }
        
        return data;
    } catch (error) {
        console.error('API 요청 오류:', error);
        throw error;
    }
}

/**
 * 문서 상태에 따른 배지 HTML 반환
 * @param {string} status - 문서 상태
 * @returns {string} 배지 HTML
 */
function getStatusBadge(status) {
    if (!status) return '';
    
    let badgeClass = 'bg-secondary';
    let badgeText = status;
    
    switch (status.toLowerCase()) {
        case 'processed':
        case 'complete':
        case 'completed':
            badgeClass = 'bg-success';
            badgeText = '처리 완료';
            break;
        case 'processing':
        case 'in_progress':
            badgeClass = 'bg-primary';
            badgeText = '처리 중';
            break;
        case 'pending':
        case 'queued':
            badgeClass = 'bg-warning text-dark';
            badgeText = '대기 중';
            break;
        case 'error':
        case 'failed':
            badgeClass = 'bg-danger';
            badgeText = '오류';
            break;
    }
    
    return `<span class="badge ${badgeClass}">${badgeText}</span>`;
}
