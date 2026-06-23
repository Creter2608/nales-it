# Code Review & Optimization — Nales-It

Báo cáo rà soát toàn diện dự án **Nales-It** (Backend Python/FastAPI + Mobile Flutter/Dart) theo 5 trục đánh giá.

> [!NOTE]
> Báo cáo này dựa trên mã nguồn **thực tế trên disk** đã được xác minh trực tiếp. Backend đã dùng `lifespan` context manager (tốt), Pydantic schemas đã được sử dụng ở quiz API (tốt), Mobile dùng shared `dioProvider` (tốt).

---

## User Review Required

> [!CAUTION]
> **API Key & MongoDB credentials bị lộ trong `.env` đang nằm trong Git.** File [.env](file:///d:/Nales-It/nales-it/backend/.env) chứa `GEMINI_API_KEY` và `MONGODB_URI` (với username/password) dạng plaintext. Mặc dù `.env` **đã có trong [.gitignore](file:///d:/Nales-It/nales-it/.gitignore)**, nếu file này đã từng được commit trước đó thì key vẫn tồn tại trong Git history. Cần kiểm tra và xóa khỏi history nếu cần.

> [!WARNING]
> **File backup 39KB (UTF-16 LE) nằm trong production code.** [quiz_generator_backup.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator_backup.py) (39KB, UTF-16 LE encoding) là bản cũ không được import ở bất cứ đâu. Nên xóa.

> [!IMPORTANT]
> **MongoDB URI bị hardcode, không dùng config.** File [mongodb.py](file:///d:/Nales-It/nales-it/backend/app/db/mongodb.py#L14) hardcode `mongodb://localhost:27017` thay vì dùng `settings.MONGODB_URI` từ [config.py](file:///d:/Nales-It/nales-it/backend/app/core/config.py).

---

## Phát hiện theo 5 trục đánh giá

### 1. 🔴 CORRECTNESS — Lỗi logic & hành vi sai

#### Critical: MongoDB URI hardcoded, bỏ qua config

File: [mongodb.py](file:///d:/Nales-It/nales-it/backend/app/db/mongodb.py#L14)

```python
mongo_url = "mongodb://localhost:27017"  # ← Hardcode!
```

Nhưng [config.py](file:///d:/Nales-It/nales-it/backend/app/core/config.py#L5) và [.env](file:///d:/Nales-It/nales-it/backend/.env#L3) đã định nghĩa:
```python
MONGODB_URI: str = "mongodb://admin:password@localhost:27017"
```

Kết quả: **Hệ thống luôn kết nối `localhost:27017` không có auth**, bỏ qua toàn bộ cấu hình MongoDB trong `.env`. Nếu Docker yêu cầu auth (như trong [docker-compose.yml](file:///d:/Nales-It/nales-it/docker-compose.yml) — `MONGO_INITDB_ROOT_USERNAME: admin`), kết nối sẽ **luôn thất bại** và fallback sang MockDB mà không báo lỗi rõ ràng.

```diff
 async def connect_to_mongo():
     logger.info("Đang kết nối tới MongoDB...")
-    mongo_url = "mongodb://localhost:27017"
+    from app.core.config import settings
+    mongo_url = settings.MONGODB_URI
     try:
         db.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
```

#### Required: `_parse_json_from_text` trả về `dict` nhưng nhiều nơi mong đợi `list`

File: [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L15)

```python
def _parse_json_from_text(text: str) -> dict:  # ← Return type annotation says dict
```

Tuy nhiên `solve_quiz_questions()` ở line 152 gọi hàm này và mong đợi `list`:
```python
return _parse_json_from_text(response.content)  # ← Expected List[Dict]
```

Ngoài ra, khi parse thất bại hàm trả về `{}` (empty dict) thay vì `[]` (empty list), khiến code gọi `for item in result` sẽ iterate qua dictionary keys thay vì list items. Annotation nên là `dict | list` và fallback nên kiểm tra context.

#### Required: `solve_quiz_questions` trả `dict` khi LLM response là JSON object thay vì array

File: [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L113-L152)

Nếu LLM trả về `{"id": "1", ...}` thay vì `[{"id": "1", ...}]`, hàm `_parse_json_from_text` sẽ trả về dict, và `background_solve_chunking` sẽ crash khi iterate:

```python
# upload.py line 38
solved_map = {str(item["id"]): item for item in solved_results}  # ← crash nếu dict
```

Cần wrap result: `if isinstance(result, dict): result = [result]`.

#### Required: `quiz_screen.dart` — `_pageController` không dispose

File: [quiz_screen.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_screen.dart#L33-L34)

```dart
class _QuizScreenState extends ConsumerState<QuizScreen> {
  final PageController _pageController = PageController();
  // ...
  // ← Missing dispose()! Memory leak.
```

`PageController` cần được dispose trong `dispose()` method để tránh memory leak. Cần thêm:
```dart
@override
void dispose() {
  _pageController.dispose();
  super.dispose();
}
```

#### Required: `quiz_state.dart` — `stream.listen` không cancel subscription

File: [quiz_state.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_state.dart) — `startStreamingQuiz` method

```dart
void startStreamingQuiz(Stream<Map<String, dynamic>> stream) {
    stream.listen((event) { ... });  // ← No StreamSubscription stored!
```

Stream subscription không được lưu và không bao giờ cancel. Nếu user navigate away khỏi quiz screen, stream vẫn tiếp tục listen và ghi state vào disposed notifier → crash hoặc memory leak.

#### Required: `quiz_state.dart` — Lazy Loading `refreshQuiz()` gây full re-fetch

File: [quiz_state.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_state.dart)

```dart
void nextQuestion() {
    final nextQ = state.quiz.value!.questions[state.currentQuestionIndex];
    if (nextQ.correctAnswerId == null) {
      refreshQuiz();  // ← Re-fetches ENTIRE quiz from server!
    }
}
```

Mỗi lần user chuyển sang câu chưa có đáp án, app gọi `getQuiz(quizId)` reload **toàn bộ quiz** (tất cả câu hỏi). Với đề 50 câu, payload rất lớn. Nên implement endpoint `/quiz/{id}/question/{idx}` chỉ fetch 1 câu.

---

### 2. 🟡 READABILITY & SIMPLICITY

#### Required: File `quiz_generator_backup.py` (39KB, UTF-16 LE) là dead code

File: [quiz_generator_backup.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator_backup.py)

File này **không được import** ở bất cứ đâu, encoding UTF-16 LE bất thường (không phải UTF-8 chuẩn Python), và là bản sao cũ. Nên xóa.

#### Nit: `quiz_screen.dart` 447 lines — nên tách widget

File: [quiz_screen.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_screen.dart)

File chứa `QuizScreen`, `MathMarkdownBuilder`, mode selection bottom sheet, resolve dialog, grid navigation — tất cả trong 1 file. Nên extract thành:
- `math_markdown_builder.dart` 
- `mode_selection_sheet.dart`
- `question_grid_sheet.dart`

#### Nit: Unused `Tuple` import

File: [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L4)
```python
from typing import Dict, Any, List, Tuple, AsyncGenerator  # ← Tuple unused
```

---

### 3. 🟠 ARCHITECTURE

#### Required: Duplicated quiz-lookup pattern across endpoints

File: [quiz.py (API)](file:///d:/Nales-It/nales-it/backend/app/api/quiz.py)

Ba endpoints (`get_quiz`, `grade_quiz`, `resolve_question`) lặp lại cùng pattern:
```python
db = get_database()
if db is None:
    quiz_data = get_mock_quiz(request.quiz_id)
    if not quiz_data: raise HTTPException(404)
else:
    obj_id = ObjectId(quiz_id)
    quiz_data = await db["quizzes"].find_one({"_id": obj_id})
if not quiz_data: raise HTTPException(404)
```

Nên extract thành helper `_get_quiz_data(quiz_id: str) -> dict`.

#### Required: LLM instances tạo mới mỗi lần gọi function

File: [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py)

Mỗi function (`_prescan_answer_keys`, `_map_images_to_questions`, `solve_quiz_questions`, `resolve_single_question`, `stream_quiz_from_pdf`) đều tạo `ChatGoogleGenerativeAI(...)` instance mới:

```python
async def _prescan_answer_keys(text: str) -> dict:
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", ...)  # ← New instance
    
async def solve_quiz_questions(...):
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", ...)  # ← Another new instance
```

Nên tạo **module-level singleton** (hoặc factory) để reuse connections và giảm overhead khởi tạo.

#### Optional: `grade_quiz` tạo LLM instance inline trong API endpoint

File: [quiz.py (API)](file:///d:/Nales-It/nales-it/backend/app/api/quiz.py#L93-L97)

```python
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", 
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.7,
)
```

AI logic nên nằm trong service layer (`quiz_generator.py`), không trực tiếp trong API handler. Điều này vi phạm separation of concerns.

#### Optional: `background_solve_chunking` trong `upload.py` dùng `replace_one` full document update

File: [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py#L36-L44)

```python
quiz_data = await db["quizzes"].find_one({"_id": ObjectId(quiz_id)})
# ... modify quiz_data in memory ...
await db["quizzes"].replace_one({"_id": ObjectId(quiz_id)}, quiz_data)
```

Pattern read-modify-write toàn bộ document có race condition: nếu 2 background tasks chạy đồng thời, task sau sẽ overwrite kết quả của task trước. Nên dùng atomic `$set` với positional operator thay vì `replace_one`.

---

### 4. 🔴 SECURITY

#### Critical: CORS wildcard + credentials

File: [main.py](file:///d:/Nales-It/nales-it/backend/app/main.py#L22-L28)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # ← Open to all origins
    allow_credentials=True,    # ← Combined with * is dangerous
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**`allow_origins=["*"]` + `allow_credentials=True`** cho phép mọi website gửi credentialed requests đến API. Trong dev environment thì OK, nhưng cần thu hẹp cho production. 

> [!TIP]
> FastAPI thực tế sẽ **không** set `Access-Control-Allow-Origin: *` khi `allow_credentials=True` (nó sẽ echo origin cụ thể). Tuy nhiên đây vẫn là cấu hình nguy hiểm vì nó chấp nhận **bất kỳ origin nào**.

#### Required: Không validate file size khi upload PDF

File: [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py#L66-L71)

```python
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # ← No file size check!
    chunks = await extract_text_from_pdf(file)
```

[pdf_extractor.py](file:///d:/Nales-It/nales-it/backend/app/services/pdf_extractor.py#L17) gọi `content = await file.read()` đọc toàn bộ file vào RAM. Không có giới hạn kích thước → attacker có thể gây OOM.

#### Required: Không validate file extension/MIME type

File [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py#L66) không kiểm tra `.pdf` extension hay MIME type. Bất kỳ file nào cũng được accept.

#### Required: Error details exposed trong SSE stream

File: [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py#L105-L109)

```python
except Exception as e:
    error_event = {"type": "error", "detail": f"Server error: {str(e)}"}
    yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
```

Internal exception messages (có thể chứa paths, stack traces, DB connection strings) được gửi thẳng cho client.

#### Nit: `pdf_extractor.py` — Path injection qua `file.filename`

File: [pdf_extractor.py](file:///d:/Nales-It/nales-it/backend/app/services/pdf_extractor.py#L22)

```python
temp_pdf_path = os.path.join(temp_dir, file.filename or "temp.pdf")
```

`file.filename` do client control, có thể chứa `../../malicious.pdf`. Nên sanitize:
```python
import os
safe_filename = os.path.basename(file.filename or "temp.pdf")
```

---

### 5. 🟡 PERFORMANCE

#### Required: `_map_images_to_questions` gửi ALL images trong 1 request

File: [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L69-L111)

```python
all_images_b64 = image_chunks[0]  # ← Tất cả images (50 pages mỗi chunk!)
# ... gửi tất cả qua 1 LLM call
```

Với PDF 100 trang, `pages_per_chunk=50` → 50 ảnh PNG base64 trong 1 request. Token count sẽ **cực lớn** (mỗi ảnh ~258 tokens minimum). Có thể hit context window limit hoặc timeout.

#### Optional: `extract_images_from_pdf` render 2x resolution cho tất cả pages

File: [pdf_extractor.py](file:///d:/Nales-It/nales-it/backend/app/services/pdf_extractor.py#L97)

```python
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Scale 2x
```

Matrix 2x doubles resolution cho tất cả trang, tăng gấp 4 lần memory footprint. Nhiều trang text-only không cần high res. Có thể dùng 1x cho text pages và 2x chỉ cho pages có hình.

#### Nit: `asyncio.create_task` trong `stream_quiz_from_pdf` không lưu reference

File: [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L264)

```python
tasks = [asyncio.create_task(process_text_chunk(i, text)) for i, text in enumerate(chunks)]
```

Các task đã được lưu vào list `tasks` (tốt), nhưng nếu exception xảy ra giữa chừng và generator bị cancelled, tasks orphaned sẽ không được cleanup. Nên add try/finally.

---

## Summary Table

| # | Severity | Issue | File |
|---|----------|-------|------|
| 1 | 🔴 Critical | MongoDB URI hardcoded, bỏ qua `settings.MONGODB_URI` | [mongodb.py](file:///d:/Nales-It/nales-it/backend/app/db/mongodb.py#L14) |
| 2 | 🔴 Critical | CORS `allow_origins=["*"]` + `allow_credentials=True` | [main.py](file:///d:/Nales-It/nales-it/backend/app/main.py#L24) |
| 3 | 🔴 Critical | API key + MongoDB credentials trong `.env` (kiểm tra Git history) | [.env](file:///d:/Nales-It/nales-it/backend/.env) |
| 4 | 🟠 Required | `_parse_json_from_text` return type/fallback mismatch | [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L15) |
| 5 | 🟠 Required | `solve_quiz_questions` không handle dict response | [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L152) |
| 6 | 🟠 Required | Không validate file size/type khi upload | [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py#L66) |
| 7 | 🟠 Required | Error details exposed trong SSE stream | [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py#L108) |
| 8 | 🟠 Required | `PageController` không dispose — memory leak | [quiz_screen.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_screen.dart#L34) |
| 9 | 🟠 Required | Stream subscription không cancel — memory leak | [quiz_state.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_state.dart) |
| 10 | 🟠 Required | Duplicated quiz-lookup pattern across 3 endpoints | [quiz.py](file:///d:/Nales-It/nales-it/backend/app/api/quiz.py) |
| 11 | 🟠 Required | Dead code: `quiz_generator_backup.py` (39KB, UTF-16 LE) | [quiz_generator_backup.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator_backup.py) |
| 12 | 🟡 Optional | LLM instances tạo mới mỗi function call | [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py) |
| 13 | 🟡 Optional | `grade_quiz` chứa AI logic trực tiếp trong API handler | [quiz.py](file:///d:/Nales-It/nales-it/backend/app/api/quiz.py#L93) |
| 14 | 🟡 Optional | Race condition trong `replace_one` background task | [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py#L44) |
| 15 | 🟡 Optional | `_map_images_to_questions` gửi quá nhiều images 1 lúc | [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L76) |
| 16 | 🟡 Optional | `refreshQuiz()` re-fetch toàn bộ quiz thay vì 1 câu | [quiz_state.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_state.dart) |
| 17 | 🟢 Nit | Unused `Tuple` import | [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py#L4) |
| 18 | 🟢 Nit | Path injection qua `file.filename` | [pdf_extractor.py](file:///d:/Nales-It/nales-it/backend/app/services/pdf_extractor.py#L22) |

---

## Proposed Changes

### Phase 1: Critical Fixes (Ưu tiên cao nhất)

#### [MODIFY] [mongodb.py](file:///d:/Nales-It/nales-it/backend/app/db/mongodb.py)
- Dùng `settings.MONGODB_URI` thay vì hardcoded URL

#### [MODIFY] [main.py](file:///d:/Nales-It/nales-it/backend/app/main.py)
- Thu hẹp CORS (ít nhất dùng env config cho allowed origins)

#### Verify `.env` Git history
- Kiểm tra xem `.env` đã từng được commit chưa, nếu có thì xóa khỏi history

---

### Phase 2: Required Fixes (Correctness & Security)

#### [MODIFY] [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py)
- Fix `_parse_json_from_text` return type annotation → `dict | list`
- Wrap `solve_quiz_questions` result: `if isinstance(result, dict): result = [result]`
- Remove unused `Tuple` import
- Extract LLM instances thành module-level singletons

#### [MODIFY] [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py)
- Thêm file size/type validation
- Sanitize error messages trước khi gửi qua SSE

#### [MODIFY] [pdf_extractor.py](file:///d:/Nales-It/nales-it/backend/app/services/pdf_extractor.py)
- Sanitize `file.filename` trước khi dùng trong path

#### [MODIFY] [quiz.py (API)](file:///d:/Nales-It/nales-it/backend/app/api/quiz.py)
- Extract `_get_quiz_data()` helper cho duplicated lookup pattern

#### [MODIFY] [quiz_screen.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_screen.dart)
- Thêm `dispose()` để cleanup `_pageController`

#### [MODIFY] [quiz_state.dart](file:///d:/Nales-It/nales-it/mobile/lib/features/quiz/presentation/quiz_state.dart)
- Lưu `StreamSubscription` và cancel trong destructor

#### [DELETE] [quiz_generator_backup.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator_backup.py)
- Dead code, 39KB UTF-16 LE

---

### Phase 3: Optimization & Polish

#### [MODIFY] [quiz_generator.py](file:///d:/Nales-It/nales-it/backend/app/services/quiz_generator.py)
- Tối ưu `_map_images_to_questions` — batch images thay vì gửi tất cả 1 lúc

#### [MODIFY] [quiz.py (API)](file:///d:/Nales-It/nales-it/backend/app/api/quiz.py)
- Move AI logic từ `grade_quiz` endpoint vào service layer

#### [MODIFY] [upload.py](file:///d:/Nales-It/nales-it/backend/app/api/upload.py)
- Dùng atomic `$set` thay vì `replace_one` trong background task

#### [NEW] Backend: Endpoint `/quiz/{id}/question/{idx}`
- Cho phép mobile fetch từng câu hỏi thay vì toàn bộ quiz

---

## What's Already Good 👍

Những điểm đáng khen trong codebase:

| Aspect | Detail |
|--------|--------|
| ✅ `lifespan` pattern | Backend đã dùng `asynccontextmanager` đúng cách |
| ✅ Pydantic schemas | `Quiz`, `Question`, `Answer` schemas được dùng cho `response_model` |
| ✅ Shared `dioProvider` | Mobile dùng single Dio instance qua Riverpod Provider |
| ✅ Graceful DB fallback | Tự động chuyển MockDB khi MongoDB không available |
| ✅ SSE streaming | Progressive loading qua Server-Sent Events hoạt động tốt |
| ✅ Vision fallback | Tự động chuyển sang OCR nếu text extraction thất bại |
| ✅ Rate limit handling | `max_retries=6` + Semaphore(3) cho concurrent requests |
| ✅ Pre-scan answer keys | Quét đáp án sẵn trước khi bóc tách câu hỏi — rất thông minh |
| ✅ Structured project | Clean architecture: data/domain/presentation layers cho mobile |

---

## Verification Plan

### Automated Tests
```bash
cd backend
poetry run python -c "from app.core.config import settings; print(f'MONGODB_URI={settings.MONGODB_URI}')"
poetry run python -c "from app.services.quiz_generator import _parse_json_from_text; print(_parse_json_from_text('[{\"id\":1}]'))"
```

### Manual Verification
- Kiểm tra `.env` không có trong `git log --all -- backend/.env`
- Khởi động Docker MongoDB và verify kết nối thành công (thay vì fallback MockDB)
- Upload PDF lớn (>50MB) và verify file size rejection
- Test streaming upload và verify background solving
