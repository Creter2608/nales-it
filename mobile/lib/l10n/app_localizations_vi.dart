// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Vietnamese (`vi`).
class AppLocalizationsVi extends AppLocalizations {
  AppLocalizationsVi([String locale = 'vi']) : super(locale);

  @override
  String get appTitle => 'Nales-It Gia Sư AI';

  @override
  String get modeSelectionTitle => 'Chọn Chế Độ Làm Bài';

  @override
  String get modeInstant => 'Ôn luyện';

  @override
  String get modeInstantDesc => 'Báo màu xanh đỏ ngay khi chọn.';

  @override
  String get modeExam => 'Thi thử';

  @override
  String get modeExamDesc => 'Chấm điểm ở cuối giờ.';

  @override
  String get modeAi => 'Đánh giá AI';

  @override
  String get modeAiDesc => 'AI nhận xét tổng quan kỹ năng của bạn.';

  @override
  String get modePractice => 'Tự do';

  @override
  String get modePracticeDesc => 'Không chấm điểm, chỉ đọc câu hỏi.';

  @override
  String get questionGridTitle => 'Bảng câu hỏi';

  @override
  String get resolveDialogTitle => 'Yêu cầu giải lại?';

  @override
  String get resolveDialogDesc =>
      'Bạn thấy cấn cấn? Yêu cầu Gia sư AI kiểm tra và giải lại câu này?';

  @override
  String get cancel => 'Hủy';

  @override
  String get resolve => 'Giải lại';

  @override
  String get resolvingMsg => 'Đang yêu cầu AI giải lại...';

  @override
  String get resolvedMsg => 'Đã cập nhật lời giải mới!';

  @override
  String get resolveErrorMsg => 'Lỗi: Không thể giải lại lúc này.';
}
