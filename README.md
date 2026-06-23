# Nales-It: Ứng dụng EdTech Tích hợp Trí Tuệ Nhân Tạo

Dự án ứng dụng di động giáo dục thế hệ mới, tự động bóc tách file PDF đề thi thành các bài trắc nghiệm tương tác siêu mượt nhờ công nghệ LLMs. 

## 🌟 Tính Năng Nổi Bật

### 1. Kiến trúc Trí tuệ Nhân tạo Đa tầng (Two-Pass Pipeline) & Streaming
- **Fast Extraction (Streaming)**: Tách PDF thành các trang nhỏ, xử lý song song bằng `gemini-1.5-flash`, và trả dữ liệu về Mobile theo thời gian thực (SSE - Server-Sent Events) giúp ứng dụng phản hồi chớp nhoáng.
- **Deep Reasoning**: Tự động dùng `gemini-3.1-pro-preview` đóng vai trò Gia sư để giải các câu hỏi không có đáp án, và nhận xét điểm yếu/mạnh của học sinh ở cuối bài.
- **Background Chunking**: Tính năng gom cụm thông minh giúp AI bóc tách đến đâu học sinh làm bài đến đó, các thao tác phụ trợ được xử lý ở Background chống dính Timeout.

### 2. Trải nghiệm Mobile Mượt Mà (Progressive Loading)
- 4 chế độ làm bài thông minh: **Ôn Luyện**, **Thi Thử**, **Đánh Giá AI**, và **Tự Do**.
- Giao diện tone màu **Xanh Da Trời (Sky Blue)** thân thiện.
- Tính năng **Progressive Loading**: Hiệu ứng UI như xem video YouTube, câu hỏi hiện dần trong lúc AI đang chạy ngầm, tích hợp Lazy Loading gọi đáp án mượt mà.

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
Dự án đã hoàn thiện Phase 7 (Cơ chế Progressive Streaming qua Server-Sent Events, Pagination Chunking cho PDF, Giao diện Loading mượt mà trên Mobile, và Xử lý Rate Limit với `gemini-1.5-flash`).
**Mới cập nhật:** Đã hoàn tất **Phase 8 - Tối ưu Toàn diện & Sửa lỗi Sâu (Deep Refactoring)**. Xử lý triệt để Event Loop Blocking bằng `asyncio.to_thread`, ngăn rò rỉ RAM (Memory Leaks) bằng `autoDispose` trên Riverpod, chặn gọi thừa API Gemini khi rớt kết nối mạng (Orphaned Task Cancellation), tối ưu băm nhỏ ngữ cảnh hình ảnh (Context Window Overflow) và nâng cấp cấu hình bảo mật Database/CORS.

Sẵn sàng cho những đợt nâng cấp tiếp theo về Ngân hàng Câu hỏi và Social Features!
