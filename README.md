# Nales-It: Ứng dụng EdTech Tích hợp Trí Tuệ Nhân Tạo

Dự án ứng dụng di động giáo dục thế hệ mới, tự động bóc tách file PDF đề thi thành các bài trắc nghiệm tương tác siêu mượt nhờ công nghệ LLMs. 

## 🌟 Tính Năng Nổi Bật

### 1. Kiến trúc Trí tuệ Nhân tạo Đa tầng (Two-Pass Pipeline)
- **Fast Extraction**: Sử dụng `gemini-flash-latest` để đọc và bóc tách cấu trúc file PDF cực nhanh.
- **Deep Reasoning**: Tự động dùng `gemini-3.1-pro-preview` đóng vai trò Gia sư để giải các câu hỏi không có đáp án, và nhận xét điểm yếu/mạnh của học sinh ở cuối bài.
- **Background Chunking**: Tự động băm nhỏ đề thi dài thành các cụm 5 câu. API chỉ giải 5 câu đầu và trả kết quả ngay, các câu còn lại được AI giải ngầm ở Background giúp ứng dụng khởi động tức thì, chống dính Timeout.

### 2. Trải nghiệm Mobile Mượt Mà (Lazy Loading)
- 4 chế độ làm bài thông minh: **Ôn Luyện**, **Thi Thử**, **Đánh Giá AI**, và **Tự Do**.
- Giao diện tone màu **Xanh Da Trời (Sky Blue)** thân thiện.
- Tính năng **Lazy Loading**: Khi học sinh lướt PageView sang câu mới, Mobile tự động kéo đáp án (vừa được AI giải ngầm xong) từ Server về một cách lặng lẽ.

### 3. Tương tác "Giải Lại" (Re-solve) Độc Đáo
- Nếu cảm thấy lời giải của AI "cấn cấn", học sinh có thể bấm biểu tượng Cờ đỏ 🚩. 
- Hệ thống sẽ kích hoạt một API đặc biệt bắt AI suy luận lại từng bước một (Step-by-step) với mức tư duy cao hơn để cập nhật lời giải mới ngay lập tức.

## 🛠️ Công Nghệ Sử Dụng

- **Backend**: Python 3.11, FastAPI, LangChain, Motor (MongoDB Async Driver).
- **Frontend (Mobile)**: Flutter, Riverpod (State Management), Dio, go_router.
- **Database**: MongoDB (Tích hợp sẵn tính năng Graceful Fallback sang Mock DB/RAM nếu máy dev chưa bật Docker).

## 🚀 Hướng Dẫn Khởi Chạy (Local)

### 1. Backend
Đảm bảo bạn đã cấu hình biến môi trường `GEMINI_API_KEY` trong file `backend/.env`.
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```
*(Nếu có cài đặt Docker, hãy chạy `docker-compose up -d` ở thư mục gốc để bật MongoDB. Nếu không, hệ thống sẽ tự động fallback về Mock DB).*

### 2. Mobile App
```bash
cd mobile
flutter pub get
flutter run -d chrome  # hoặc flutter run -d edge
```

## 📝 Nhật ký Phát triển
Dự án đã hoàn thiện Phase 6 (Background Task, Chunking, Resolve AI, và Giao diện UI). Sẵn sàng cho những đợt nâng cấp tiếp theo trong tương lai!
