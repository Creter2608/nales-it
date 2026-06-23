# Bảng công việc cho Phiên làm việc tiếp theo (Tối ưu Hiệu suất Extraction)

Hiện tại, tốc độ tạo đề (Upload PDF) đã được cải thiện từ 10 phút xuống còn 1-2 phút nhờ cơ chế **Background Chunking** (khi đưa việc giải đề xuống chạy ngầm). Tuy nhiên, 1-2 phút vẫn là khá chậm đối với trải nghiệm người dùng hiện đại.

Lý do của sự chậm trễ này là do bước **Nhận diện sườn đề (Extraction)**: AI (`gemini-flash`) đang phải đọc toàn bộ PDF và sinh ra một JSON cực lớn cùng một lúc. Token Generation mất nhiều thời gian.

## 🎯 Các giải pháp cần thực hiện ở Phase tới:

> **[CẬP NHẬT PHASE 8]**: Ở phiên làm việc gần nhất, hệ thống đã được tối ưu cực kỳ chuyên sâu (Deep Refactoring) về kiến trúc:
> - Giải quyết bài toán treo Backend khi parse PDF bằng cách bọc `opendataloader` và `fitz` vào `asyncio.to_thread`.
> - Tối ưu vòng đời (Memory Leaks) trên Mobile bằng `autoDispose` cho Riverpod, tự động thu dọn rác bộ nhớ.
> - Xử lý ngắt kết nối thông minh (Orphaned Task Cancellation) tránh "đốt" tiền API Gemini khi user thoát ngang.
> - An toàn Database với kết nối an toàn và chặn lỗ hổng ghi đè dữ liệu cục bộ bằng Atomic Update `$set`.

### ~~1. Băm nhỏ quá trình đọc PDF (Concurrent Extraction)~~ [ĐÃ HOÀN THÀNH Ở PHASE 7]
- **Vấn đề**: Hiện tại đẩy nguyên cục text dài vào Flash.
- **Giải pháp**: Tách text PDF theo từng trang (hoặc từng cụm 2-3 trang). Sử dụng `asyncio.gather()` ở Backend để gọi API `gemini-1.5-flash` **song song** (Concurrent). 
- **Lợi ích**: Dù đề thi có 10 trang hay 100 trang, thời gian nhận diện sườn đề sẽ được rút ngắn đáng kể!

### 2. Tối giản cấu trúc Prompt JSON
- Ép LLM trả về cấu trúc JSON rút gọn nhất có thể. Càng ít chữ (token) được sinh ra, tốc độ API trả về càng nhanh.

### 3. Giảm tải Synchronous Solving
- Hiện tại đang chờ giải xong 5 câu đầu tiên rồi mới trả kết quả về Mobile. 
- Có thể giảm xuống chỉ chờ giải xong **1 hoặc 2 câu đầu**, phần còn lại đưa vào Background. Thời gian chờ sẽ giảm thêm được 10 giây nữa.

### ~~4. Cải thiện UI (Real-time Feedback)~~ [ĐÃ HOÀN THÀNH Ở PHASE 7]
- Thay vì Mobile hiện một vòng xoay Loading nhàm chán suốt 1 phút, Backend đã được nâng cấp để trả về Server-Sent Events (SSE). Mobile hiển thị từng câu hỏi được trích xuất theo thời gian thực giống như hiệu ứng stream, tạo cảm giác mượt mà và an tâm cho người dùng.

### 5. Xây dựng "Ngân hàng Câu hỏi" (Global Question Bank / AI Caching)
- **Ý tưởng nâng cao**: Khi người dùng A upload một đề và AI đã giải xong, câu hỏi cùng lời giải đó sẽ được lưu vào một thư viện chung (Question Bank / Vector DB) thông qua thuật toán băm (Hashing) hoặc nhúng vector (Embeddings).
- **Lợi ích**: Khi người dùng B upload một đề khác nhưng có chứa câu hỏi trùng lặp (hoặc giống 95% do sai số nhận diện OCR), hệ thống sẽ đối chiếu và lấy thẳng lời giải từ thư viện ra thay vì gọi API Gemini. Tối ưu hóa cực kỳ mạnh mẽ chi phí Token và đẩy tốc độ tạo đề đạt mức "tức thời" (0 giây) đối với các câu hỏi phổ biến.

### 6. Tính năng Tra cứu Câu hỏi (Global Search / Diễn đàn Mini)
- **Ý tưởng**: Dựa trên "Ngân hàng Câu hỏi" đã xây dựng ở mục 5, chúng ta sẽ làm một thanh công cụ Search (Tìm kiếm). Học sinh không cần phải upload nguyên cái đề, mà chỉ cần gõ nội dung câu hỏi (hoặc chụp ảnh câu hỏi) lên thanh tìm kiếm.
- **Cách thức hoạt động**: Hệ thống sẽ truy vấn vào Vector DB (Semantic Search) để tìm ra các câu hỏi tương tự nhất đã được AI giải trước đó. Hoạt động giống hệt chức năng tìm kiếm của một diễn đàn học tập cộng đồng (như Hocmai, VietJack,...), giúp học sinh tham khảo cách giải ngay lập tức.

### 7. Hệ thống Đánh giá Cá nhân hóa (Personalized Learning & Recommendation)
- **Ý tưởng**: Thu thập dữ liệu lịch sử làm bài (Quiz History) của từng học sinh. AI sẽ tổng hợp và phân tích xem học sinh đó thường trả lời sai ở dạng bài nào, chuyên đề nào.
- **Cách thức hoạt động**: Từ bảng đánh giá điểm yếu (Knowledge Gaps), hệ thống sẽ chủ động "nhặt" các câu hỏi từ **Ngân hàng Câu hỏi (Question Bank)** để tạo ra một "Đề thi Ôn tập (Tailored Quiz)" dành riêng cho học sinh đó. Tính năng này giống như một Gia sư cá nhân thực thụ theo dõi sát sao sự tiến bộ của học sinh.

### 8. Linh vật AI "Nales" & Catchphrase
- **Ý tưởng**: Xây dựng nhận diện thương hiệu (Branding) với linh vật là một trợ lý AI mang tên **Nales**.
- **Cách thức hoạt động**: Khi học sinh làm đúng một câu hỏi khó hoặc đạt điểm xuất sắc trong bài thi, một Popup/Animation của Nales sẽ xuất hiện với câu thoại đặc trưng: **"Nales It!"** (Chơi chữ của từ "Nailed It!" - Làm tốt lắm/Đỉnh quá!). Giúp tạo động lực, sự thân thiện và yếu tố Gamification cho ứng dụng.

### 9. Chế độ "Ôn thi cấp tốc" (Crash Course / Speed Run)
- **Ý tưởng**: Tính năng giao tiếp trực tiếp với linh vật Nales để thiết kế đề ôn tập theo yêu cầu chủ đề cụ thể.
- **Cách thức hoạt động**: Thay vì tự tải đề lên, học sinh chỉ cần chat/yêu cầu Nales: *"Hãy giúp mình ôn cấp tốc môn Database"*. Hệ thống sẽ ngay lập tức truy vấn vào **Ngân hàng Câu hỏi** để tổng hợp ra một bộ đề bao quát toàn bộ các mảng kiến thức cốt lõi nhất của môn Database. Giúp học sinh ôn thi "nước rút" ngay trước giờ G một cách hiệu quả nhất.

### 10. Chống trùng lặp Đa ngôn ngữ (Cross-lingual Deduplication) & Entity-Variant Architecture
- **Vấn đề**: Ứng dụng định hướng quốc tế, cùng một bài toán (ví dụ Toán học) nhưng người dùng upload bằng tiếng Anh, tiếng Việt, hoặc Tây Ban Nha. Việc gọi AI giải lại từ đầu cùng một bài toán gây lãng phí Token. Ngược lại, nếu chỉ lưu 1 bản gốc (VD: Tiếng Anh) rồi dùng công cụ dịch tự động (như Google Translate) để hiển thị thì sẽ gây ra lỗi dịch thuật lủng củng đối với các thuật ngữ chuyên ngành.
- **Giải pháp (Kiến trúc Entity - Variant)**: 
  - Sử dụng **Cross-lingual Text Embeddings** để phát hiện ra câu tiếng Việt và câu tiếng Anh thực chất là *cùng một bài toán cốt lõi*.
  - Hệ thống sẽ tạo ra 1 `Entity` (Thực thể cốt lõi) chứa **cách giải logic (Toán học/Vật lý)** do AI giải 1 lần duy nhất.
  - Các câu hỏi bằng ngôn ngữ khác nhau được người dùng upload lên sẽ được lưu dưới dạng các **`Variants` (Biến thể ngôn ngữ)** gắn vào Entity đó.
  - Khi hiển thị, học sinh Tây Ban Nha sẽ đọc đúng văn bản gốc do người Tây Ban Nha upload (không bị dịch máy lủng củng). Core logic giải bài sẽ được LLM (có hiểu biết ngữ cảnh chuyên ngành) chuyển ngữ mượt mà sang ngôn ngữ đích chỉ trong 1 tích tắc.

### 11. Hàng đợi thông minh & Khử trùng lặp Tức thời (Request Deduplication & Queueing)
- **Vấn đề**: Trong các mùa thi cao điểm, có thể có 50 học sinh cùng một lớp tải lên chung một file "Đề Thi Giữa Kỳ Toán.pdf" vào cùng một thời điểm (ví dụ lúc 8h00 tối). Nếu đẩy cả 50 request này lên API Gemini thì sẽ gây lãng phí khổng lồ và dễ dính lỗi `429 Too Many Requests`.
- **Giải pháp**: Xây dựng cơ chế **Request Deduplication Queue**. 
  - Khi nhận file, hệ thống sẽ tính mã băm (Hash - MD5/SHA256) của nội dung file PDF.
  - Nếu file đó đang được AI giải rồi (trạng thái `Processing`), 49 học sinh đăng sau sẽ được đưa vào một Hàng đợi (Queue/PubSub) để "chờ ké" kết quả.
  - Ngay khi AI giải xong cho người đầu tiên, kết quả sẽ được Broadcast (Phát sóng) trả về ngay lập tức cho 49 người còn lại mà không tốn thêm bất kỳ một đồng tiền Token nào!

### ~~12. Chống ngợp Token ở khâu Bóc tách (Extraction Chunking & Pagination)~~ [ĐÃ HOÀN THÀNH Ở PHASE 7]
- **Giải pháp đã triển khai**: Xử lý băm nhỏ ngay từ lúc đọc PDF (Pagination) kết hợp Semaphore giới hạn Rate Limit.
  - Tách PDF thành từng cụm.
  - Gửi song song (Concurrent) nhiều request đến `gemini-1.5-flash` để bóc tách từng cụm trang đó thành các mảng JSON nhỏ. Tự động trả về qua SSE. Lách được Token Limit và tăng tốc độ nhờ chạy song song.

### 13. Hệ thống Tài khoản & Gói cước (Auth & Monetization)
- **Ý tưởng**: Xây dựng mô hình kinh doanh cho ứng dụng với hệ thống Người dùng Miễn phí (Free) và Trả phí (Premium/Pro).
- **Cách thức hoạt động**:
  - **Auth**: Tích hợp đăng nhập bằng Google/Apple (OAuth2) để quá trình Onboarding siêu nhanh gọn.
  - **Tier 1 (Free Users)**: Được quyền tìm kiếm câu hỏi trong Diễn đàn/Ngân hàng đề miễn phí. Nếu upload đề mới, chỉ được giải 10 câu đầu, hoặc bị giới hạn số lượng câu hỏi giải bằng AI trong ngày (Daily Quota).
  - **Tier 2 (Premium Users)**: Trả phí hàng tháng. Được cấp quyền truy cập tính năng "Ôn thi Cấp tốc cùng Nales", không giới hạn độ dài đề thi tải lên, và được quyền dùng nút 🚩 (Re-solve) để yêu cầu Gia sư AI giải chi tiết Step-by-step.

---
*Ghi chú này được tạo ra để chuẩn bị cho phiên làm việc nâng cấp hiệu suất tiếp theo!*
