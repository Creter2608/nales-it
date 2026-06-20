# Bảng công việc cho Phiên làm việc tiếp theo (Tối ưu Hiệu suất Extraction)

Hiện tại, tốc độ tạo đề (Upload PDF) đã được cải thiện từ 10 phút xuống còn 1-2 phút nhờ cơ chế **Background Chunking** (khi đưa việc giải đề xuống chạy ngầm). Tuy nhiên, 1-2 phút vẫn là khá chậm đối với trải nghiệm người dùng hiện đại.

Lý do của sự chậm trễ này là do bước **Nhận diện sườn đề (Extraction)**: AI (`gemini-flash`) đang phải đọc toàn bộ PDF và sinh ra một JSON cực lớn cùng một lúc. Token Generation mất nhiều thời gian.

## 🎯 Các giải pháp cần thực hiện ở Phase tới:

### 1. Băm nhỏ quá trình đọc PDF (Concurrent Extraction)
- **Vấn đề**: Hiện tại đẩy nguyên cục text dài vào Flash.
- **Giải pháp**: Tách text PDF theo từng trang (hoặc từng cụm 2-3 trang). Sử dụng `asyncio.gather()` ở Backend để gọi API `gemini-flash` **song song** (Concurrent). 
- **Lợi ích**: Dù đề thi có 10 trang hay 100 trang, thời gian nhận diện sườn đề sẽ được rút ngắn xuống chỉ bằng thời gian nhận diện 1 trang (khoảng 5 - 10 giây)!

### 2. Tối giản cấu trúc Prompt JSON
- Ép LLM trả về cấu trúc JSON rút gọn nhất có thể. Càng ít chữ (token) được sinh ra, tốc độ API trả về càng nhanh.

### 3. Giảm tải Synchronous Solving
- Hiện tại đang chờ giải xong 5 câu đầu tiên rồi mới trả kết quả về Mobile. 
- Có thể giảm xuống chỉ chờ giải xong **1 hoặc 2 câu đầu**, phần còn lại đưa vào Background. Thời gian chờ sẽ giảm thêm được 10 giây nữa.

### 4. Cải thiện UI (Real-time Feedback)
- Thay vì Mobile hiện một vòng xoay Loading nhàm chán suốt 1 phút, Backend có thể trả về tiến trình (Server-Sent Events / WebSocket) để Mobile hiển thị: *"Đang phân tích trang 1/10...", "Đang phân tích trang 5/10..."*. Tạo cảm giác nhanh và an tâm cho người dùng.

---
*Ghi chú này được tạo ra để chuẩn bị cho phiên làm việc nâng cấp hiệu suất tiếp theo!*
