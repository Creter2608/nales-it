import requests
from reportlab.pdfgen import canvas

def create_pdf(filename):
    c = canvas.Canvas(filename)
    text = """Trường Đại học Bách khoa-ĐHQG TPHCM Khoa Khoa học Ứng dụng
Thi cuối kỳ Kỳ/năm học 241 2024-2025
Ngày thi 24/12/2024
Môn học GIẢI TÍCH 1
Câu 1. (L.O.1) Cho f(x) = 1/sqrt(1 + 2x). Dùng xấp xỉ tuyến tính của f(x) tại x0 = 0 để tính gần đúng f(-0.1) ta được kết quả là
A 1.1372 B Các câu khác sai. C 1.0863
D 1.0763 E 1.1000"""
    c.drawString(100, 750, "Sample Exam")
    y = 730
    for line in text.split('\n'):
        c.drawString(100, y, line)
        y -= 20
    c.save()

if __name__ == "__main__":
    create_pdf("test_exam.pdf")
    with open("test_exam.pdf", "rb") as f:
        response = requests.post("http://localhost:8000/api/v1/upload/pdf", files={"file": f})
    
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except:
        print("Response Text:", response.text)
