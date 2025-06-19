from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_test_pdf(output_path):
    """테스트용 PDF 파일 생성"""
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # PDF 생성
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter  # A4 용지 크기
    
    # 제목 추가
    c.setFont("Helvetica-Bold", 16)
    title = "Docling 테스트 문서"
    title_width = c.stringWidth(title, "Helvetica-Bold", 16)
    c.drawString((width - title_width) / 2, height - 50, title)
    
    # 본문 추가
    c.setFont("Helvetica", 12)
    y_position = height - 100
    
    # 텍스트 추가
    text_lines = [
        "이 문서는 Docling 통합 테스트를 위해 생성된 테스트 문서입니다.",
        "This is a test document for Docling integration testing.",
        "",
        "테스트 항목:",
        "1. 텍스트 추출",
        "2. 표 인식",
        "3. 레이아웃 분석"
    ]
    
    for line in text_lines:
        c.drawString(50, y_position, line)
        y_position -= 20
    
    # 표 추가 (간단한 표)
    y_position -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "테이블 예제:")
    y_position -= 20
    
    # 표 헤더
    c.rect(50, y_position - 15, 200, 20)
    c.rect(150, y_position - 15, 100, 20)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_position - 10, "항목")
    c.drawString(160, y_position - 10, "값")
    
    # 표 내용
    table_data = [
        ("생성일", "2025-05-17"),
        ("버전", "1.0.0"),
        ("작성자", "테스터")
    ]
    
    for i, (key, value) in enumerate(table_data):
        y = y_position - 20 - (i * 20)
        c.rect(50, y - 15, 200, 20)
        c.rect(150, y - 15, 100, 20)
        c.setFont("Helvetica", 10)
        c.drawString(60, y - 10, key)
        c.drawString(160, y - 10, value)
    
    # 페이지 저장
    c.save()
    print(f"테스트 PDF 파일이 생성되었습니다: {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = os.path.join(os.path.dirname(__file__), "test_data/test_document.pdf")
    
    create_test_pdf(output_path)
