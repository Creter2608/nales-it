import 'package:freezed_annotation/freezed_annotation.dart';

part 'quiz_models.freezed.dart';
part 'quiz_models.g.dart';

enum QuizMode {
  instantFeedback, // 1. Ôn luyện (Báo đúng/sai ngay)
  exam,            // 2. Thi thử (Giấu đáp án, chấm điểm cuối giờ)
  aiEvaluation,    // 3. Đánh giá AI (Nộp bài cho AI nhận xét)
  practice         // 4. Tự do (Không chấm điểm)
}

String _idToString(dynamic value) => value.toString();
String? _nullableIdToString(dynamic value) => value?.toString();

@freezed
abstract class Answer with _$Answer {
  const factory Answer({
    @JsonKey(fromJson: _idToString) required String id,
    required String content,
  }) = _Answer;

  factory Answer.fromJson(Map<String, dynamic> json) => _$AnswerFromJson(json);
}

@freezed
abstract class Question with _$Question {
  const factory Question({
    @JsonKey(fromJson: _idToString) required String id,
    required String content,
    required List<Answer> answers,
    @JsonKey(name: 'correct_answer_id') String? correctAnswerId,
    String? explanation,
    @JsonKey(name: 'shared_context') String? sharedContext,
    @JsonKey(name: 'image_base64') String? imageBase64,
  }) = _Question;

  factory Question.fromJson(Map<String, dynamic> json) => _$QuestionFromJson(json);
}

@freezed
abstract class Quiz with _$Quiz {
  const factory Quiz({
    @JsonKey(fromJson: _nullableIdToString) String? id,
    required String title,
    required List<Question> questions,
  }) = _Quiz;

  factory Quiz.fromJson(Map<String, dynamic> json) => _$QuizFromJson(json);
}
