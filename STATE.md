# Nales-It Project State

## Current Architecture
- **Mobile App**: Flutter (Dart 3.x), Feature-First Architecture, Clean Architecture principles.
- **State Management**: Riverpod 2.x (Notifier/AsyncNotifier).
- **Routing**: GoRouter.
- **Data Models**: Freezed + JSON Serializable.
- **Network**: Dio with Retry Interceptor, SSE streaming support.
- **Offline Caching**: Hive.
- **Monitoring**: Sentry (Error tracking and crashes).
- **Localization**: flutter_localizations + intl.
- **UI/UX**: Material 3, flutter_animate (micro-animations), skeletonizer (loading states), BouncingScrollPhysics (swiping).

## Completed Tasks
- **Phase 1**: Khảo sát & sửa lỗi cú pháp (cập nhật Riverpod `autoDispose`, sửa lỗi SSE stream listener trong `quiz_state.dart`).
- **Phase 2**: Chia tách UI Widget lớn thành các file nhỏ (`mode_selection_sheet.dart`, `question_grid_sheet.dart`, `resolve_dialog.dart`, `math_markdown_builder.dart`).
- **Phase 3**: Nâng cấp hạ tầng: 
  - Chuyển Data models sang `@freezed`.
  - Cài đặt `CacheService` (Hive) fallback dữ liệu offline.
  - Tích hợp `Sentry` catch lỗi.
  - Chuyển đổi đa ngôn ngữ (i18n) với `AppLocalizations`.
- **Phase 4**: Tinh chỉnh UI/UX:
  - Nâng cấp `AppTheme` với `darkTheme` & `lightTheme` hiện đại.
  - Tích hợp `skeletonizer` mô phỏng skeleton loading lúc chờ AI.
  - Áp dụng `flutter_animate` cho đáp án, nút nhấn.
  - Bật cơ chế swipe câu hỏi (chuyển `NeverScrollableScrollPhysics` thành `BouncingScrollPhysics`).
- **Testing**: Cập nhật lại toàn bộ `unit_test.dart` và `widget_test.dart`. Hiện tại 34/34 test chạy PASS. 0 lỗi Analyzer.

## Pending Tasks / Known Bugs
- **Phase 5**: Edge cases handling & Deployment preparation (nếu có).
- Cần phát triển thêm backend endpoint thực tế cho SSE stream (hiện app có mock stream).
- Kiểm tra tính ổn định trên thiết bị vật lý thật (iOS/Android).

## Running Services
- `flutter run` trong thư mục `mobile` để chạy ứng dụng giả lập.
- Chạy `dart run build_runner watch -d` để theo dõi thay đổi của Freezed và JSON Serializable.
- Chạy `flutter test` để xác minh trạng thái.
